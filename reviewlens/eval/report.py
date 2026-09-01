"""Render an evaluation report as markdown.

Every number printed here traces to a run directory, and anything that has
not actually been measured is written as "not measured" rather than as a
zero, a dash in a results row, or an estimate. That is a project rule, not a
stylistic preference: this report is the artifact a reader would cite.
"""

from __future__ import annotations

from reviewlens.eval.corpus import CategorizationMeta
from reviewlens.eval.metrics import Metrics

NOT_MEASURED = "not measured"


def _pct(value: float | None) -> str:
    return NOT_MEASURED if value is None else f"{value * 100:.1f}%"


def _fraction(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}" if denominator else NOT_MEASURED


def render_report(
    metrics: Metrics,
    run_meta: dict,
    judge_model: str,
    judge_prompt,
    *,
    categorization: CategorizationMeta | None = None,
) -> str:
    """Build the full markdown report for one model's run.

    `categorization` is None whenever the corpus has no `categories.json`
    (categorization is a separate stage, T8, that may not have run) — the
    provenance rows and per-category method note it feeds are simply
    omitted in that case, matching the existing "absent, not fabricated"
    treatment of per-category recall itself.
    """
    prompt_meta = run_meta.get("prompt", {})
    lines: list[str] = []

    lines.append(f"# ReviewLens evaluation — `{run_meta.get('model', 'unknown model')}`")
    lines.append("")

    if not run_meta.get("complete", False):
        lines.append(
            "> **Incomplete run.** This report covers only the PRs the review run "
            f"finished ({metrics.pr_count} of {run_meta.get('corpus_pr_count', '?')} in the corpus). "
            "Treat these numbers as a partial pass, not as the study's result."
        )
        lines.append("")

    lines.append("## Provenance")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Review model | `{run_meta.get('model', '?')}` |")
    lines.append(f"| Review prompt | `{prompt_meta.get('name', '?')}` v{prompt_meta.get('version', '?')} |")
    lines.append(f"| Review prompt sha256 | `{str(prompt_meta.get('sha256', '?'))[:16]}…` |")
    lines.append(f"| Judge model | `{judge_model}` |")
    lines.append(f"| Match rubric | `{judge_prompt.name}` v{judge_prompt.version} |")
    lines.append(f"| Match rubric sha256 | `{judge_prompt.sha256[:16]}…` |")
    if categorization is not None:
        lines.append(f"| Comment categorizer | `{categorization.model}` |")
        lines.append(
            f"| Category rubric | `{categorization.prompt_name}` v{categorization.prompt_version} |"
        )
        lines.append(f"| Category rubric sha256 | `{categorization.prompt_sha256[:16]}…` |")
    lines.append(f"| Corpus | `{run_meta.get('corpus', '?')}` |")
    lines.append(f"| Run started | {run_meta.get('started', '?')} |")
    lines.append(f"| Run finished | {run_meta.get('finished') or 'did not finish'} |")
    providers = _collect_providers(run_meta)
    if providers:
        rendered = ", ".join(f"{name} ({count})" for name, count in providers)
        lines.append(f"| Upstream providers | {rendered} |")
    lines.append("")

    lines.append("## RQ1 — Recall of human review comments")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| PRs evaluated | {metrics.pr_count} |")
    lines.append(f"| Human comments (denominator) | {metrics.human_comment_count} |")
    lines.append(f"| Model comments | {metrics.model_comment_count} |")
    lines.append(f"| Matched | {_fraction(metrics.matched_count, metrics.human_comment_count)} |")
    lines.append(f"| **Recall** | **{_pct(metrics.recall)}** |")
    lines.append("")
    lines.append(
        "Recall here means agreement with the humans who reviewed these PRs, "
        "not absolute defect detection — reviewers miss issues too."
    )
    lines.append("")

    lines.append("### Recall by category")
    lines.append("")
    if metrics.categories_available:
        lines.append("| Category | Matched | Total | Recall |")
        lines.append("|---|---|---|---|")
        for category in metrics.by_category:
            lines.append(
                f"| {category.category} | {category.matched} | {category.total} | "
                f"{_pct(category.recall)} |"
            )
        lines.append("")
        if categorization is not None:
            lines.append(
                "Categories were assigned LLM-assisted, one call per comment — "
                "not by hand and not by keyword rules. "
                f"{categorization.categorized_count} comments carry a category, "
                f"with {categorization.failure_count} categorization failures and "
                f"{categorization.low_confidence_count} assigned at low confidence. "
                "The rubric forces a choice among exactly four categories, so a "
                "comment that fits none is recorded at low confidence rather than "
                "given a fifth category. Category assignment is rubric-sensitive: "
                "a revision of the rubric changed a substantial share of labels, "
                "so per-category recall carries more uncertainty than overall "
                "recall. A reproducible sample of the assignments is re-rated by a "
                "second, independent model against the same frozen rubric (see "
                "`reports/categorization-interrater.md`); no human validated these "
                "labels, so that check measures inter-model consistency in applying "
                "the rubric, not correctness."
            )
    else:
        lines.append(
            "Not available: the mined human comments do not carry categories yet, "
            "so the per-category denominator does not exist. This breakdown stays "
            "absent rather than being reported as zeros."
        )
    lines.append("")

    lines.append("## RQ2 — Unmatched model comments")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(
        f"| Unmatched model comments | "
        f"{_fraction(metrics.unmatched_model_count, metrics.model_comment_count)} |"
    )
    lines.append(f"| Unmatched rate | {_pct(metrics.unmatched_model_rate)} |")
    lines.append(f"| **Hallucination rate** | **{NOT_MEASURED}** |")
    lines.append("")
    lines.append(
        "The unmatched rate is an **upper bound** on hallucination, not the "
        "hallucination rate. A model comment matching no human comment may be "
        "a genuine issue the reviewers did not raise. Separating the two "
        "requires the manual verification pass, which has not been run."
    )
    lines.append("")

    lines.append("## Run health")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Chunks reviewed | {metrics.chunk_count} |")
    lines.append(
        f"| Chunks lost (no output) | "
        f"{_fraction(metrics.lost_chunk_count, metrics.chunk_count)} |"
    )
    lines.append(f"| **Chunk loss rate** | **{_pct(metrics.chunk_loss_rate)}** |")
    lines.append(
        f"| Chunks with a parse error | "
        f"{_fraction(metrics.error_chunk_count, metrics.chunk_count)} |"
    )
    lines.append(f"| Error-chunk rate | {_pct(metrics.error_chunk_rate)} |")
    lines.append(
        f"| Malformed items per chunk | {_pct(metrics.parse_failure_rate)} |"
    )
    lines.append(
        f"| &nbsp;&nbsp;— of which provider-caused | "
        f"{_fraction(metrics.provider_error_items, metrics.parse_error_items)} |"
    )
    lines.append(
        f"| &nbsp;&nbsp;— of which model-caused | "
        f"{_fraction(metrics.model_error_items, metrics.parse_error_items)} |"
    )
    lines.append("")
    lines.append(
        "**Chunk loss rate** is the headline coverage number: a lost chunk "
        "contributed zero model comments, so it depresses recall for reasons "
        "unrelated to review ability, and is reported next to recall so the two "
        "are read together. **Malformed items per chunk** counts individual "
        "rejected items rather than lost chunks — a chunk can carry a malformed "
        "item and still contribute other, valid comments — so this rate is not a "
        "chunk-loss rate and can exceed 1. Provider-caused failures are delivery "
        "faults (the model was billed and generated tokens, but the provider "
        "returned a null content field) and are not attributable to the model."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def _collect_providers(run_meta: dict) -> list[tuple[str, int]]:
    """Tally which upstreams served the run, most-used first."""
    totals: dict[str, int] = {}
    for summary in run_meta.get("pr_summaries", []):
        for name, count in (summary.get("providers") or {}).items():
            totals[name] = totals.get(name, 0) + count
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))
