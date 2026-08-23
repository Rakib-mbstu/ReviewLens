"""CLI entry point: `python -m reviewlens.eval.sensitivity --run … --judge-model …`.

The matching rule pairs a model comment with a human comment only when they
sit within ±3 lines of each other in the same file. On the first real run,
most human comments had no model comment inside that window at all, so the
±3 choice — not the model's judgment — was deciding the majority of the
recall number. That is a threat to how RQ1 should be read: "the model missed
this issue" and "the model raised this issue somewhere else in the file" are
different failures, and the headline recall figure cannot tell them apart.

This module re-runs matching at several windows and reports recall at each.
It does NOT change the rule: `match_v1` and the ±3 tolerance stay frozen, and
the number reported in the evaluation report is always the ±3 one. This is a
sensitivity result published alongside it, so a reader can see how much of
the measured recall is line anchoring and how much is genuine disagreement
about the issue.

Re-judging the same pair at a wider window is free: the response cache keys
on the rendered messages, so a pair already judged at ±3 replays at $0.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from reviewlens.eval.corpus import load_eval_inputs
from reviewlens.eval.matching import LINE_TOLERANCE, LlmJudge
from reviewlens.eval.report import NOT_MEASURED
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.prompt import load_prompt

_MATCH_PROMPT_RELATIVE_PATH = os.path.join("prompts", "match_v1.md")
DEFAULT_WINDOWS = (3, 5, 10, 25)


def _repo_root() -> str:
    """The repo root, derived from this file's location (never cwd), so the
    rubric path resolves the same way regardless of where the CLI is run."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _pct(value: float | None) -> str:
    return NOT_MEASURED if value is None else f"{value * 100:.1f}%"


def measure_window(prs: list, judge, line_tolerance: int) -> dict:
    """Recall and reachability at one line window.

    `reachable` is the count of human comments with at least one model comment
    inside the window — the ceiling recall could reach at this tolerance even
    if the judge accepted every pair it saw. Reporting it next to recall is
    the point of the whole exercise: it splits "wrong place" from "wrong
    issue".
    """
    from reviewlens.eval.matching import is_candidate, match_comments

    matched = human_total = reachable = judge_calls = 0
    for pr in prs:
        result = match_comments(
            pr.human_comments, pr.model_comments, judge, line_tolerance
        )
        matched += len(result.matches)
        judge_calls += len(result.judge_log)
        human_total += len(pr.human_comments)
        for human in pr.human_comments:
            if any(
                is_candidate(human, model, line_tolerance)
                for model in pr.model_comments
            ):
                reachable += 1
    return {
        "line_tolerance": line_tolerance,
        "human_comments": human_total,
        "reachable": reachable,
        "reachable_rate": reachable / human_total if human_total else None,
        "matched": matched,
        "recall": matched / human_total if human_total else None,
        "judge_calls": judge_calls,
    }


def render_markdown(rows: list[dict], run_meta: dict, judge_model: str) -> str:
    """Render the sensitivity table, marking which row is the frozen rule."""
    lines = [
        f"# Line-window sensitivity — `{run_meta.get('model', '?')}`",
        "",
        "Recall as a function of the matching rule's line window. **The frozen "
        f"rule is ±{LINE_TOLERANCE}, and that row is the study's reported recall.** "
        "The wider windows are diagnostic only — they are not a re-definition of "
        "the rule, and comparing them across models would be invalid.",
        "",
        f"Judge model: `{judge_model}`. Run: `{run_meta.get('model', '?')}`, "
        f"{'complete' if run_meta.get('complete') else 'PARTIAL'}.",
        "",
        "| Window | Reachable | Reachable % | Matched | Recall | Judge calls |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        marker = " (frozen rule)" if row["line_tolerance"] == LINE_TOLERANCE else ""
        lines.append(
            f"| ±{row['line_tolerance']}{marker} | {row['reachable']}/{row['human_comments']} | "
            f"{_pct(row['reachable_rate'])} | {row['matched']} | **{_pct(row['recall'])}** | "
            f"{row['judge_calls']} |"
        )
    lines += [
        "",
        "`Reachable` counts human comments with at least one model comment inside "
        "the window — the ceiling recall could reach at that tolerance if the judge "
        "accepted every pair. The gap between Reachable % and Recall is disagreement "
        "about the issue; the gap between 100% and Reachable % is the model "
        "commenting somewhere else entirely.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval.sensitivity",
        description="Report how measured recall varies with the matching rule's line window.",
    )
    parser.add_argument("--run", required=True, help="Run directory produced by reviewlens.review.")
    parser.add_argument(
        "--judge-model", required=True, help="OpenRouter model ID used to judge equivalence."
    )
    parser.add_argument("--report", required=True, help="Path for the markdown sensitivity table.")
    parser.add_argument(
        "--windows",
        default=",".join(str(w) for w in DEFAULT_WINDOWS),
        help=f"Comma-separated line windows (default: {','.join(str(w) for w in DEFAULT_WINDOWS)}).",
    )
    parser.add_argument("--corpus", default=None, help="Override the corpus recorded in run_meta.")
    parser.add_argument("--no-cache", action="store_true", help="Bypass the LLM response cache.")
    args = parser.parse_args(argv)

    try:
        windows = sorted({int(w) for w in args.windows.split(",") if w.strip()})
    except ValueError:
        sys.exit(f"--windows must be comma-separated integers, got {args.windows!r}")
    if not windows:
        sys.exit("--windows must name at least one window.")
    if LINE_TOLERANCE not in windows:
        sys.exit(
            f"--windows must include the frozen rule (±{LINE_TOLERANCE}), otherwise the "
            "table has nothing to anchor the reported recall against."
        )

    try:
        inputs = load_eval_inputs(args.run, args.corpus)
    except FileNotFoundError as exc:
        sys.exit(str(exc))
    if inputs.missing_from_corpus:
        sys.exit(
            f"{len(inputs.missing_from_corpus)} reviewed PRs are absent from the corpus; "
            "this would compute recall against the wrong denominator."
        )

    llm_client = OpenRouterClient(use_cache=not args.no_cache)
    try:
        judge_prompt = load_prompt(os.path.join(_repo_root(), _MATCH_PROMPT_RELATIVE_PATH))
        judge = LlmJudge(llm_client, args.judge_model, judge_prompt)
        rows = []
        for window in windows:
            row = measure_window(inputs.prs, judge, window)
            rows.append(row)
            print(
                f"±{window}: reachable {row['reachable']}/{row['human_comments']} "
                f"({_pct(row['reachable_rate'])}), recall {_pct(row['recall'])} "
                f"after {row['judge_calls']} judge calls"
            )
    finally:
        llm_client.close()

    report_dir = os.path.dirname(os.path.abspath(args.report))
    os.makedirs(report_dir, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(render_markdown(rows, inputs.run_meta, args.judge_model))
    json_path = os.path.splitext(args.report)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_model": inputs.run_meta.get("model"),
                "run_complete": inputs.run_meta.get("complete"),
                "judge_model": args.judge_model,
                "frozen_line_tolerance": LINE_TOLERANCE,
                "match_prompt_sha256": judge_prompt.sha256,
                "windows": rows,
            },
            f,
            indent=2,
        )
    print(f"Wrote {args.report} and {json_path}.")


if __name__ == "__main__":
    main()
