import httpx
import pytest

from reviewlens.review.ingest import (
    REASON_NO_REVIEW_ACTIVITY,
    REASON_PRE_REVIEW_COMMIT_UNREACHABLE,
    AuthError,
    GitHubClient,
    PRExcluded,
    RateLimitError,
    fetch_pr_snapshot,
)

PULL = {"number": 42, "base": {"sha": "base-sha"}, "head": {"sha": "head-sha"}}

COMPARE_OK = {
    "files": [
        {"filename": "Foo.java", "status": "modified", "patch": "@@ -1,1 +1,1 @@\n-a\n+b\n"},
    ]
}


def make_client(transport, **kwargs):
    kwargs.setdefault("backoff_base", 0.0)
    return GitHubClient(token="test-token", transport=transport, **kwargs)


def route(pull=None, comments=None, reviews=None, compare_status=200, compare_body=None):
    """Build a routing handler for the four endpoints fetch_pr_snapshot touches."""
    pull = pull if pull is not None else PULL
    comments = comments if comments is not None else []
    reviews = reviews if reviews is not None else []
    compare_body = compare_body if compare_body is not None else COMPARE_OK

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/42"):
            return httpx.Response(200, json=pull)
        if path.endswith("/comments"):
            return httpx.Response(200, json=comments)
        if path.endswith("/reviews"):
            return httpx.Response(200, json=reviews)
        if "/compare/" in path:
            return httpx.Response(compare_status, json=compare_body)
        raise AssertionError(f"unexpected request: {request.method} {path}")

    return handler


def test_earliest_activity_is_a_review_comment():
    comments = [
        {"original_commit_id": "sha-early", "created_at": "2024-01-01T00:00:00Z"},
        {"original_commit_id": "sha-late", "created_at": "2024-01-03T00:00:00Z"},
    ]
    reviews = [
        {"commit_id": "sha-mid", "submitted_at": "2024-01-02T00:00:00Z"},
    ]
    transport = httpx.MockTransport(route(comments=comments, reviews=reviews))
    client = make_client(transport)

    snapshot = fetch_pr_snapshot(client, "org", "repo", 42)

    assert snapshot.pre_review_sha == "sha-early"
    assert snapshot.base_sha == "base-sha"
    assert snapshot.repo == "org/repo"
    assert snapshot.number == 42
    assert snapshot.files[0].path == "Foo.java"
    assert snapshot.files[0].status == "modified"
    assert snapshot.files[0].patch == "@@ -1,1 +1,1 @@\n-a\n+b\n"


def test_earliest_activity_is_a_review():
    comments = [
        {"original_commit_id": "sha-late", "created_at": "2024-01-03T00:00:00Z"},
    ]
    reviews = [
        {"commit_id": "sha-early", "submitted_at": "2024-01-01T00:00:00Z"},
        {"commit_id": "sha-mid", "submitted_at": "2024-01-02T00:00:00Z"},
    ]
    transport = httpx.MockTransport(route(comments=comments, reviews=reviews))
    client = make_client(transport)

    snapshot = fetch_pr_snapshot(client, "org", "repo", 42)

    assert snapshot.pre_review_sha == "sha-early"


def test_reviews_without_usable_sha_or_timestamp_are_skipped():
    comments = []
    reviews = [
        # PENDING review: no submitted_at yet.
        {"commit_id": "sha-pending", "submitted_at": None, "state": "PENDING"},
        # Malformed/edge entry: missing commit_id entirely.
        {"submitted_at": "2024-01-01T00:00:00Z", "state": "COMMENTED"},
        # The only usable entry.
        {"commit_id": "sha-usable", "submitted_at": "2024-01-05T00:00:00Z", "state": "COMMENTED"},
    ]
    transport = httpx.MockTransport(route(comments=comments, reviews=reviews))
    client = make_client(transport)

    snapshot = fetch_pr_snapshot(client, "org", "repo", 42)

    assert snapshot.pre_review_sha == "sha-usable"


def test_no_review_activity_excludes_pr():
    transport = httpx.MockTransport(route(comments=[], reviews=[]))
    client = make_client(transport)

    with pytest.raises(PRExcluded) as exc_info:
        fetch_pr_snapshot(client, "org", "repo", 42)
    assert exc_info.value.reason == REASON_NO_REVIEW_ACTIVITY


def test_unreachable_pre_review_commit_excludes_pr_as_force_push():
    comments = [{"original_commit_id": "gone-sha", "created_at": "2024-01-01T00:00:00Z"}]
    transport = httpx.MockTransport(route(comments=comments, compare_status=422, compare_body={}))
    client = make_client(transport)

    with pytest.raises(PRExcluded) as exc_info:
        fetch_pr_snapshot(client, "org", "repo", 42)
    assert exc_info.value.reason == REASON_PRE_REVIEW_COMMIT_UNREACHABLE
    assert "force-push" in str(exc_info.value)


def test_unreachable_pre_review_commit_404_also_excludes():
    comments = [{"original_commit_id": "gone-sha", "created_at": "2024-01-01T00:00:00Z"}]
    transport = httpx.MockTransport(route(comments=comments, compare_status=404, compare_body={}))
    client = make_client(transport)

    with pytest.raises(PRExcluded) as exc_info:
        fetch_pr_snapshot(client, "org", "repo", 42)
    assert exc_info.value.reason == REASON_PRE_REVIEW_COMMIT_UNREACHABLE


def test_missing_github_token_fails_loudly(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(AuthError, match="GITHUB_TOKEN"):
        GitHubClient()


def test_auth_error_vs_rate_limit_are_distinguishable():
    auth_transport = httpx.MockTransport(lambda request: httpx.Response(401, json={}))
    auth_client = make_client(auth_transport)
    with pytest.raises(AuthError, match="401"):
        auth_client.get_pull("org", "repo", 42)

    rate_limit_transport = httpx.MockTransport(
        lambda request: httpx.Response(
            403,
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "123456"},
            json={},
        )
    )
    rate_limit_client = make_client(rate_limit_transport)
    with pytest.raises(RateLimitError, match="rate limit"):
        rate_limit_client.get_pull("org", "repo", 42)
