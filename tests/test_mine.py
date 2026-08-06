import json
import os

import httpx
import pytest

from reviewlens.mine.miner import PROJECT_REGISTRY, mine, mine_project, write_corpus
from reviewlens.mine.select import (
    changed_java_files,
    comment_qualifies,
    is_bot_author,
    pr_is_merged,
    pr_size_ok,
    resolve_canonical_line,
)
from reviewlens.review.ingest import GitHubClient

OWNER, REPO = "junit-team", "junit5"
DEFAULT_PATCH = "@@ -1,2 +1,2 @@\n-old line\n+new line\n"


# ---------------------------------------------------------------------------
# select.py: pure predicate unit tests
# ---------------------------------------------------------------------------


def _comment(**overrides):
    # original_commit_id is deliberately None by default: in the miner-level
    # fixtures below, the paired _review() fixture is what determines the
    # PR's pre-review SHA (via ingest.py's earliest-activity logic) — a
    # comment with a commit id would compete for "earliest" and, on a tied
    # timestamp, could win non-deterministically depending on dict order.
    base = {
        "id": 1,
        "path": "src/Foo.java",
        "line": 10,
        "original_line": 10,
        "original_commit_id": None,
        "in_reply_to_id": None,
        "side": "RIGHT",
        "user": {"login": "bob", "type": "User"},
        "created_at": "2024-01-01T00:00:00Z",
        "body": "x" * 40,
        "html_url": "https://github.com/o/r/pull/1#discussion_r1",
    }
    base.update(overrides)
    return base


def test_thread_reply_is_rejected_from_the_rq1_denominator():
    # One review thread is one human finding. A reply is discussion, not a new
    # issue, and is unmatchable by any model comment — counting it would
    # depress RQ1 recall (measured: 35% of a 90-PR corpus's raw comments).
    reply = _comment(in_reply_to_id=99)
    assert not comment_qualifies(reply, pr_author_login="alice")


def test_thread_opening_comment_is_kept():
    assert comment_qualifies(_comment(in_reply_to_id=None), pr_author_login="alice")


def test_pr_qualifying_only_via_thread_replies_is_skipped():
    # Two comments on the PR, but they are one thread: opener + reply. That is
    # a single finding, so the PR must fall below the >=2 bar.
    pulls = [_pr(600)]
    thread = [_comment(id=1), _comment(id=2, in_reply_to_id=1)]
    handler = make_handler(
        OWNER,
        REPO,
        pulls,
        comments_by_number={600: thread},
        reviews_by_number={600: [_review(600)]},
        compare_by_key={"base-600...pre-600": _default_compare()},
    )
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert records == []
    assert entry["skipped"]["too_few_comments"] == 1


def test_bot_by_user_type_is_rejected():
    comment = _comment(user={"login": "some-bot", "type": "Bot"})
    assert not comment_qualifies(comment, pr_author_login="alice")
    assert is_bot_author(comment["user"])


def test_bot_by_login_suffix_is_rejected():
    comment = _comment(user={"login": "dependabot[bot]", "type": "User"})
    assert not comment_qualifies(comment, pr_author_login="alice")
    assert is_bot_author(comment["user"])


def test_pr_author_self_comment_is_rejected():
    comment = _comment(user={"login": "alice", "type": "User"})
    assert not comment_qualifies(comment, pr_author_login="alice")


def test_body_under_30_chars_is_rejected():
    comment = _comment(body="too short")
    assert not comment_qualifies(comment, pr_author_login="alice")


def test_body_that_is_only_quote_and_fence_normalizes_under_threshold():
    body = "> quoted line one\n> quoted line two\n```\nsome code\n```"
    comment = _comment(body=body)
    assert not comment_qualifies(comment, pr_author_login="alice")


def test_non_java_path_is_rejected():
    comment = _comment(path="README.md")
    assert not comment_qualifies(comment, pr_author_login="alice")


def test_unanchored_comment_is_rejected():
    comment = _comment(line=None, original_line=None)
    assert resolve_canonical_line(comment) is None
    assert not comment_qualifies(comment, pr_author_login="alice")


def test_canonical_line_prefers_original_line_over_line():
    comment = _comment(line=44, original_line=42)
    assert resolve_canonical_line(comment) == 42


def test_canonical_line_falls_back_to_line_when_original_is_null():
    comment = _comment(line=44, original_line=None)
    assert resolve_canonical_line(comment) == 44


def test_qualifying_comment_passes_all_checks():
    comment = _comment()
    assert comment_qualifies(comment, pr_author_login="alice")


def test_pr_is_merged():
    assert pr_is_merged({"merged_at": "2024-01-01T00:00:00Z"})
    assert not pr_is_merged({"merged_at": None})


def test_changed_java_files_filters_non_java():
    files = [{"path": "src/Foo.java"}, {"path": "README.md"}, {"path": "src/Bar.java"}]
    assert changed_java_files(files) == ["src/Foo.java", "src/Bar.java"]


def test_pr_size_ok_over_file_cap():
    files = [{"path": f"src/F{i}.java", "patch": "@@ -1,1 +1,1 @@\n-a\n+b\n"} for i in range(51)]
    assert not pr_size_ok(files)


def test_pr_size_ok_over_line_cap():
    big_patch = "@@ -1,2001 +1,2001 @@\n" + "+x\n" * 2001
    files = [{"path": "src/Foo.java", "patch": big_patch}]
    assert not pr_size_ok(files)


def test_pr_size_ok_within_caps():
    files = [{"path": "src/Foo.java", "patch": DEFAULT_PATCH}]
    assert pr_size_ok(files)


# ---------------------------------------------------------------------------
# miner.py: end-to-end orchestration against a mocked GitHub API
# ---------------------------------------------------------------------------


def _pr(number, merged=True, author="alice", title="a title"):
    return {
        "number": number,
        "title": title,
        "html_url": f"https://github.com/{OWNER}/{REPO}/pull/{number}",
        "merged_at": "2024-01-01T00:00:00Z" if merged else None,
        "user": {"login": author, "type": "User"},
        "base": {"sha": f"base-{number}"},
        "head": {"sha": f"head-{number}"},
    }


def _review(number):
    return {"commit_id": f"pre-{number}", "submitted_at": "2024-01-01T00:00:00Z", "state": "COMMENTED"}


def make_handler(owner, repo, pulls, comments_by_number=None, reviews_by_number=None, compare_by_key=None):
    """Route the handful of endpoints mine_project touches for one repo."""
    pull_by_number = {p["number"]: p for p in pulls}
    comments_by_number = comments_by_number or {}
    reviews_by_number = reviews_by_number or {}
    compare_by_key = compare_by_key or {}
    prefix = f"/repos/{owner}/{repo}"

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == f"{prefix}/pulls":
            return httpx.Response(200, json=pulls)
        if path.startswith(f"{prefix}/compare/"):
            key = path[len(f"{prefix}/compare/") :]
            fixture = compare_by_key.get(key, {"files": []})
            return httpx.Response(fixture.get("status", 200), json=fixture.get("json", {"files": []}))
        if path.startswith(f"{prefix}/pulls/"):
            parts = path[len(f"{prefix}/pulls/") :].split("/")
            number = int(parts[0])
            if len(parts) == 1:
                return httpx.Response(200, json=pull_by_number[number])
            if parts[1] == "comments":
                return httpx.Response(200, json=comments_by_number.get(number, []))
            if parts[1] == "reviews":
                return httpx.Response(200, json=reviews_by_number.get(number, []))
        raise AssertionError(f"unexpected request: {request.method} {path}")

    return handler


def combine_handlers(handlers_by_prefix):
    def handler(request: httpx.Request) -> httpx.Response:
        for prefix, sub in handlers_by_prefix.items():
            if request.url.path.startswith(prefix):
                return sub(request)
        raise AssertionError(f"unrouted request: {request.url.path}")

    return handler


def make_client(transport, **kwargs):
    kwargs.setdefault("backoff_base", 0.0)
    return GitHubClient(token="test-token", transport=transport, **kwargs)


def _default_compare():
    return {"json": {"files": [{"filename": "src/Foo.java", "status": "modified", "patch": DEFAULT_PATCH}]}}


def _qualifying_comments(number):
    return [
        _comment(id=number * 10 + 1, user={"login": "bob", "type": "User"}),
        _comment(id=number * 10 + 2, user={"login": "carol", "type": "User"}),
    ]


def test_end_to_end_run_produces_correct_corpus_and_manifest_tallies(tmp_path):
    pulls = [
        _pr(105, merged=False),  # not_merged
        _pr(104),  # no_java_files
        _pr(103),  # too_large
        _pr(102),  # too_few_comments
        _pr(101),  # no_review_activity (PRExcluded)
        _pr(100),  # selected
    ]
    # The comment filter runs before the snapshot fetch, so every PR meant to
    # be rejected for a *later* reason must first clear the >=2 qualifying
    # comments bar — otherwise it would be tallied as too_few_comments instead.
    comments_by_number = {
        104: _qualifying_comments(104),
        103: _qualifying_comments(103),
        102: [_comment(id=1021, user={"login": "bob", "type": "User"})],
        101: _qualifying_comments(101),
        100: _qualifying_comments(100),
    }
    reviews_by_number = {
        104: [_review(104)],
        103: [_review(103)],
        102: [_review(102)],
        101: [],  # no review activity at all -> PRExcluded
        100: [_review(100)],
    }
    compare_by_key = {
        "base-104...pre-104": {"json": {"files": [{"filename": "README.md", "status": "modified", "patch": DEFAULT_PATCH}]}},
        "base-103...pre-103": {
            "json": {
                "files": [
                    {
                        "filename": "src/Foo.java",
                        "status": "modified",
                        "patch": "@@ -1,2001 +1,2001 @@\n" + "+x\n" * 2001,
                    }
                ]
            }
        },
        "base-102...pre-102": _default_compare(),
        "base-100...pre-100": _default_compare(),
    }
    handler = make_handler(
        OWNER, REPO, pulls, comments_by_number, reviews_by_number, compare_by_key
    )
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert entry["scanned"] == 6
    assert entry["selected"] == 1
    assert entry["hit_scan_limit"] is False
    assert entry["skipped"] == {
        "not_merged": 1,
        "bot_author": 0,
        "no_java_files": 1,
        "too_large": 1,
        "too_few_comments": 1,
        "no_review_activity": 1,
        "pre_review_commit_unreachable": 0,
    }
    assert len(records) == 1
    assert records[0]["number"] == 100

    manifest = {
        "mined_at": "2024-01-01T00:00:00Z",
        "criteria": {},
        "projects": [entry],
        "prs": [{"repo": r["repo"], "number": r["number"], "pre_review_sha": r["pre_review_sha"]} for r in records],
    }
    out_dir = str(tmp_path / "corpus")
    write_corpus(out_dir, records, manifest)

    expected_file = os.path.join(out_dir, f"{OWNER}__{REPO}__100.json")
    assert os.path.isfile(expected_file)
    with open(expected_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["repo"] == f"{OWNER}/{REPO}"
    assert data["number"] == 100
    assert data["base_sha"] == "base-100"
    assert data["pre_review_sha"] == "pre-100"
    assert data["changed_java_files"] == ["src/Foo.java"]
    assert len(data["human_comments"]) == 2
    comment = data["human_comments"][0]
    assert set(comment) == {
        "id", "path", "line", "raw_line", "original_line", "original_commit_id",
        "in_reply_to_id", "side", "author", "created_at", "body", "url",
    }

    with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
        manifest_on_disk = json.load(f)
    total_skipped = sum(manifest_on_disk["projects"][0]["skipped"].values())
    assert total_skipped + manifest_on_disk["projects"][0]["selected"] == manifest_on_disk["projects"][0]["scanned"]


def test_pr_excluded_by_fetch_pr_snapshot_is_tallied_under_its_reason(tmp_path):
    # Qualifying comments (so the comment filter passes) but no review with a
    # usable commit id, and _comment() leaves original_commit_id None — so
    # ingest.py can pin no pre-review SHA and excludes the PR.
    pulls = [_pr(200)]
    handler = make_handler(
        OWNER,
        REPO,
        pulls,
        comments_by_number={200: _qualifying_comments(200)},
        reviews_by_number={200: []},
    )
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert records == []
    assert entry["skipped"]["no_review_activity"] == 1
    assert entry["selected"] == 0


def test_too_few_comments_pr_never_triggers_the_expensive_snapshot_fetch():
    # Guards the API-cost ordering: the 1-call comment filter must reject a PR
    # before the ~4-call fetch_pr_snapshot runs. Reversing the order would put
    # a full three-project mining run over GitHub's 5000 requests/hour limit.
    paths_requested = []
    pulls = [_pr(400)]
    inner = make_handler(
        OWNER,
        REPO,
        pulls,
        comments_by_number={400: [_comment(id=4001, user={"login": "bob", "type": "User"})]},
        reviews_by_number={400: [_review(400)]},
        compare_by_key={"base-400...pre-400": _default_compare()},
    )

    def recording_handler(request: httpx.Request) -> httpx.Response:
        paths_requested.append(request.url.path)
        return inner(request)

    client = make_client(httpx.MockTransport(recording_handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert entry["skipped"]["too_few_comments"] == 1
    assert records == []
    assert any(p.endswith("/pulls/400/comments") for p in paths_requested)
    assert not any("/compare/" in p for p in paths_requested)
    assert not any(p.endswith("/pulls/400/reviews") for p in paths_requested)


def test_bot_authored_pr_is_skipped_without_any_api_call():
    # The bot check reads the list payload, so it must cost zero extra requests.
    # Measured on live data, 82% of junit5's merged PRs are renovate bumps; one
    # comment fetch each would be ~460 wasted calls per 600 PRs scanned.
    paths_requested = []
    pulls = [_pr(500, author="renovate[bot]")]
    inner = make_handler(OWNER, REPO, pulls, comments_by_number={500: _qualifying_comments(3)})

    def recording_handler(request: httpx.Request) -> httpx.Response:
        paths_requested.append(request.url.path)
        return inner(request)

    client = make_client(httpx.MockTransport(recording_handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert records == []
    assert entry["skipped"]["bot_author"] == 1
    assert not any(p.endswith("/pulls/500/comments") for p in paths_requested)


def test_bot_detection_by_user_type_not_only_login_suffix():
    pulls = [_pr(501, author="somebot")]
    pulls[0]["user"]["type"] = "Bot"
    handler = make_handler(OWNER, REPO, pulls, comments_by_number={501: _qualifying_comments(3)})
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert records == []
    assert entry["skipped"]["bot_author"] == 1


def test_qualifying_comment_count_boundary_one_rejects_two_accepts():
    # Exactly 1 qualifying comment -> too_few_comments.
    pulls_one = [_pr(300)]
    handler_one = make_handler(
        OWNER,
        REPO,
        pulls_one,
        comments_by_number={300: [_comment(id=1, user={"login": "bob", "type": "User"})]},
        reviews_by_number={300: [_review(300)]},
        compare_by_key={"base-300...pre-300": _default_compare()},
    )
    client_one = make_client(httpx.MockTransport(handler_one))
    records_one, entry_one = mine_project(client_one, "junit5", per_project=30, scan_limit=400)
    assert records_one == []
    assert entry_one["skipped"]["too_few_comments"] == 1

    # Exactly 2 qualifying comments -> selected.
    pulls_two = [_pr(301)]
    handler_two = make_handler(
        OWNER,
        REPO,
        pulls_two,
        comments_by_number={301: _qualifying_comments(301)},
        reviews_by_number={301: [_review(301)]},
        compare_by_key={"base-301...pre-301": _default_compare()},
    )
    client_two = make_client(httpx.MockTransport(handler_two))
    records_two, entry_two = mine_project(client_two, "junit5", per_project=30, scan_limit=400)
    assert len(records_two) == 1
    assert entry_two["skipped"]["too_few_comments"] == 0


def test_unanchored_comments_are_tallied_but_do_not_block_selection():
    unanchored = _comment(id=1, line=None, original_line=None, user={"login": "dave", "type": "User"})
    pulls = [_pr(400)]
    handler = make_handler(
        OWNER,
        REPO,
        pulls,
        comments_by_number={400: _qualifying_comments(400) + [unanchored]},
        reviews_by_number={400: [_review(400)]},
        compare_by_key={"base-400...pre-400": _default_compare()},
    )
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=400)

    assert len(records) == 1
    assert entry["unanchored_comments"] == 1


def test_per_project_flag_caps_selected_and_stops_scanning():
    pulls = [_pr(n) for n in (500, 501, 502)]
    comments_by_number = {n: _qualifying_comments(n) for n in (500, 501, 502)}
    reviews_by_number = {n: [_review(n)] for n in (500, 501, 502)}
    compare_by_key = {f"base-{n}...pre-{n}": _default_compare() for n in (500, 501, 502)}
    handler = make_handler(OWNER, REPO, pulls, comments_by_number, reviews_by_number, compare_by_key)
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=2, scan_limit=400)

    assert len(records) == 2
    assert entry["scanned"] == 2
    assert entry["hit_scan_limit"] is False


def test_scan_limit_flag_bounds_examined_prs_and_is_recorded():
    pulls = [_pr(600, merged=False), _pr(601, merged=False), _pr(602)]
    comments_by_number = {602: _qualifying_comments(602)}
    reviews_by_number = {602: [_review(602)]}
    compare_by_key = {"base-602...pre-602": _default_compare()}
    handler = make_handler(OWNER, REPO, pulls, comments_by_number, reviews_by_number, compare_by_key)
    client = make_client(httpx.MockTransport(handler))

    records, entry = mine_project(client, "junit5", per_project=30, scan_limit=2)

    assert records == []
    assert entry["scanned"] == 2
    assert entry["hit_scan_limit"] is True
    assert entry["skipped"]["not_merged"] == 2


def test_max_total_flag_is_honored_across_projects():
    junit_pulls = [_pr(n) for n in (700, 701, 702)]
    junit_comments = {n: _qualifying_comments(n) for n in (700, 701, 702)}
    junit_reviews = {n: [_review(n)] for n in (700, 701, 702)}
    junit_compare = {f"base-{n}...pre-{n}": _default_compare() for n in (700, 701, 702)}
    junit_handler = make_handler(OWNER, REPO, junit_pulls, junit_comments, junit_reviews, junit_compare)

    mockito_pulls = [_pr(n) for n in (800, 801, 802)]
    mockito_comments = {n: _qualifying_comments(n) for n in (800, 801, 802)}
    mockito_reviews = {n: [_review(n)] for n in (800, 801, 802)}
    mockito_compare = {f"base-{n}...pre-{n}": _default_compare() for n in (800, 801, 802)}
    mockito_handler = make_handler(
        "mockito", "mockito", mockito_pulls, mockito_comments, mockito_reviews, mockito_compare
    )

    combined = combine_handlers(
        {
            f"/repos/{OWNER}/{REPO}": junit_handler,
            "/repos/mockito/mockito": mockito_handler,
        }
    )
    client = make_client(httpx.MockTransport(combined))

    records, manifest = mine(
        client, ["junit5", "mockito"], per_project=3, max_total=4, scan_limit=400
    )

    assert len(records) == 4
    assert manifest["projects"][0]["selected"] == 3
    assert manifest["projects"][1]["selected"] == 1


def test_unknown_project_slug_raises_loud_error():
    client = make_client(httpx.MockTransport(lambda r: httpx.Response(200, json=[])))
    with pytest.raises(ValueError, match="Unknown project slug"):
        mine_project(client, "not-a-real-project", per_project=30, scan_limit=400)


def test_project_registry_has_the_three_locked_projects():
    assert PROJECT_REGISTRY == {
        "junit5": "junit-team/junit5",
        "mockito": "mockito/mockito",
        "checkstyle": "checkstyle/checkstyle",
    }
