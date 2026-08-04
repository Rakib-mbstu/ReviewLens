"""Fetch a pull request's *pre-review* state from the GitHub API.

The evaluation measures recall against real human review comments (RQ1): what
fraction of the comments a human reviewer left does the LLM also raise. That
comparison is only valid if the LLM reviews the same code the human reviewer
saw. If we accidentally reviewed the post-review/merged state, the model
would effectively get to see fixes the human comments already produced,
silently inflating (or deflating) recall. So this module's only job is to
pin down the exact commit that was checked out when review activity first
started, and to refuse to guess if that commit can no longer be reached
(e.g. after a force-push rewrote history) rather than silently falling back
to a different state.

Pre-review commit = the commit referenced by the EARLIEST review activity
(review comment or review) on the PR. That is the state reviewers were
actually looking at when they wrote their first comment.
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass

import httpx

GITHUB_API_BASE_URL = "https://api.github.com"
TOKEN_ENV_VAR = "GITHUB_TOKEN"

# PRExcluded.reason values. A PR carrying one of these is unusable for
# evaluation and must be dropped from the corpus, never silently patched up.
REASON_NO_REVIEW_ACTIVITY = "no_review_activity"
REASON_PRE_REVIEW_COMMIT_UNREACHABLE = "pre_review_commit_unreachable"


class GitHubError(Exception):
    """Base class for GitHub client / ingestion failures."""


class AuthError(GitHubError):
    """Authentication or permission failure — not retried."""


class RateLimitError(GitHubError):
    """Rate limited and retries exhausted (or primary limit exhausted)."""


class TransientError(GitHubError):
    """Server or network error and retries exhausted."""


class PRExcluded(GitHubError):
    """A PR that cannot be used for evaluation and must be excluded.

    Raised instead of falling back to some other commit state, because a
    silent fallback (e.g. to the merged head) would contaminate the RQ1
    recall measurement. `reason` is one of the REASON_* constants above so
    callers building the corpus can tally/report exclusions by cause.
    """

    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(message)


@dataclass
class PRFile:
    """One file's change within a PR, as of the pre-review diff."""

    path: str
    status: str
    patch: str


@dataclass
class PRSnapshot:
    """The pre-review state of a PR: what a human reviewer first saw."""

    repo: str
    number: int
    base_sha: str
    pre_review_sha: str
    files: list[PRFile]


class GitHubClient:
    """Read-only GitHub REST client. transport is injectable for tests.

    Retries with exponential backoff only on transient conditions (secondary
    rate limit, 5xx, network errors). Auth failures and primary rate-limit
    exhaustion fail immediately with an actionable message — retrying those
    would just waste the backoff budget.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = GITHUB_API_BASE_URL,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._token = token or os.environ.get(TOKEN_ENV_VAR)
        if not self._token:
            raise AuthError(
                f"No GitHub token: pass token or set the {TOKEN_ENV_VAR} environment variable "
                "(read-only access is sufficient)."
            )
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._http = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
            transport=transport,
            # GitHub 301-redirects API calls when a repo is renamed (e.g.
            # junit-team/junit5 -> junit-team/junit-framework); without this,
            # every mined PR under an old name would fail unnecessarily.
            follow_redirects=True,
        )

    def get_pull(self, owner: str, repo: str, number: int) -> dict:
        """Fetch pull request metadata (used here for the base SHA)."""
        return self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}").json()

    def get_review_comments(self, owner: str, repo: str, number: int) -> list[dict]:
        """Fetch all inline review comments (paginated)."""
        return self._paginated_get(
            f"/repos/{owner}/{repo}/pulls/{number}/comments", {"per_page": 100}
        )

    def get_reviews(self, owner: str, repo: str, number: int) -> list[dict]:
        """Fetch all reviews (paginated)."""
        return self._paginated_get(
            f"/repos/{owner}/{repo}/pulls/{number}/reviews", {"per_page": 100}
        )

    def list_pulls(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        sort: str = "created",
        direction: str = "desc",
        max_items: int | None = None,
    ) -> list[dict]:
        """List pull requests newest-first (paginated), used by mining to page
        through a project's history looking for corpus candidates.

        `max_items` bounds how many pages are actually fetched (mining's
        --scan-limit exists to cap API cost on large repos), unlike
        get_review_comments/get_reviews which always want every item.
        """
        return self._paginated_get(
            f"/repos/{owner}/{repo}/pulls",
            {"state": state, "sort": sort, "direction": direction, "per_page": 100},
            max_items=max_items,
        )

    def compare(self, owner: str, repo: str, base: str, head: str) -> httpx.Response:
        """Compare two commits. 404/422 are returned (not raised) so callers
        can distinguish "commit unreachable" (force-push) from other errors.
        """
        return self._request(
            "GET",
            f"/repos/{owner}/{repo}/compare/{base}...{head}",
            ok_statuses=(200, 404, 422),
        )

    def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        """Fetch a file's full text content at a given ref (for chunk context)."""
        resp = self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        data = resp.json()
        content = data.get("content")
        if content is None or data.get("encoding") != "base64":
            raise GitHubError(
                f"Unexpected /contents response for {owner}/{repo}/{path}@{ref} "
                "(missing base64-encoded content — file may be too large or a directory)."
            )
        return base64.b64decode(content).decode("utf-8")

    def _paginated_get(
        self, path: str, params: dict, max_items: int | None = None
    ) -> list[dict]:
        items: list[dict] = []
        next_path: str | None = path
        next_params: dict | None = dict(params)
        while next_path:
            resp = self._request("GET", next_path, params=next_params)
            items.extend(resp.json())
            if max_items is not None and len(items) >= max_items:
                break
            next_link = resp.links.get("next") if resp.links else None
            next_path = next_link["url"] if next_link else None
            next_params = None
        return items[:max_items] if max_items is not None else items

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        ok_statuses: tuple = (200,),
    ) -> httpx.Response:
        last_error = "no request attempted"
        for attempt in range(self._max_retries):
            if attempt > 0:
                time.sleep(self._backoff_base * 2 ** (attempt - 1))
            try:
                resp = self._http.request(method, path, params=params)
            except httpx.HTTPError as exc:
                last_error = f"network error: {exc}"
                continue

            if resp.status_code in ok_statuses:
                return resp
            if resp.status_code == 401:
                raise AuthError(
                    f"GitHub rejected the token (HTTP 401) for {method} {path}. "
                    f"Check that {TOKEN_ENV_VAR} is set to a valid, unexpired token."
                )
            if resp.status_code == 403:
                if resp.headers.get("X-RateLimit-Remaining") == "0":
                    reset = resp.headers.get("X-RateLimit-Reset", "unknown")
                    raise RateLimitError(
                        f"GitHub API rate limit exhausted (HTTP 403) for {method} {path} "
                        f"(resets at epoch {reset}). Wait and re-run."
                    )
                raise AuthError(
                    f"GitHub denied access (HTTP 403) for {method} {path}. "
                    f"Check that {TOKEN_ENV_VAR} has read access to this repository."
                )
            if resp.status_code == 429:
                last_error = "secondary rate limit (HTTP 429)"
                continue
            if resp.status_code >= 500:
                last_error = f"server error (HTTP {resp.status_code})"
                continue
            raise GitHubError(
                f"Unexpected GitHub response (HTTP {resp.status_code}) for {method} {path}: "
                f"{resp.text[:500]}"
            )

        if "429" in last_error:
            raise RateLimitError(
                f"GitHub secondary rate limit hit repeatedly for {method} {path} after "
                f"{self._max_retries} attempts. Wait and re-run."
            )
        raise TransientError(
            f"GitHub request failed after {self._max_retries} attempts ({last_error}) for "
            f"{method} {path}. Check network connectivity and https://www.githubstatus.com, "
            "then re-run."
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "GitHubClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


def _earliest_review_activity_sha(comments: list[dict], reviews: list[dict]) -> str | None:
    """The commit SHA referenced by the earliest review comment or review.

    Activity without a usable (timestamp, commit) pair — e.g. a PENDING
    review with no submitted_at, or a review missing commit_id — is skipped
    rather than treated as an error, since only *some* entries need a usable
    SHA for us to determine the pre-review state.

    GitHub timestamps are fixed-width UTC ISO-8601 strings (YYYY-MM-DDTHH:MM:SSZ),
    which sort lexicographically in chronological order, so plain string
    comparison avoids any datetime-parsing edge cases.
    """
    activity: list[tuple[str, str]] = []
    for comment in comments:
        sha = comment.get("original_commit_id")
        ts = comment.get("created_at")
        if sha and ts:
            activity.append((ts, sha))
    for review in reviews:
        sha = review.get("commit_id")
        ts = review.get("submitted_at")
        if sha and ts:
            activity.append((ts, sha))

    if not activity:
        return None
    activity.sort(key=lambda pair: pair[0])
    return activity[0][1]


def fetch_pr_snapshot(client: GitHubClient, owner: str, repo: str, number: int) -> PRSnapshot:
    """Fetch the pre-review snapshot of one PR.

    Raises PRExcluded (never falls back to another commit) when:
      - the PR has no review comments/reviews with a usable commit reference, or
      - the determined pre-review commit is no longer reachable (force-push).
    """
    pr = client.get_pull(owner, repo, number)
    base_sha = pr["base"]["sha"]

    comments = client.get_review_comments(owner, repo, number)
    reviews = client.get_reviews(owner, repo, number)

    pre_review_sha = _earliest_review_activity_sha(comments, reviews)
    if pre_review_sha is None:
        raise PRExcluded(
            REASON_NO_REVIEW_ACTIVITY,
            f"{owner}/{repo}#{number} has no review comments or reviews with a usable "
            "commit reference — there is nothing to measure human recall against, "
            "excluding from the corpus.",
        )

    compare_resp = client.compare(owner, repo, base_sha, pre_review_sha)
    if compare_resp.status_code in (404, 422):
        raise PRExcluded(
            REASON_PRE_REVIEW_COMMIT_UNREACHABLE,
            f"{owner}/{repo}#{number}: pre-review commit {pre_review_sha} is unreachable "
            f"(HTTP {compare_resp.status_code}), most likely a force-push rewrote history. "
            "Excluding from the corpus rather than falling back to the merged state.",
        )

    files = [
        PRFile(path=f["filename"], status=f["status"], patch=f.get("patch", ""))
        for f in compare_resp.json().get("files", [])
    ]

    return PRSnapshot(
        repo=f"{owner}/{repo}",
        number=number,
        base_sha=base_sha,
        pre_review_sha=pre_review_sha,
        files=files,
    )
