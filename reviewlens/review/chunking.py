"""Split a PR file's unified diff into per-file review chunks.

Purpose: large PRs don't fit in an LLM context window, so each file's patch
is broken into hunk-sized chunks (one chunk = one later LLM call). Pure
functions only — no I/O, no LLM calls — so this stays trivially unit
testable and reusable regardless of where the patch/file content came from.

Diff format assumed: the `patch` string is a GitHub-style fragment made only
of unified-diff hunks (no `--- a/...`/`+++ b/...` file headers), e.g. the
`patch` field returned by the GitHub compare/pulls-files APIs:

    @@ -12,3 +12,4 @@
     unchanged line
    -removed line
    +added line
    +another added line
     unchanged line

Chunk.content format: one output line per input line, in new-side (post-diff,
pre-review-file) order, as `"{marker} {new_line_no}: {text}"` where marker is
'+' (added), '-' (removed), or ' ' (context/unchanged), and new_line_no is
the line's 1-based line number in the new-side file, or empty for '-' lines
(a removed line has no line number in the new file). This keeps the exact
text recoverable and keeps new-side line numbers — the numbers Chunk.start_line
/ end_line are expressed in — attached to every line that has one.

Context expansion: `context_lines` extends each hunk by that many lines of
surrounding *new-side* file content (clamped to file boundaries), using the
optional `file_lines` parameter (the full pre-review file, split into lines,
1-indexed conceptually via file_lines[n - 1]). Without file_lines (e.g. a
newly added file, where no pre-review content exists) no expansion happens,
regardless of context_lines, since there is nothing to expand into.
Hunks whose expanded ranges overlap or become adjacent are merged into a
single chunk so the same line is never split across two separate LLM calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

# One raw diff line, reduced to what downstream chunk-building needs:
# (marker, new_lineno, text) — new_lineno is None for removed ('-') lines.
_DiffLine = tuple[str, "int | None", str]


@dataclass
class Chunk:
    """A contiguous, reviewable slice of one file's pre-review new-side lines."""

    file: str
    start_line: int
    end_line: int
    content: str


@dataclass
class _Hunk:
    new_start: int
    new_end: int
    lines: list[_DiffLine]


def _parse_hunks(patch: str) -> list[_Hunk]:
    """Parse a unified-diff patch fragment into a list of _Hunk objects."""
    hunks: list[_Hunk] = []
    current: _Hunk | None = None
    new_ptr = 0
    for raw_line in patch.splitlines():
        header = _HUNK_HEADER_RE.match(raw_line)
        if header:
            new_start = int(header.group(3))
            new_count = int(header.group(4)) if header.group(4) is not None else 1
            new_end = new_start + new_count - 1 if new_count > 0 else new_start - 1
            current = _Hunk(new_start=new_start, new_end=new_end, lines=[])
            hunks.append(current)
            new_ptr = new_start
            continue
        if current is None:
            continue  # stray content before the first hunk header; ignore
        if raw_line.startswith("\\"):
            continue  # "\ No newline at end of file" — not a content line
        if not raw_line:
            continue  # defensive: patch text should not contain bare blank lines
        marker, text = raw_line[0], raw_line[1:]
        if marker == "-":
            current.lines.append(("-", None, text))
        elif marker == "+":
            current.lines.append(("+", new_ptr, text))
            new_ptr += 1
        elif marker == " ":
            current.lines.append((" ", new_ptr, text))
            new_ptr += 1
        # Any other leading character is not valid unified-diff content and is skipped.
    return hunks


def _expanded_range(
    hunk: _Hunk, context_lines: int, file_lines: list[str] | None
) -> tuple[int, int]:
    """The hunk's new-side range after context expansion, clamped to file bounds.

    context_lines=0, or no file_lines available, means literally no expansion.
    """
    if context_lines <= 0 or file_lines is None:
        return hunk.new_start, hunk.new_end
    start = max(1, hunk.new_start - context_lines)
    end = min(len(file_lines), hunk.new_end + context_lines)
    return start, end


def _group_hunks(hunks: list[_Hunk], context_lines: int, file_lines: list[str] | None) -> list[dict]:
    """Group hunks (in file order) whose expanded ranges overlap or touch."""
    groups: list[dict] = []
    for hunk in hunks:
        exp_start, exp_end = _expanded_range(hunk, context_lines, file_lines)
        if groups and exp_start <= groups[-1]["end"] + 1:
            groups[-1]["hunks"].append(hunk)
            groups[-1]["end"] = max(groups[-1]["end"], exp_end)
        else:
            groups.append({"hunks": [hunk], "start": exp_start, "end": exp_end})
    return groups


def _format_line(marker: str, lineno: int | None, text: str) -> str:
    lineno_str = str(lineno) if lineno is not None else ""
    return f"{marker} {lineno_str}: {text}"


def _build_chunk(file: str, group: dict, file_lines: list[str] | None) -> Chunk:
    start, end = group["start"], group["end"]
    out: list[str] = []
    cursor = start
    for hunk in group["hunks"]:
        if file_lines is not None:
            while cursor < hunk.new_start:
                out.append(_format_line(" ", cursor, file_lines[cursor - 1]))
                cursor += 1
        for marker, lineno, text in hunk.lines:
            out.append(_format_line(marker, lineno, text))
        cursor = hunk.new_end + 1
    if file_lines is not None:
        while cursor <= end:
            out.append(_format_line(" ", cursor, file_lines[cursor - 1]))
            cursor += 1
    return Chunk(file=file, start_line=start, end_line=end, content="\n".join(out))


def chunk_file_diff(
    file: str,
    patch: str,
    context_lines: int,
    file_lines: list[str] | None = None,
) -> list[Chunk]:
    """Split one file's unified-diff patch into review chunks.

    file: path, used only to tag the returned Chunks.
    patch: unified-diff hunk fragment (see module docstring for the exact
        assumed format).
    context_lines: how many new-side file lines of context to pull in around
        each hunk before merging overlapping/adjacent hunks. 0 = no expansion.
    file_lines: the full pre-review file, pre-split into lines (no trailing
        newlines), used as the source of context/gap-fill text. None if the
        file has no pre-review content (e.g. newly added) or expansion isn't
        wanted; expansion is then a no-op regardless of context_lines.
    """
    hunks = _parse_hunks(patch)
    if not hunks:
        return []
    groups = _group_hunks(hunks, context_lines, file_lines)
    return [_build_chunk(file, group, file_lines) for group in groups]
