"""Pure, network-free mining predicates: which PRs and which review comments
belong in the corpus.

Kept separate from miner.py's GitHub orchestration so every qualification
rule (RQ1's ground truth depends on getting these right) is unit-testable
against plain dicts, with no mocked HTTP transport required. Everything here
operates on plain dicts/strings/lists — miner.py is responsible for
adapting GitHubClient's dataclasses (PRFile, PRSnapshot) into that shape.
"""

from __future__ import annotations

import re

# Corpus qualification thresholds (T7, locked by the owner). Also surfaced
# in the mining manifest's "criteria" block so a corpus is self-documenting.
MIN_QUALIFYING_COMMENTS = 2
MIN_COMMENT_BODY_CHARS = 30
MAX_CHANGED_FILES = 50
MAX_CHANGED_LINES = 2000

# Fenced code blocks first (they may themselves contain '>' lines that would
# otherwise be mistaken for quote markers), then quote lines.
_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_QUOTE_LINE_RE = re.compile(r"(?m)^>.*$")


def pr_is_merged(pr: dict) -> bool:
    """A PR only qualifies once merged — an open or closed-unmerged PR has
    no stable final diff and no guarantee its review comments reflect
    accepted judgments."""
    return pr.get("merged_at") is not None


def normalize_comment_body(body: str) -> str:
    """Strip quoted lines and fenced code blocks, then surrounding whitespace.

    A comment that merely echoes a code fence or quotes another comment back
    carries no reviewer-authored signal, so it must not count toward the
    length threshold even if its raw length would otherwise clear it.
    """
    without_fences = _FENCE_RE.sub("", body or "")
    without_quotes = _QUOTE_LINE_RE.sub("", without_fences)
    return without_quotes.strip()


def is_bot_author(user: dict) -> bool:
    """True for a GitHub-typed bot account, or the `[bot]`-suffixed login
    convention some bot integrations use instead of setting `type`."""
    login = user.get("login") or ""
    return user.get("type") == "Bot" or login.endswith("[bot]")


def resolve_canonical_line(comment: dict) -> int | None:
    """The pre-review line a comment anchors to.

    ReviewLens reviews the PR's pre-review state (CLAUDE.md), so a human
    comment must be anchored to the line as the reviewer saw it, not as of
    the merged diff: `original_line` is GitHub's line-in-the-diff-at-comment-
    time, so it wins over `line` (which GitHub updates as the PR is pushed
    to). If neither is set the comment is unanchored (outdated or
    file-level) and cannot be matched against pre-review code at all.
    """
    original_line = comment.get("original_line")
    if original_line is not None:
        return original_line
    return comment.get("line")


def is_reply(comment: dict) -> bool:
    """True for a comment posted inside an existing review thread.

    GitHub sets `in_reply_to_id` only on replies, so its absence identifies
    the comment that opened a thread.
    """
    return comment.get("in_reply_to_id") is not None


def comment_qualifies(comment: dict, pr_author_login: str) -> bool:
    """Whether one raw GitHub review comment counts as ground-truth review
    activity for RQ1's recall denominator."""
    path = comment.get("path") or ""
    if not path.endswith(".java"):
        return False
    # One review thread is one human finding: replies continue a discussion
    # ("Alright, that extra test is good to have") rather than raise a new
    # issue, and no model comment could ever match them. Measured on the
    # first 90-PR corpus, replies were 35% of the denominator, so counting
    # them would depress RQ1 recall by up to a third.
    if is_reply(comment):
        return False
    if is_bot_author(comment.get("user") or {}):
        return False
    if (comment.get("user") or {}).get("login") == pr_author_login:
        return False
    if len(normalize_comment_body(comment.get("body") or "")) < MIN_COMMENT_BODY_CHARS:
        return False
    if resolve_canonical_line(comment) is None:
        return False
    return True


def changed_java_files(files: list[dict]) -> list[str]:
    """Paths of the `.java` files among a PR's changed files, in order."""
    return [f["path"] for f in files if f["path"].endswith(".java")]


def count_changed_lines(patch: str) -> int:
    """Additions+deletions implied by a unified-diff patch string.

    Mirrors GitHub's own additions+deletions accounting: every added/removed
    line except the `+++`/`---` file-header lines. Computed from the patch
    text (rather than requiring a second API call for file-level stats)
    because it only needs data GitHubClient already fetches.
    """
    count = 0
    for line in (patch or "").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") or line.startswith("-"):
            count += 1
    return count


def pr_size_ok(files: list[dict]) -> bool:
    """Size cap for review-cost control: at most MAX_CHANGED_FILES files and
    MAX_CHANGED_LINES changed lines. Applied to the PR's pre-review file set
    (what actually gets sent to the LLM), not the final merged diff."""
    if len(files) > MAX_CHANGED_FILES:
        return False
    total_lines = sum(count_changed_lines(f.get("patch", "")) for f in files)
    return total_lines <= MAX_CHANGED_LINES
