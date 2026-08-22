"""CLI entry point: `python -m reviewlens.eval --run … --judge-model … --report …`.

Thin wiring only: loading lives in corpus.py, the matching rule in
matching.py, aggregation in metrics.py, and rendering in report.py.

Alongside the markdown report this writes `eval_matches.json` back into the
run directory, holding every match, every miss, and every judge verdict —
including the rejections. A report that cannot be re-derived, or audited
comment by comment, is not evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from reviewlens.eval.corpus import load_eval_inputs
from reviewlens.eval.matching import LlmJudge, match_comments
from reviewlens.eval.metrics import compute_metrics
from reviewlens.eval.report import render_report
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.prompt import load_prompt

_MATCH_PROMPT_RELATIVE_PATH = os.path.join("prompts", "match_v1.md")
MATCHES_FILENAME = "eval_matches.json"


def _repo_root() -> str:
    """The repo root, derived from this file's location (never cwd), so the
    rubric path resolves the same way regardless of where the CLI is run."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _serialize_matches(per_pr_results) -> list[dict]:
    """Flatten per-PR results into an auditable JSON record."""
    return [
        {
            "repo": pr.repo,
            "number": pr.number,
            "matches": [
                {"human": human, "model": model, "reason": reason}
                for human, model, reason in result.matches
            ],
            "unmatched_human": result.unmatched_human,
            "unmatched_model": result.unmatched_model,
            "judge_log": [
                {"human": human, "model": model, "equivalent": equivalent, "reason": reason}
                for human, model, equivalent, reason in result.judge_log
            ],
        }
        for pr, result in per_pr_results
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval",
        description="Match model comments to human comments and compute recall/hallucination metrics.",
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Run directory produced by reviewlens.review (e.g. runs/<model-id>/).",
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path for the markdown evaluation report (e.g. reports/<model-id>.md).",
    )
    parser.add_argument(
        "--judge-model",
        required=True,
        help="OpenRouter model ID used to judge semantic equivalence of comment pairs.",
    )
    parser.add_argument(
        "--corpus",
        default=None,
        help="Override the corpus directory recorded in the run's run_meta.json.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the LLM response cache and force fresh judge calls.",
    )
    args = parser.parse_args(argv)

    try:
        inputs = load_eval_inputs(args.run, args.corpus)
    except FileNotFoundError as exc:
        sys.exit(str(exc))

    if inputs.missing_from_corpus:
        sys.exit(
            "Run and corpus disagree: the run reviewed PRs the corpus does not contain "
            f"({', '.join(inputs.missing_from_corpus)}). Evaluating anyway would compute "
            "recall against the wrong denominator."
        )

    judge_prompt = load_prompt(os.path.join(_repo_root(), _MATCH_PROMPT_RELATIVE_PATH))
    llm_client = OpenRouterClient(use_cache=not args.no_cache)
    judge = LlmJudge(llm_client, args.judge_model, judge_prompt)

    per_pr_results = []
    try:
        for pr in inputs.prs:
            result = match_comments(pr.human_comments, pr.model_comments, judge)
            per_pr_results.append((pr, result))
            print(
                f"{pr.repo}#{pr.number}: {len(result.matches)}/{len(pr.human_comments)} "
                f"human comments matched, {len(result.unmatched_model)} model comments unmatched"
            )
    finally:
        llm_client.close()

    metrics = compute_metrics(per_pr_results)

    matches_path = os.path.join(args.run, MATCHES_FILENAME)
    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(_serialize_matches(per_pr_results), f, indent=2, ensure_ascii=True)

    report_dir = os.path.dirname(os.path.abspath(args.report))
    os.makedirs(report_dir, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(
            render_report(
                metrics,
                inputs.run_meta,
                args.judge_model,
                judge_prompt,
                categorization=inputs.categorization,
            )
        )

    if inputs.missing_from_run:
        print(
            f"Note: {len(inputs.missing_from_run)} corpus PRs were not reviewed by this run "
            "and are excluded from the denominator."
        )
    print(f"Wrote {args.report} and {matches_path}.")


if __name__ == "__main__":
    main()
