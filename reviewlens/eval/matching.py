"""Match model review comments to human review comments (RQ1 recall / RQ2 hallucination).

CLAUDE.md pins the matching rule (same file, within ±3 lines, semantically
equivalent) as normative and confines matching logic to this package. The
geometric half (`is_candidate`) is cheap and network-free; the semantic
half is delegated to an injectable judge callable so tests never touch the
network and the judge implementation (LLM-backed here) stays swappable.

A false match inflates recall (RQ1) — the exact error this study must not
make — so the judge and its rubric (prompts/match_v1.md) are written to be
conservative, and an unparseable judge reply is always treated as "not
equivalent" rather than silently counted as a match.

Comments (human or model) are plain dicts with at least "file", "line", and
"comment" keys. Model comments already have this shape as produced by
`reviewlens.review.engine.parse_review_response` (`{file, line, category,
severity, comment}` — the extra keys are simply ignored here); human
comments are expected to be normalized to the same three keys by whatever
produces `data/corpus/` mined comments.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable

from reviewlens.review.prompt import Prompt

LINE_TOLERANCE = 3

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n```$", re.DOTALL)

# An injectable match judge: (human_comment, model_comment) -> (equivalent, reason).
JudgeFn = Callable[[dict, dict], "tuple[bool, str]"]


def is_candidate(
    comment_a: dict, comment_b: dict, line_tolerance: int = LINE_TOLERANCE
) -> bool:
    """The geometric half of the matching rule: same file, within LINE_TOLERANCE lines.

    Pure and network-free by design: this is the cheap pre-filter that keeps
    the (necessarily paid) semantic judge off pairs that could never match
    regardless of what the judge would say. Symmetric in its arguments, so
    the ±3 window means the same thing whichever comment is considered first.

    `line_tolerance` defaults to the frozen rule and exists only so
    `reviewlens.eval.sensitivity` can report how much of the measured recall
    depends on the window. Callers that report a headline number must leave
    it alone: varying it silently would make two runs incomparable.
    """
    return (
        comment_a["file"] == comment_b["file"]
        and abs(comment_a["line"] - comment_b["line"]) <= line_tolerance
    )


def render_match_user(
    template: str,
    human_file: str,
    human_line: int,
    human_comment: str,
    model_file: str,
    model_line: int,
    model_comment: str,
) -> str:
    """Substitute the literal `[[TOKEN]]` placeholders in the match_v1 user template.

    Plain str.replace, not str.format: the rubric's system section contains
    literal JSON braces (the output schema example) that str.format would
    misinterpret as replacement fields — same reason render_user exists in
    reviewlens/review/prompt.py.
    """
    text = template.replace("[[HUMAN_FILE]]", human_file)
    text = text.replace("[[HUMAN_LINE]]", str(human_line))
    text = text.replace("[[HUMAN_COMMENT]]", human_comment)
    text = text.replace("[[MODEL_FILE]]", model_file)
    text = text.replace("[[MODEL_LINE]]", str(model_line))
    text = text.replace("[[MODEL_COMMENT]]", model_comment)
    return text


def _strip_code_fence(content: str) -> str:
    """Defensively strip a ```json ... ``` (or bare ```) fence some models add
    despite the rubric asking for a bare JSON object."""
    match = _CODE_FENCE_RE.match(content.strip())
    return match.group(1).strip() if match else content.strip()


def _parse_judge_reply(response: dict) -> tuple[bool, str]:
    """Parse one raw OpenRouter response into (equivalent, reason).

    Mirrors the defensiveness of `parse_review_response` in review/engine.py:
    a malformed response structure, non-JSON content, or a reply missing the
    `equivalent` key must never crash the run — it is treated as "not
    equivalent" with the problem recorded as the reason, since an unparseable
    verdict must never be silently counted as a match.
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return False, f"malformed judge response structure ({exc})"

    # Reasoning models return content=None when the reasoning budget consumes
    # the whole completion; that must read as "not equivalent", never crash.
    if not isinstance(content, str):
        return False, f"judge reply content was {type(content).__name__}, not a string"

    unfenced = _strip_code_fence(content)
    try:
        parsed = json.loads(unfenced)
    except json.JSONDecodeError as exc:
        return False, f"judge reply was not valid JSON ({exc}): {content!r}"

    if not isinstance(parsed, dict) or "equivalent" not in parsed:
        return False, f"judge reply missing 'equivalent' key: {content!r}"

    equivalent = parsed["equivalent"]
    if not isinstance(equivalent, bool):
        return False, f"judge reply 'equivalent' was not a bool: {content!r}"

    reason = parsed.get("reason", "")
    if not isinstance(reason, str):
        reason = str(reason)
    return equivalent, reason


class LlmJudge:
    """LLM-backed semantic-equivalence judge, callable as `judge(human, model)`.

    All calls go through the caller-supplied `client` (an OpenRouterClient),
    so judge verdicts are cached exactly like review comments — a warm re-run
    of the matching pipeline costs $0. `model` is always a parameter, never
    hardcoded, per CLAUDE.md.
    """

    def __init__(self, client, model: str, prompt: Prompt):
        self._client = client
        self._model = model
        self._prompt = prompt

    def __call__(self, human_comment: dict, model_comment: dict) -> tuple[bool, str]:
        user_content = render_match_user(
            self._prompt.user_template,
            human_comment["file"],
            human_comment["line"],
            human_comment["comment"],
            model_comment["file"],
            model_comment["line"],
            model_comment["comment"],
        )
        messages = [
            {"role": "system", "content": self._prompt.system},
            {"role": "user", "content": user_content},
        ]
        response = self._client.complete(self._model, messages, **self._prompt.params)
        return _parse_judge_reply(response)


@dataclass
class MatchResult:
    """Output of `match_comments`: everything RQ1/RQ2 metric computation (T10) needs.

    `judge_log` retains every judge invocation made during matching — including
    ones that returned "not equivalent" — so no verdict is silently dropped;
    T10/T11 can audit *why* a near-miss candidate was rejected, not just the
    final match/no-match outcome.
    """

    matches: list[tuple[dict, dict, str]]  # (human_comment, model_comment, judge_reason)
    unmatched_human: list[dict]  # misses -> RQ1 recall denominator
    unmatched_model: list[dict]  # hallucination candidates -> RQ2
    judge_log: list[tuple[dict, dict, bool, str]]  # every call: (human, model, equivalent, reason)


def match_comments(
    human_comments: list[dict],
    model_comments: list[dict],
    judge: JudgeFn,
    line_tolerance: int = LINE_TOLERANCE,
) -> MatchResult:
    """One-to-one match model comments against human comments.

    Determinism (a CLAUDE.md reproducibility rule) requires a fixed traversal
    order: human comments are visited in the order given, and for each, its
    candidate model comments are tried in order of (abs(line_delta),
    model_line, original_index) — the first the judge calls equivalent wins.
    Model comments already claimed by an earlier human comment are not
    reconsidered, and a human comment claims at most one model comment, so
    the result is a one-to-one matching regardless of input order.
    """
    matches: list[tuple[dict, dict, str]] = []
    judge_log: list[tuple[dict, dict, bool, str]] = []
    matched_model_indices: set[int] = set()
    matched_human_indices: set[int] = set()

    for human_idx, human in enumerate(human_comments):
        candidates = [
            (model_idx, model)
            for model_idx, model in enumerate(model_comments)
            if model_idx not in matched_model_indices
            and is_candidate(human, model, line_tolerance)
        ]
        candidates.sort(
            key=lambda pair: (abs(pair[1]["line"] - human["line"]), pair[1]["line"], pair[0])
        )

        for model_idx, model in candidates:
            equivalent, reason = judge(human, model)
            judge_log.append((human, model, equivalent, reason))
            if equivalent:
                matches.append((human, model, reason))
                matched_model_indices.add(model_idx)
                matched_human_indices.add(human_idx)
                break

    unmatched_human = [h for i, h in enumerate(human_comments) if i not in matched_human_indices]
    unmatched_model = [m for i, m in enumerate(model_comments) if i not in matched_model_indices]

    return MatchResult(
        matches=matches,
        unmatched_human=unmatched_human,
        unmatched_model=unmatched_model,
        judge_log=judge_log,
    )
