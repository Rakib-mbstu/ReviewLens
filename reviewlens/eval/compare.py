"""CLI entry point: `python -m reviewlens.eval.compare --runs … --report …`.

RQ3 asks how results vary across models. Answering it means putting several
runs side by side, and the honest version of that table needs three things a
per-model report cannot provide on its own.

First, a **shared denominator**: the runs must cover the same PRs, or the
recall column compares different questions. This module refuses to emit a
table when the runs disagree about which PRs they reviewed.

Second, **uncertainty**. On a corpus this size a recall difference of a few
points rests on a handful of matched comments, and a bare percentage invites
a reader to believe an ordering the data does not support. Every recall is
printed with a Wilson score interval, and the pairwise Fisher exact p-value
against the lowest-recall arm is reported so a non-significant gap cannot be
mistaken for a finding.

Third, **efficiency**. Models differ enormously in how much they say under
the same prompt, and volume is not capability: a model can reach a higher
recall purely by commenting everywhere. Matches-per-comment separates the
two, and reachability (human comments with any candidate inside the line
window) shows whether a low recall came from not looking or from disagreeing.

The delivery channel (`via` in run_meta) is printed for every arm, because a
model reached through an agent harness did not get the same treatment as one
reached over the API and the comparison is confounded to that extent.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from math import comb

from reviewlens.eval.corpus import RUN_META_FILENAME, pr_key
from reviewlens.eval.matching import LINE_TOLERANCE

MATCHES_FILENAME = "eval_matches.json"


def wilson_interval(successes: int, total: int, z: float = 1.96) -> "tuple[float, float] | None":
    """Wilson score interval for a proportion, or None when there is no data.

    Wilson rather than the normal approximation because recall here is a
    small proportion over a small denominator, exactly where the normal
    interval misbehaves (it can dip below zero and is far too narrow).
    """
    if total <= 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for the 2x2 table [[a, b], [c, d]].

    Exact rather than chi-squared: the matched-comment counts are single
    digits, where chi-squared's approximation is not trustworthy.
    """
    def table_prob(w: int, x: int, y: int, z_: int) -> float:
        return comb(w + x, w) * comb(y + z_, y) / comb(w + x + y + z_, w + y)

    observed = table_prob(a, b, c, d)
    total = 0.0
    for i in range(0, min(a + b, a + c) + 1):
        j, k = a + b - i, a + c - i
        l = d - (a - i)
        if j < 0 or k < 0 or l < 0:
            continue
        prob = table_prob(i, j, k, l)
        if prob <= observed + 1e-12:
            total += prob
    return min(1.0, total)


def summarize_run(run_dir: str) -> dict:
    """Read one evaluated run into the row the comparison table needs."""
    with open(os.path.join(run_dir, RUN_META_FILENAME), encoding="utf-8") as f:
        run_meta = json.load(f)
    matches_path = os.path.join(run_dir, MATCHES_FILENAME)
    if not os.path.isfile(matches_path):
        sys.exit(
            f"No {MATCHES_FILENAME} in {run_dir}. Run `python -m reviewlens.eval` on it "
            "first — the comparison reads evaluated runs, it does not evaluate them."
        )
    with open(matches_path, encoding="utf-8") as f:
        per_pr = json.load(f)

    matched = sum(len(p["matches"]) for p in per_pr)
    human = matched + sum(len(p["unmatched_human"]) for p in per_pr)
    model = matched + sum(len(p["unmatched_model"]) for p in per_pr)
    reachable = sum(
        len({(j["human"]["file"], j["human"]["line"]) for j in p["judge_log"]}) for p in per_pr
    )
    summaries = run_meta.get("pr_summaries", [])
    return {
        "model": run_meta.get("model", "?"),
        "via": run_meta.get("via", "unrecorded"),
        "complete": run_meta.get("complete", False),
        "prs": sorted(pr_key(p["repo"], p["number"]) for p in per_pr),
        "human_comments": human,
        "model_comments": model,
        "matched": matched,
        "reachable": reachable,
        "chunks": sum(s.get("chunk_count", 0) for s in summaries),
        "parse_errors": sum(s.get("parse_error_count", 0) for s in summaries),
    }


def _pct(value: "float | None") -> str:
    return "not measured" if value is None else f"{value * 100:.1f}%"


def render_comparison(rows: list[dict], judge_model: str) -> str:
    """Render the cross-model table, uncertainty and confounds included."""
    baseline = min(rows, key=lambda r: (r["matched"] / r["human_comments"] if r["human_comments"] else 0))
    human_total = rows[0]["human_comments"]
    lines = [
        "# RQ3 — cross-model comparison",
        "",
        f"All arms reviewed the **same {len(rows[0]['prs'])} PRs** carrying "
        f"**{human_total} human review comments**, through the same frozen prompt, "
        f"the same chunker, and the same matcher (same file, ±{LINE_TOLERANCE} lines, "
        f"semantic equivalence judged by `{judge_model}`).",
        "",
        "## Recall",
        "",
        "| Arm | Via | Model comments | Matched | Recall | 95% CI | p vs lowest |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        n, k = row["human_comments"], row["matched"]
        ci = wilson_interval(k, n)
        ci_text = "—" if ci is None else f"[{ci[0]*100:.1f}%, {ci[1]*100:.1f}%]"
        if row is baseline or not human_total:
            p_text = "—"
        else:
            p = fisher_exact_two_sided(k, n - k, baseline["matched"], n - baseline["matched"])
            p_text = f"{p:.3f}" + ("" if p < 0.05 else " (n.s.)")
        lines.append(
            f"| `{row['model']}` | {row['via']} | {row['model_comments']} | {k} | "
            f"**{_pct(k / n if n else None)}** | {ci_text} | {p_text} |"
        )
    lines += [
        "",
        "A gap marked **n.s.** is not evidence of an ordering. On a corpus this "
        "size recall rests on single-digit match counts, and the intervals overlap.",
        "",
        "## Efficiency and reach",
        "",
        "| Arm | Comments per chunk | Matches per comment | Reachable | Parse failures |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        cpc = row["model_comments"] / row["chunks"] if row["chunks"] else None
        mpc = row["matched"] / row["model_comments"] if row["model_comments"] else None
        lines.append(
            f"| `{row['model']}` | {cpc:.2f} | {_pct(mpc)} | "
            f"{row['reachable']}/{row['human_comments']} "
            f"({_pct(row['reachable']/row['human_comments'] if row['human_comments'] else None)}) | "
            f"{row['parse_errors']}/{row['chunks']} |"
        )
    lines += [
        "",
        "`Reachable` counts human comments with at least one model comment inside the "
        f"±{LINE_TOLERANCE} window — the ceiling recall could reach if the judge accepted "
        "every pair it saw. A low recall with high reachability means the model looked in "
        "the right place and raised a different issue; a low recall with low reachability "
        "means it never looked.",
        "",
        "`Matches per comment` is the closest thing here to precision against human "
        "judgement. It is the column least sensitive to a single match landing or not.",
        "",
        "## Confounds",
        "",
        "Arms differ in **delivery channel**, not only in model. An arm marked "
        "`claude-code-subagent` was reached through an agent harness rather than the "
        "OpenRouter API: no temperature control, and the harness's own system prompt "
        "wrapped every call. A difference between an `openrouter` arm and a "
        "`claude-code-subagent` arm mixes model capability with that channel, and cannot "
        "be attributed to capability alone.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv: "list[str] | None" = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval.compare",
        description="Compare several evaluated runs on a shared corpus (RQ3).",
    )
    parser.add_argument("--runs", nargs="+", required=True, help="Evaluated run directories.")
    parser.add_argument("--report", required=True, help="Path for the markdown comparison.")
    parser.add_argument("--judge-model", required=True, help="Judge model used for all arms.")
    args = parser.parse_args(argv)

    rows = [summarize_run(d) for d in args.runs]
    if len({tuple(r["prs"]) for r in rows}) != 1:
        sys.exit(
            "The runs do not cover the same PRs, so a shared recall denominator does not "
            "exist and the columns would not be comparable. Evaluate them against one corpus."
        )
    incomplete = [r["model"] for r in rows if not r["complete"]]
    if incomplete:
        print(f"Note: partial runs included ({', '.join(incomplete)}).")

    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(render_comparison(rows, args.judge_model))
    for row in rows:
        n = row["human_comments"]
        print(f"{row['model']:38s} recall {row['matched']}/{n} = {row['matched']/n*100:.1f}%")
    print(f"Wrote {args.report}.")


if __name__ == "__main__":
    main()
