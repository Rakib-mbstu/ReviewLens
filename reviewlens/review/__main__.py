from __future__ import annotations

import argparse
import sys


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
    parser.parse_args(argv)
    sys.exit(
        "reviewlens.review is not implemented yet — "
        "tracked in https://github.com/Rakib-mbstu/ReviewLens/issues/5"
    )


if __name__ == "__main__":
    main()
