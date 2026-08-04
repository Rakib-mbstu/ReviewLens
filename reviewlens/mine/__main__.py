"""CLI entry point: `python -m reviewlens.mine --projects … --out …`.

Thin argument-wiring only — qualification predicates live in select.py,
GitHub paging/orchestration and corpus writing in miner.py. Mirrors
reviewlens.review.__main__'s conventions (CLAUDE.md: keep pipeline
invocations and their flags stable).
"""

from __future__ import annotations

import argparse
import os

from reviewlens.mine.miner import PROJECT_REGISTRY, mine, write_corpus
from reviewlens.review.ingest import GitHubClient


def _corpus_size_mb(out_dir: str) -> float:
    """Total on-disk size of the corpus directory, in MB — the owner uses
    this to decide whether data/corpus/ (gitignored) is small enough to
    commit anyway for a given run."""
    total_bytes = sum(
        os.path.getsize(os.path.join(out_dir, name))
        for name in os.listdir(out_dir)
        if os.path.isfile(os.path.join(out_dir, name))
    )
    return total_bytes / (1024 * 1024)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.mine",
        description="Mine merged Java PRs and their human review comments into a corpus.",
    )
    parser.add_argument(
        "--projects",
        nargs="+",
        required=True,
        choices=sorted(PROJECT_REGISTRY),
        help="Projects to mine (e.g. junit5 mockito checkstyle).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for the mined corpus (e.g. data/corpus/).",
    )
    parser.add_argument(
        "--per-project",
        type=int,
        default=30,
        help="Max qualifying PRs to select per project (default: 30).",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=100,
        help="Max qualifying PRs across all projects combined (default: 100).",
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=400,
        help="Max PRs examined per project, bounding API cost (default: 400).",
    )
    args = parser.parse_args(argv)

    client = GitHubClient()
    try:
        pr_records, manifest = mine(
            client,
            args.projects,
            per_project=args.per_project,
            max_total=args.max_total,
            scan_limit=args.scan_limit,
        )
    finally:
        client.close()

    write_corpus(args.out, pr_records, manifest)

    for entry in manifest["projects"]:
        limit_note = " (hit scan limit)" if entry["hit_scan_limit"] else ""
        print(
            f"{entry['slug']} ({entry['repo']}): scanned {entry['scanned']}, "
            f"selected {entry['selected']}{limit_note}"
        )
    size_mb = _corpus_size_mb(args.out)
    print(
        f"Total: {len(pr_records)} PRs mined across {len(args.projects)} projects, "
        f"{size_mb:.2f} MB on disk in {args.out}."
    )


if __name__ == "__main__":
    main()
