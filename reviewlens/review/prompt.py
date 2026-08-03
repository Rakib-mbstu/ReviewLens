"""Load and render the versioned review prompt (prompts/review_v1.md).

Frontmatter is deliberately simple (flat `key: value` pairs plus one nested
`params:` block) so it can be parsed without adding a YAML dependency —
CLAUDE.md caps this project at stdlib + httpx-level dependencies. Once a
prompt version is frozen (T6) it is never edited in place, so the file's
sha256 is carried into run metadata: that is what lets a run be tied back to
the exact prompt bytes that produced it, independent of the `version` field
a human might forget to bump.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

_FRONTMATTER_DELIM = "---"
_SYSTEM_MARKER = "## System"
_USER_MARKER = "## User"


@dataclass
class Prompt:
    """A loaded, versioned review prompt ready to render per chunk."""

    name: str
    version: int
    params: dict
    system: str
    user_template: str
    sha256: str


def _strip_inline_comment(line: str) -> str:
    """Drop a trailing ` # comment`; lines without '#' pass through unchanged."""
    idx = line.find("#")
    return line if idx == -1 else line[:idx]


def _parse_scalar(value: str) -> object:
    """Parse a bare frontmatter scalar: float if numeric, else the raw string."""
    try:
        return float(value)
    except ValueError:
        return value


def _parse_frontmatter(fm_lines: list[str]) -> tuple[dict, dict]:
    """Parse flat `key: value` pairs plus one nested `params:` block.

    This is intentionally not a general YAML parser — only what
    prompts/review_v1.md actually uses: top-level scalars, and exactly one
    indented block (`params:`) of further scalars.
    """
    top_level: dict = {}
    params: dict = {}
    in_params = False
    for raw_line in fm_lines:
        line = _strip_inline_comment(raw_line).rstrip()
        if not line.strip():
            continue
        if line[0] in " \t":
            if in_params:
                key, _, value = line.strip().partition(":")
                params[key.strip()] = _parse_scalar(value.strip())
            continue  # stray indentation outside a nested block; ignore
        in_params = False
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            in_params = key == "params"
            continue
        top_level[key] = value
    return top_level, params


def load_prompt(path: str | os.PathLike) -> Prompt:
    """Load and parse a versioned prompt file into a `Prompt`.

    Raises ValueError with an actionable message if the file doesn't match
    the expected frontmatter/`## System`/`## User` shape — a malformed
    prompt file should fail loudly at startup, not surface as a confusing
    downstream error once reviewing is underway.
    """
    with open(path, "rb") as f:
        raw_bytes = f.read()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8")

    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        raise ValueError(f"{path}: expected frontmatter starting with '---'")
    try:
        end_idx = next(
            i for i in range(1, len(lines)) if lines[i].strip() == _FRONTMATTER_DELIM
        )
    except StopIteration:
        raise ValueError(f"{path}: frontmatter is not closed with a second '---'") from None

    top_level, params = _parse_frontmatter(lines[1:end_idx])
    if "name" not in top_level or "version" not in top_level:
        raise ValueError(f"{path}: frontmatter must set 'name' and 'version'")

    body = "\n".join(lines[end_idx + 1 :])
    if _SYSTEM_MARKER not in body or _USER_MARKER not in body:
        raise ValueError(f"{path}: missing '## System' or '## User' section")
    system_idx = body.index(_SYSTEM_MARKER)
    user_idx = body.index(_USER_MARKER)
    system = body[system_idx + len(_SYSTEM_MARKER) : user_idx].strip()
    user_template = body[user_idx + len(_USER_MARKER) :].strip()

    return Prompt(
        name=top_level["name"],
        version=int(top_level["version"]),
        params=params,
        system=system,
        user_template=user_template,
        sha256=sha256,
    )


def render_user(template: str, file: str, start_line: int, end_line: int, chunk_content: str) -> str:
    """Substitute the literal `[[TOKEN]]` placeholders in the user template.

    Plain str.replace, not str.format: the prompt body contains literal JSON
    braces (the output schema example) that str.format would misinterpret
    as replacement fields.
    """
    text = template.replace("[[FILE]]", file)
    text = text.replace("[[START_LINE]]", str(start_line))
    text = text.replace("[[END_LINE]]", str(end_line))
    text = text.replace("[[CHUNK]]", chunk_content)
    return text
