"""Load a run directory and its corpus into the shape `matching` expects.

This module exists because the two halves of the study speak different
dialects: `reviewlens.mine` writes human comments as `{path, line, body}`
(GitHub's own field names), while `reviewlens.eval.matching` reads
`{file, line, comment}`. Left unreconciled the mismatch is silent — every
`is_candidate` lookup would raise or, worse, compare nothing and produce a
0% recall that looks like a finding instead of a bug. Normalizing in exactly
one place, here, is what keeps that from happening.

Pairing is per PR: a model comment can only match a human comment on the
same pull request, so the join is (repo, number) and a PR present in one
side but not the other is reported rather than quietly dropped.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field

from reviewlens.mine.miner import MANIFEST_FILENAME

RUN_META_FILENAME = "run_meta.json"
# Written by reviewlens.eval.categorize, keyed by human comment id. Not a PR
# record, so load_corpus must skip it exactly like the mining manifest.
CATEGORIES_FILENAME = "categories.json"


@dataclass
class EvalPR:
    """One PR's human and model comments, ready for `match_comments`."""

    repo: str
    number: int
    human_comments: list[dict]
    model_comments: list[dict]
    parse_error_count: int = 0
    chunk_count: int = 0


@dataclass
class CategorizationMeta:
    """Provenance and coverage stats for `categories.json` (T8).

    The per-comment category verdicts already flow through
    `EvalPR.human_comments` via `normalize_human_comment`; this dataclass
    carries what the report needs to state additionally: *how* those
    verdicts were produced (which model, which rubric version) and *how
    completely* (how many comments, failures, low-confidence calls), so the
    report can document the method instead of leaving a reader to guess
    whether categories were hand-labeled or LLM-assigned.
    """

    model: str
    prompt_name: str
    prompt_version: int
    prompt_sha256: str
    categorized_count: int
    low_confidence_count: int
    failure_count: int


@dataclass
class EvalInputs:
    """Everything the metrics and report stages need from disk."""

    run_meta: dict
    prs: list[EvalPR]
    corpus_dir: str
    # PRs the run reviewed that the corpus does not contain, and vice versa.
    # Never silently ignored: either direction means the run and the corpus
    # disagree about what was evaluated, which invalidates the denominator.
    missing_from_corpus: list[str] = field(default_factory=list)
    missing_from_run: list[str] = field(default_factory=list)
    # None when the corpus has no categories.json — categorization is a
    # separate stage (T8) that may not have run, and that absence must stay
    # visible rather than being papered over with a fabricated stub.
    categorization: CategorizationMeta | None = None


def normalize_human_comment(raw: dict, categories: dict | None = None) -> dict:
    """Rewrite a mined human comment into matching's `{file, line, comment}`.

    Identity fields (`id`, `url`, `author`) are carried through unchanged so
    the manual-verification export can link a judgment back to the comment
    a human actually wrote on GitHub. `category` is added only when
    `categories` (keyed by comment id as a string, as `categorize.py` writes
    it) has an entry for this comment — absence must stay absence, not a
    fabricated category, so metrics.compute_metrics can tell "not yet
    categorized" apart from every real category.
    """
    normalized = {
        "file": raw["path"],
        "line": raw["line"],
        "comment": raw["body"],
        "id": raw.get("id"),
        "url": raw.get("url"),
        "author": raw.get("author"),
    }
    if categories:
        entry = categories.get(str(raw.get("id")))
        if entry is not None:
            normalized["category"] = entry["category"]
    return normalized


def pr_key(repo: str, number: int) -> str:
    """Stable identifier used for joining, directory names, and reporting."""
    owner, _, name = repo.partition("/")
    return f"{owner}__{name}__{number}"


def load_corpus(corpus_dir: str) -> dict[str, dict]:
    """Load mined PRs keyed by `pr_key`, skipping the mining manifest.

    Raises FileNotFoundError with an actionable message rather than
    returning an empty corpus, because an empty denominator would render
    recall as a division by zero at best and a fabricated 0% at worst.
    """
    if not os.path.isdir(corpus_dir):
        raise FileNotFoundError(
            f"Corpus directory not found: {corpus_dir}. "
            "Run `python -m reviewlens.mine` first, or pass --corpus."
        )
    records: dict[str, dict] = {}
    for path in sorted(glob.glob(os.path.join(corpus_dir, "*.json"))):
        if os.path.basename(path) in (MANIFEST_FILENAME, CATEGORIES_FILENAME):
            continue
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        records[pr_key(record["repo"], record["number"])] = record
    if not records:
        raise FileNotFoundError(f"Corpus directory holds no PR files: {corpus_dir}")
    return records


def _read_categories_file(corpus_dir: str) -> dict | None:
    """Read `categories.json` raw, or None if the corpus has not been
    categorized. Shared by `load_categories` and `load_categorization_meta`
    so both agree on what "missing" means."""
    path = os.path.join(corpus_dir, CATEGORIES_FILENAME)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_categories(corpus_dir: str) -> dict:
    """Read `categories.json` from a corpus directory, keyed by comment id.

    Its absence is not an error: categorization is a separate stage (T8) that
    may not have run yet, and per-category recall simply stays unavailable
    (metrics.compute_metrics's existing behavior) rather than this module
    treating a missing file as a setup mistake.
    """
    raw = _read_categories_file(corpus_dir)
    return {} if raw is None else raw["categories"]


def load_categorization_meta(corpus_dir: str) -> CategorizationMeta | None:
    """Read `categories.json`'s provenance and coverage stats, or None.

    `load_categories` throws away everything but the id -> verdict map,
    which is enough to annotate model comments but not enough for the
    report to say *how* those verdicts were produced. This reads the same
    file and derives the counts the report needs (categorized / failed /
    low-confidence) from the data itself, so nothing here is hardcoded.
    Mirrors `load_categories`'s "missing file is not an error" behavior.
    """
    raw = _read_categories_file(corpus_dir)
    if raw is None:
        return None
    prompt = raw.get("prompt", {})
    categories = raw.get("categories", {})
    low_confidence_count = sum(
        1 for entry in categories.values() if entry.get("confidence") == "low"
    )
    return CategorizationMeta(
        model=raw.get("model", "?"),
        prompt_name=prompt.get("name", "?"),
        prompt_version=prompt.get("version", "?"),
        prompt_sha256=prompt.get("sha256", "?"),
        categorized_count=len(categories),
        low_confidence_count=low_confidence_count,
        failure_count=len(raw.get("failures", [])),
    )


def load_run_meta(run_dir: str) -> dict:
    """Read a run's metadata, failing loudly if the run never wrote it.

    A run directory without run_meta.json cannot be evaluated: the prompt
    version, model ID, and PR list that make a report reproducible all live
    there. Runs aborted before this file existed have to be re-run.
    """
    path = os.path.join(run_dir, RUN_META_FILENAME)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No {RUN_META_FILENAME} in {run_dir}. A report must be reproducible from "
            "the run directory alone, so this run cannot be evaluated — re-run "
            "`python -m reviewlens.review` to produce it."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_model_comments(run_dir: str, key: str) -> list[dict]:
    """Read one PR's model comments from a run directory.

    A missing comments.json means the run did not finish that PR, which is
    different from the model having found nothing; the caller distinguishes
    the two via run_meta's pr_summaries.
    """
    path = os.path.join(run_dir, key, "comments.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_eval_inputs(run_dir: str, corpus_dir: str | None = None) -> EvalInputs:
    """Assemble a run plus its corpus into per-PR comment pairs.

    The corpus directory is read from run_meta by default so the documented
    `--run`/`--report` CLI needs no third argument, and so a report is tied
    to the corpus the run actually used rather than whatever is on disk now.
    """
    run_meta = load_run_meta(run_dir)
    resolved_corpus = corpus_dir or run_meta.get("corpus")
    if not resolved_corpus:
        raise FileNotFoundError(
            f"{RUN_META_FILENAME} in {run_dir} does not record which corpus the run used, "
            "and no --corpus was given."
        )

    corpus = load_corpus(resolved_corpus)
    categories = load_categories(resolved_corpus)
    categorization = load_categorization_meta(resolved_corpus)
    prs: list[EvalPR] = []
    missing_from_corpus: list[str] = []
    reviewed_keys = set()

    for summary in run_meta.get("pr_summaries", []):
        key = pr_key(summary["repo"], summary["number"])
        reviewed_keys.add(key)
        record = corpus.get(key)
        if record is None:
            missing_from_corpus.append(key)
            continue
        prs.append(
            EvalPR(
                repo=summary["repo"],
                number=summary["number"],
                human_comments=[
                    normalize_human_comment(c, categories)
                    for c in record.get("human_comments", [])
                ],
                model_comments=load_model_comments(run_dir, key),
                parse_error_count=summary.get("parse_error_count", 0),
                chunk_count=summary.get("chunk_count", 0),
            )
        )

    return EvalInputs(
        run_meta=run_meta,
        prs=prs,
        corpus_dir=resolved_corpus,
        missing_from_corpus=missing_from_corpus,
        missing_from_run=sorted(set(corpus) - reviewed_keys),
        categorization=categorization,
    )
