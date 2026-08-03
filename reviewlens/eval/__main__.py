from __future__ import annotations

import argparse
import sys


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
    parser.parse_args(argv)
    sys.exit(
        "reviewlens.eval is not implemented yet — "
        "tracked in https://github.com/Rakib-mbstu/ReviewLens/issues/9"
    )


if __name__ == "__main__":
    main()
