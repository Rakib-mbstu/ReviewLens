from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.mine",
        description="Mine merged Java PRs and their human review comments into a corpus.",
    )
    parser.add_argument(
        "--projects",
        nargs="+",
        required=True,
        help="Projects to mine (e.g. junit5 mockito checkstyle).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for the mined corpus (e.g. data/corpus/).",
    )
    parser.parse_args(argv)
    sys.exit(
        "reviewlens.mine is not implemented yet — "
        "tracked in https://github.com/Rakib-mbstu/ReviewLens/issues/7"
    )


if __name__ == "__main__":
    main()
