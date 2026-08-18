"""CLI entry point: `python -m reviewlens.review --corpus … --model … --out …`.

Thin argument-wiring only — chunking/review logic lives in engine.py, PR
fetch logic in ingest.py, prompt loading in prompt.py. This module's job is
to read the corpus, drive one review_pr() call per PR, and assemble
run_meta.json so a run directory is reproducible on its own (CLAUDE.md).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

from reviewlens.mine.miner import MANIFEST_FILENAME
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.engine import DEFAULT_CONTEXT_LINES, review_pr
from reviewlens.review.ingest import GitHubClient, PRExcluded, fetch_pr_snapshot
from reviewlens.review.prompt import load_prompt

_PROMPT_RELATIVE_PATH = os.path.join("prompts", "review_v1.md")


def _repo_root() -> str:
    """The repo root, derived from this file's location (never cwd), so the
    prompt path resolves the same way regardless of where the CLI is invoked
    from."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_corpus_entries(corpus_dir: str) -> list[dict]:
    """Load every corpus PR entry, failing loudly on anything malformed.

    The mine -> review contract is thin for now: one JSON file per PR with
    at least {"repo": "owner/name", "number": <int>}; unknown keys are
    ignored. A missing/empty corpus dir or an invalid entry file is a setup
    error, not a per-PR condition — it stops the run immediately with an
    actionable message, unlike PRExcluded (a specific PR that is unusable at
    review time and is skipped rather than fatal).

    The mining manifest is the one file in a corpus directory that is not a
    PR entry, so it is skipped by name. Anything else lacking repo/number is
    still fatal — a corpus with a malformed PR file must not quietly review
    fewer PRs than the corpus claims to hold.
    """
    if not os.path.isdir(corpus_dir):
        sys.exit(
            f"Corpus directory not found: {corpus_dir}. "
            "Run `python -m reviewlens.mine` first to produce a corpus."
        )
    paths = [
        path
        for path in sorted(glob.glob(os.path.join(corpus_dir, "*.json")))
        if os.path.basename(path) != MANIFEST_FILENAME
    ]
    if not paths:
        sys.exit(
            f"Corpus directory {corpus_dir} contains no PR JSON files. "
            "Run `python -m reviewlens.mine` first to produce a corpus."
        )

    entries = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            sys.exit(f"Corpus file {path} is not valid JSON: {exc}")
        if not isinstance(data, dict) or "repo" not in data or "number" not in data:
            sys.exit(f"Corpus file {path} is missing required keys 'repo'/'number'.")
        entries.append(data)
    return entries


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.review",
        description="Run the LLM reviewer on the pre-review state of each corpus PR.",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        help="Corpus directory produced by reviewlens.mine (e.g. data/corpus/).",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="OpenRouter model ID to review with.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Run output directory (e.g. runs/<model-id>/).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the LLM response cache and force fresh API calls.",
    )
    args = parser.parse_args(argv)

    entries = _load_corpus_entries(args.corpus)
    prompt = load_prompt(os.path.join(_repo_root(), _PROMPT_RELATIVE_PATH))
    os.makedirs(args.out, exist_ok=True)

    github_client = GitHubClient()
    llm_client = OpenRouterClient(use_cache=not args.no_cache)

    pr_summaries: list[dict] = []
    exclusions: list[dict] = []
    started = datetime.now(timezone.utc).isoformat()

    def write_run_meta(finished: str | None) -> None:
        """Persist run metadata for the PRs completed so far.

        Called after every PR rather than once at the end: the first corpus
        run died partway through and left a run directory with outputs but no
        metadata at all, which CLAUDE.md's "reproducible from the run
        directory alone" rule does not survive. `finished` is None while the
        run is still in progress, so a partial run is self-describing instead
        of merely looking like a complete one that reviewed fewer PRs.
        """
        run_meta = {
            "model": args.model,
            "prompt": {
                "name": prompt.name,
                "version": prompt.version,
                "sha256": prompt.sha256,
                "params": prompt.params,
            },
            "context_lines": DEFAULT_CONTEXT_LINES,
            # Recorded so `reviewlens.eval` can tie a report to the corpus the
            # run actually used, rather than whatever happens to be on disk
            # when the report is generated.
            "corpus": args.corpus,
            "corpus_pr_count": len(entries),
            "started": started,
            "finished": finished,
            "complete": finished is not None,
            "pr_summaries": pr_summaries,
            "exclusions": exclusions,
        }
        path = os.path.join(args.out, "run_meta.json")
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(run_meta, f, indent=2, ensure_ascii=True)
        os.replace(tmp_path, path)

    write_run_meta(None)
    try:
        for entry in entries:
            repo = entry["repo"]
            number = entry["number"]
            owner, name = repo.split("/", 1)
            try:
                snapshot = fetch_pr_snapshot(github_client, owner, name, number)
            except PRExcluded as exc:
                exclusions.append({"repo": repo, "number": number, "reason": exc.reason})
                write_run_meta(None)
                print(f"{repo}#{number}: excluded ({exc.reason})")
                continue

            summary = review_pr(
                snapshot,
                github_client,
                llm_client,
                args.model,
                prompt,
                args.out,
                context_lines=DEFAULT_CONTEXT_LINES,
            )
            pr_summaries.append(summary)
            write_run_meta(None)
            print(
                f"{repo}#{number}: {summary['chunk_count']} chunks, "
                f"{summary['comment_count']} comments, "
                f"{summary['parse_error_count']} parse errors"
            )
    finally:
        github_client.close()
        llm_client.close()

    write_run_meta(datetime.now(timezone.utc).isoformat())

    total_comments = sum(s["comment_count"] for s in pr_summaries)
    total_errors = sum(s["parse_error_count"] for s in pr_summaries)
    print(
        f"Total: {len(pr_summaries)} PRs reviewed, {len(exclusions)} excluded, "
        f"{total_comments} comments, {total_errors} parse errors."
    )


if __name__ == "__main__":
    main()
