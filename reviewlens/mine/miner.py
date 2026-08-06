"""Mining orchestration: page each project's closed PRs newest-first, apply
select.py's filters, fetch pre-review snapshots, and assemble the corpus +
manifest.

The manifest exists so a mined corpus is auditable on its own (CLAUDE.md's
reproducibility rule): every qualification threshold, every skip reason
tally, and the pinned PR list are persisted alongside the data, not just
implied by the code that produced it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from reviewlens.mine.select import (
    MAX_CHANGED_FILES,
    MAX_CHANGED_LINES,
    MIN_COMMENT_BODY_CHARS,
    MIN_QUALIFYING_COMMENTS,
    changed_java_files,
    comment_qualifies,
    is_bot_author,
    pr_is_merged,
    pr_size_ok,
    resolve_canonical_line,
)
from reviewlens.review.ingest import GitHubClient, PRExcluded, PRSnapshot, fetch_pr_snapshot

# Project registry: slug -> owner/repo. Hardcoded per the owner's locked T7
# decision rather than made configurable — the study's corpus is fixed to
# exactly these three projects (CLAUDE.md), so a config file would be
# premature abstraction for a set that never grows.
PROJECT_REGISTRY = {
    "junit5": "junit-team/junit5",
    "mockito": "mockito/mockito",
    "checkstyle": "checkstyle/checkstyle",
}

# Skip-reason tally keys. The four PR-selection reasons are ours; the two
# PRExcluded reasons are reused from ingest.py's REASON_* constants so a
# skip is always tallied under the exact reason the exclusion happened for.
REASON_NOT_MERGED = "not_merged"
REASON_BOT_AUTHOR = "bot_author"
REASON_NO_JAVA_FILES = "no_java_files"
REASON_TOO_LARGE = "too_large"
REASON_TOO_FEW_COMMENTS = "too_few_comments"

_SKIP_REASONS = (
    REASON_NOT_MERGED,
    REASON_BOT_AUTHOR,
    REASON_NO_JAVA_FILES,
    REASON_TOO_LARGE,
    REASON_TOO_FEW_COMMENTS,
    "no_review_activity",
    "pre_review_commit_unreachable",
)


def _resolve_repo(slug: str) -> str:
    try:
        return PROJECT_REGISTRY[slug]
    except KeyError:
        valid = ", ".join(sorted(PROJECT_REGISTRY))
        raise ValueError(f"Unknown project slug '{slug}'. Valid slugs: {valid}.") from None


def _build_pr_record(pr: dict, snapshot: PRSnapshot, qualifying_comments: list[dict]) -> dict:
    """Assemble one corpus JSON record from a list-endpoint PR summary, its
    pre-review snapshot, and its already-filtered human comments."""
    files = [{"path": f.path} for f in snapshot.files]
    human_comments = [
        {
            "id": c["id"],
            "path": c["path"],
            "line": resolve_canonical_line(c),
            "raw_line": c.get("line"),
            "original_line": c.get("original_line"),
            "original_commit_id": c.get("original_commit_id"),
            "in_reply_to_id": c.get("in_reply_to_id"),
            "side": c.get("side"),
            "author": c["user"]["login"],
            "created_at": c["created_at"],
            "body": c["body"],
            "url": c["html_url"],
        }
        for c in qualifying_comments
    ]
    return {
        "repo": snapshot.repo,
        "number": snapshot.number,
        "title": pr.get("title"),
        "html_url": pr.get("html_url"),
        "merged_at": pr.get("merged_at"),
        "author": (pr.get("user") or {}).get("login"),
        "base_sha": snapshot.base_sha,
        "pre_review_sha": snapshot.pre_review_sha,
        "changed_java_files": changed_java_files(files),
        "human_comments": human_comments,
    }


def mine_project(
    client: GitHubClient, slug: str, per_project: int, scan_limit: int
) -> tuple[list[dict], dict]:
    """Mine up to `per_project` qualifying PRs for one project slug.

    Pages the project's closed PRs newest-first (bounded to `scan_limit`
    items so a huge repo's full history is never fully paged), applying the
    T7 qualification checks in order so each rejected PR is tallied under
    exactly one skip reason. Returns (pr_records, manifest_entry_for_slug).
    """
    repo = _resolve_repo(slug)
    owner, name = repo.split("/", 1)

    skipped = {reason: 0 for reason in _SKIP_REASONS}
    unanchored_comments = 0
    pr_records: list[dict] = []
    scanned = 0

    if per_project > 0:
        pulls = client.list_pulls(owner, name, max_items=scan_limit)
        for pr in pulls:
            if len(pr_records) >= per_project:
                break
            scanned += 1

            if not pr_is_merged(pr):
                skipped[REASON_NOT_MERGED] += 1
                continue

            # Bot-authored PRs are rejected from the list payload alone, at
            # zero API cost. Measured on 600 PRs per project: 82% of junit5's
            # and 63% of mockito's merged PRs are renovate/dependabot bumps,
            # which never carry substantive review comments. Letting them
            # reach the comment fetch below would spend one call each — ~460
            # wasted calls per 600 junit5 PRs scanned.
            author = pr.get("user") or {}
            if is_bot_author(author):
                skipped[REASON_BOT_AUTHOR] += 1
                continue

            # Comment filter next, deliberately: it costs one API call and
            # rejects the large majority of PRs, whereas fetch_pr_snapshot
            # costs four. Ordering it after the snapshot fetch would spend
            # ~5 calls on every scanned PR and blow GitHub's 5000/hour limit
            # long before three projects finish mining.
            author_login = author.get("login", "")
            raw_comments = client.get_review_comments(owner, name, pr["number"])
            for comment in raw_comments:
                if resolve_canonical_line(comment) is None:
                    unanchored_comments += 1

            qualifying_comments = [
                c for c in raw_comments if comment_qualifies(c, author_login)
            ]
            if len(qualifying_comments) < MIN_QUALIFYING_COMMENTS:
                skipped[REASON_TOO_FEW_COMMENTS] += 1
                continue

            try:
                snapshot = fetch_pr_snapshot(client, owner, name, pr["number"])
            except PRExcluded as exc:
                skipped[exc.reason] += 1
                continue

            # Size and language checks run against the pre-review file set —
            # exactly what the review engine will later chunk and send to the
            # LLM — rather than the merged diff.
            files = [{"path": f.path, "patch": f.patch} for f in snapshot.files]
            if not changed_java_files(files):
                skipped[REASON_NO_JAVA_FILES] += 1
                continue
            if not pr_size_ok(files):
                skipped[REASON_TOO_LARGE] += 1
                continue

            pr_records.append(_build_pr_record(pr, snapshot, qualifying_comments))

    hit_scan_limit = scanned >= scan_limit and len(pr_records) < per_project

    manifest_entry = {
        "slug": slug,
        "repo": repo,
        "scanned": scanned,
        "selected": len(pr_records),
        "hit_scan_limit": hit_scan_limit,
        "skipped": skipped,
        "unanchored_comments": unanchored_comments,
    }
    return pr_records, manifest_entry


def mine(
    client: GitHubClient,
    projects: list[str],
    per_project: int,
    max_total: int,
    scan_limit: int,
) -> tuple[list[dict], dict]:
    """Mine every requested project into a corpus.

    `max_total` is a global budget shared across projects (checked in the
    order `projects` is given), applied on top of each project's own
    `per_project` cap — so e.g. `--per-project 50` with three projects and
    the default `--max-total 100` still stops at 100 total, not 150.
    """
    all_records: list[dict] = []
    project_entries: list[dict] = []

    for slug in projects:
        remaining = max(0, max_total - len(all_records))
        effective_cap = min(per_project, remaining)
        records, entry = mine_project(client, slug, effective_cap, scan_limit)
        all_records.extend(records)
        project_entries.append(entry)

    manifest = {
        "mined_at": datetime.now(timezone.utc).isoformat(),
        "criteria": {
            "min_comments": MIN_QUALIFYING_COMMENTS,
            "min_comment_chars": MIN_COMMENT_BODY_CHARS,
            "max_changed_files": MAX_CHANGED_FILES,
            "max_changed_lines": MAX_CHANGED_LINES,
            "per_project": per_project,
            "max_total": max_total,
            "scan_limit": scan_limit,
        },
        "projects": project_entries,
        "prs": [
            {"repo": r["repo"], "number": r["number"], "pre_review_sha": r["pre_review_sha"]}
            for r in all_records
        ],
    }
    return all_records, manifest


def write_corpus(out_dir: str, pr_records: list[dict], manifest: dict) -> None:
    """Write one JSON file per PR plus manifest.json to `out_dir`.

    Filenames follow the `<owner>__<repo>__<number>` convention review_pr
    already uses for run directories, so downstream tooling can pattern-match
    consistently across mine/review outputs.
    """
    os.makedirs(out_dir, exist_ok=True)
    for record in pr_records:
        owner, name = record["repo"].split("/", 1)
        path = os.path.join(out_dir, f"{owner}__{name}__{record['number']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=True)
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=True)
