"""Review engine: one LLM call per diff chunk, everything persisted for reproducibility.

CLAUDE.md requires that "anyone should be able to reproduce a report from a
run directory alone" — so every chunk's exact request (model, messages,
params) and raw response is written to `raw/`, not just the parsed comments.

A malformed model reply must never abort a run: at corpus scale (50-100 PRs,
many chunks each) one bad reply is expected, and losing the whole run over it
would be worse than the recall/hallucination numbers being computed from an
incomplete pass. So parse failures are recorded (errors.json) and reviewing
continues — nothing is ever silently dropped.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from reviewlens.review.chunking import chunk_file_diff
from reviewlens.review.ingest import GitHubClient, PRSnapshot
from reviewlens.review.prompt import Prompt, render_user

DEFAULT_CONTEXT_LINES = 10

_VALID_CATEGORIES = {"bug", "design", "style", "question"}
_VALID_SEVERITIES = {"high", "medium", "low"}
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```$", re.DOTALL)


def _strip_code_fence(content: str) -> str:
    """Defensively strip a ```json ... ``` (or bare ```) fence some models add
    despite the prompt asking for a bare JSON array."""
    match = _CODE_FENCE_RE.match(content.strip())
    return match.group(1).strip() if match else content.strip()


def _validate_comment(element: Any) -> str | None:
    """Return None if `element` is a well-formed comment, else a reason string."""
    if not isinstance(element, dict):
        return f"comment element is not a JSON object: {element!r}"
    file = element.get("file")
    line = element.get("line")
    category = element.get("category")
    severity = element.get("severity")
    comment = element.get("comment")
    if not isinstance(file, str) or not file:
        return f"invalid 'file' (must be a non-empty string): {file!r}"
    if not isinstance(line, int) or isinstance(line, bool):
        return f"invalid 'line' (must be an int): {line!r}"
    if category not in _VALID_CATEGORIES:
        return f"invalid 'category' (must be one of {sorted(_VALID_CATEGORIES)}): {category!r}"
    if severity not in _VALID_SEVERITIES:
        return f"invalid 'severity' (must be one of {sorted(_VALID_SEVERITIES)}): {severity!r}"
    if not isinstance(comment, str) or not comment.strip():
        return f"invalid 'comment' (must be a non-empty string): {comment!r}"
    return None


def parse_review_response(response: dict) -> tuple[list[dict], list[dict]]:
    """Parse one raw OpenRouter response into (valid_comments, errors).

    Kept as a standalone, network-free function so parsing edge cases
    (fenced JSON, non-JSON replies, individually malformed elements) are
    unit-testable without an LLM call. Every rejected element or parse
    failure becomes one entry in the returned errors list — the caller is
    responsible for persisting them, but nothing here decides to drop them.
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return [], [
            {
                "error": f"malformed response structure ({exc})",
                "raw_content": json.dumps(response, ensure_ascii=True),
            }
        ]

    unfenced = _strip_code_fence(content)
    try:
        parsed = json.loads(unfenced)
    except json.JSONDecodeError as exc:
        return [], [{"error": f"invalid JSON ({exc})", "raw_content": content}]

    if not isinstance(parsed, list):
        return [], [
            {
                "error": f"expected a JSON array, got {type(parsed).__name__}",
                "raw_content": content,
            }
        ]

    valid: list[dict] = []
    errors: list[dict] = []
    for element in parsed:
        problem = _validate_comment(element)
        if problem is None:
            valid.append(element)
        else:
            errors.append({"error": problem, "raw_content": json.dumps(element, ensure_ascii=True)})
    return valid, errors


def review_pr(
    snapshot: PRSnapshot,
    github_client: GitHubClient,
    llm_client: Any,
    model: str,
    prompt: Prompt,
    out_dir: str,
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> dict:
    """Review one PR's pre-review diff, one LLM call per chunk.

    Writes `<out_dir>/<owner>__<repo>__<number>/` (comments.json, errors.json
    if non-empty, raw/chunk_<i>.json per call) and returns a small summary
    dict for the caller to fold into run_meta.json.

    Files with status "removed" have no new-side content to review, and
    files with an empty patch have nothing chunkable, so both are skipped
    without an LLM call. "added" files have no pre-review content to fetch
    (file_lines=None disables chunking's context expansion for them); every
    other status is treated as having pre-review content worth fetching for
    context.
    """
    owner, repo = snapshot.repo.split("/", 1)
    pr_dir = os.path.join(out_dir, f"{owner}__{repo}__{snapshot.number}")
    raw_dir = os.path.join(pr_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    comments: list[dict] = []
    errors: list[dict] = []
    chunk_index = 0

    for pr_file in snapshot.files:
        if pr_file.status == "removed" or not pr_file.patch:
            continue

        file_lines = None
        if pr_file.status != "added":
            content = github_client.get_file_content(
                owner, repo, pr_file.path, snapshot.pre_review_sha
            )
            file_lines = content.splitlines()

        for chunk in chunk_file_diff(pr_file.path, pr_file.patch, context_lines, file_lines):
            user_content = render_user(
                prompt.user_template, chunk.file, chunk.start_line, chunk.end_line, chunk.content
            )
            messages = [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": user_content},
            ]
            response = llm_client.complete(model, messages, **prompt.params)

            with open(os.path.join(raw_dir, f"chunk_{chunk_index}.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "request": {"model": model, "messages": messages, "params": prompt.params},
                        "response": response,
                    },
                    f,
                    indent=2,
                    ensure_ascii=True,
                )

            valid, parse_errors = parse_review_response(response)
            for c in valid:
                comments.append({**c, "chunk_index": chunk_index})
            for e in parse_errors:
                errors.append({**e, "chunk_index": chunk_index})

            chunk_index += 1

    with open(os.path.join(pr_dir, "comments.json"), "w", encoding="utf-8") as f:
        json.dump(comments, f, indent=2, ensure_ascii=True)

    if errors:
        with open(os.path.join(pr_dir, "errors.json"), "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=True)

    return {
        "repo": snapshot.repo,
        "number": snapshot.number,
        "chunk_count": chunk_index,
        "comment_count": len(comments),
        "parse_error_count": len(errors),
    }
