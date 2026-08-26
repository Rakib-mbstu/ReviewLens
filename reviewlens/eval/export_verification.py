"""CLI entry point: `python -m reviewlens.eval.export_verification --run … --out …`.

CLAUDE.md requires the pipeline to support sampling >=20% of matches/
hallucination judgments for manual review, and the README promises that
figure is reported. This module is the export that makes that promise
checkable: it performs no new analysis and makes no LLM calls, it only
reads `eval_matches.json` (written by `reviewlens.eval`) and formats a
sample of it into a CSV a human can fill in by hand.

Two populations are sampled *independently*, not pooled into one 20%:

* `match` — every accepted (human, model) pair. Verifying these tests RQ1:
  a judge false positive here inflates recall.
* `unmatched_model` — every model comment the judge never matched.
  Verifying these is what turns RQ2's unmatched count from an *upper
  bound* on hallucinations into a real hallucination rate.

The two populations are rarely the same size. Pooling them and drawing one
20% sample would let whichever population is smaller receive near-zero
coverage by chance (e.g. 5 unmatched-model comments against 200 matches),
silently breaking the >=20% guarantee for that population even though the
pooled total looks fine. Sampling each population on its own is the only
way to guarantee >=20% coverage of *both*.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys

MATCHES_FILENAME = "eval_matches.json"

FIELDNAMES = [
    "judgment_id",
    "run",
    "kind",
    "repo",
    "pr_number",
    "pr_url",
    "file",
    "human_line",
    "human_comment",
    "human_url",
    "model_line",
    "model_category",
    "model_severity",
    "model_comment",
    "pipeline_verdict",
    "judge_reason",
    "human_verdict",
    "human_notes",
]

MATCH_KIND = "match"
UNMATCHED_MODEL_KIND = "unmatched_model"


def _pr_url(repo: str, number: int) -> str:
    return f"https://github.com/{repo}/pull/{number}"


def run_slug(model: str) -> str:
    """Slugify a run's model id for use inside a judgment id.

    Only characters that would make an id awkward to paste, sort, or use as
    a filename are replaced; the model stays readable so an id still tells a
    human which arm produced the comment.
    """
    return re.sub(r"[^A-Za-z0-9._-]+", "__", model)


def _judgment_id(slug: str, repo: str, number: int, kind: str, index: int) -> str:
    """A stable, reconstructable id for one judgment: safe to use as a
    lookup key and to hand back to the owner as a pointer into the run.

    The run's model slug leads the id because (repo, number, kind, index) is
    NOT unique across runs — two arms that reviewed the same PR produce the
    same trailing coordinates, so ids built without a run component collide
    silently the moment several arms' exports are joined on judgment_id, and
    the colliding rows are dropped rather than flagged.

    Uniqueness contract: an id is unique within a run, and unique across runs
    of *different* models. Two runs of the SAME model (say a full-corpus pass
    and a subset pass) still share ids, so the globally safe join key is the
    (`run`, `judgment_id`) pair — which is why `run` is a column.
    """
    safe_repo = repo.replace("/", "__")
    return f"{slug}__{safe_repo}__{number}__{kind}__{index}"


def load_eval_matches(run_dir: str) -> list[dict]:
    """Read a run's eval_matches.json, failing loudly if eval hasn't run yet.

    Wording mirrors reviewlens.eval.corpus.load_run_meta: a missing input
    file is a setup mistake, not something to paper over with an empty
    export.
    """
    path = os.path.join(run_dir, MATCHES_FILENAME)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No {MATCHES_FILENAME} in {run_dir}. Run "
            "`python -m reviewlens.eval --run ... --report ... --judge-model ...` "
            "first to produce it."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _match_row(slug: str, run_dir: str, repo: str, number: int, index: int, entry: dict) -> dict:
    human = entry["human"]
    model = entry["model"]
    return {
        "judgment_id": _judgment_id(slug, repo, number, MATCH_KIND, index),
        "run": run_dir,
        "kind": MATCH_KIND,
        "repo": repo,
        "pr_number": number,
        "pr_url": _pr_url(repo, number),
        "file": human.get("file", ""),
        "human_line": human.get("line", ""),
        "human_comment": human.get("comment", ""),
        "human_url": human.get("url") or "",
        "model_line": model.get("line", ""),
        "model_category": model.get("category", ""),
        "model_severity": model.get("severity", ""),
        "model_comment": model.get("comment", ""),
        "pipeline_verdict": "matched",
        "judge_reason": entry.get("reason", ""),
        "human_verdict": "",
        "human_notes": "",
    }


def _unmatched_model_row(slug: str, run_dir: str, repo: str, number: int, index: int, model: dict) -> dict:
    return {
        "judgment_id": _judgment_id(slug, repo, number, UNMATCHED_MODEL_KIND, index),
        "run": run_dir,
        "kind": UNMATCHED_MODEL_KIND,
        "repo": repo,
        "pr_number": number,
        "pr_url": _pr_url(repo, number),
        "file": model.get("file", ""),
        "human_line": "",
        "human_comment": "",
        "human_url": "",
        "model_line": model.get("line", ""),
        "model_category": model.get("category", ""),
        "model_severity": model.get("severity", ""),
        "model_comment": model.get("comment", ""),
        "pipeline_verdict": "unmatched",
        "judge_reason": "",
        "human_verdict": "",
        "human_notes": "",
    }


def collect_populations(
    records: list[dict], slug: str, run_dir: str
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Flatten eval_matches.json into the two judgment populations, keyed by
    judgment_id. A dict (not a list) so sampling can pick ids first and look
    up rows second, keeping the sampling step free of row formatting."""
    matches: dict[str, dict] = {}
    unmatched_model: dict[str, dict] = {}
    for pr in records:
        repo = pr["repo"]
        number = pr["number"]
        for i, entry in enumerate(pr.get("matches", [])):
            row = _match_row(slug, run_dir, repo, number, i, entry)
            matches[row["judgment_id"]] = row
        for i, model in enumerate(pr.get("unmatched_model", [])):
            row = _unmatched_model_row(slug, run_dir, repo, number, i, model)
            unmatched_model[row["judgment_id"]] = row
    return matches, unmatched_model


def sample_ids(ids: list[str], rate: float, seed: int) -> list[str]:
    """Draw a reproducible sample of judgment ids from one population.

    Sorts first so the draw depends only on (ids, rate, seed) and never on
    whatever order eval_matches.json happened to list PRs in. Size is
    math.ceil(len(ids) * rate), never round, so "at least rate" is a real
    guarantee rather than something a population size like 11 at 0.20 could
    round away (ceil gives 3, round would give 2). A non-empty population
    always yields at least 1.
    """
    population = sorted(ids)
    if not population:
        return []
    sample_size = min(len(population), max(1, math.ceil(len(population) * rate)))
    return random.Random(seed).sample(population, sample_size)


def _write_csv(out_path: str, rows: list[dict]) -> None:
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _report(name: str, total: int, sampled: int) -> str:
    if total == 0:
        return f"{name}: 0/0 sampled (population empty)"
    pct = 100.0 * sampled / total
    return f"{name}: {sampled}/{total} sampled ({pct:.1f}%)"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval.export_verification",
        description=(
            "Export a reproducible sample of matches and unmatched-model comments "
            "from an eval run for manual verification."
        ),
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Run directory containing eval_matches.json (produced by reviewlens.eval).",
    )
    parser.add_argument("--out", required=True, help="Output CSV path.")
    parser.add_argument(
        "--sample-rate",
        type=float,
        default=0.20,
        help="Fraction of each population to sample (default 0.20).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260823,
        help="Random seed; same seed + same eval_matches.json reproduces the same sample.",
    )
    args = parser.parse_args(argv)

    try:
        records = load_eval_matches(args.run)
    except FileNotFoundError as exc:
        sys.exit(str(exc))

    run_meta_path = os.path.join(args.run, "run_meta.json")
    try:
        with open(run_meta_path, encoding="utf-8") as f:
            model = json.load(f)["model"]
    except (FileNotFoundError, KeyError) as exc:
        sys.exit(f"{run_meta_path}: cannot read the run's model, needed to build judgment ids ({exc})")

    matches, unmatched_model = collect_populations(records, run_slug(model), args.run)

    sampled_match_ids = sample_ids(list(matches), args.sample_rate, args.seed)
    sampled_unmatched_ids = sample_ids(list(unmatched_model), args.sample_rate, args.seed)

    rows = sorted(
        (matches[i] for i in sampled_match_ids),
        key=lambda r: r["judgment_id"],
    ) + sorted(
        (unmatched_model[i] for i in sampled_unmatched_ids),
        key=lambda r: r["judgment_id"],
    )

    _write_csv(args.out, rows)

    print(_report(MATCH_KIND, len(matches), len(sampled_match_ids)))
    print(_report(UNMATCHED_MODEL_KIND, len(unmatched_model), len(sampled_unmatched_ids)))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
