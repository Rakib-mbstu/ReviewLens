"""Join a blind match sheet to its key and emit verification CSVs.

A match sheet is deliberately blind: it is keyed by sheet id and names no
model, so the rater cannot lean on a prior about which arm produced a match.
That makes it unreadable by anything downstream. This script performs the join
that was previously done by hand, and writes it in the schema
`reviewlens.eval.export_verification` produces, so
`python -m reviewlens.eval.compare --verified ...` can consume it directly.

For the subset30 census two files come out, because two different numbers are
defensible and the study reports both:

  * `-blind.csv`  — verdicts as first recorded, arms hidden. 5/8 upheld.
  * `.csv`        — verdicts after the arms were disclosed and two were
                    revised. 7/8 upheld.

The blind pass has the stronger provenance and the final pass is the rater's
considered judgment. Emitting both means neither figure can be quoted without
the other existing beside it, and both are reproducible by command rather
than only asserted in prose.

A census with no separate blind record — one pass, never revised — passes
`--blind none` and gets a single CSV. That is the stronger provenance of the
two, and it is worth keeping it that way: the subset30 sheet only needs two
files because its verdicts were revised after unblinding.

Invoked with no arguments it reproduces the published subset30 join. The
full-corpus qwen census is:

    python work/match/join_verdicts.py \\
        --key work/match/match_full87_key.json \\
        --sheet reports/match-verification-full87.csv \\
        --out reports/match-verification-full87-joined.csv --blind none
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from reviewlens.eval.export_verification import MATCH_KIND

DEFAULT_RUN_DIRS = {
    "qwen": "runs/subset30/qwen3-coder-30b-a3b-instruct/",
    "opus": "runs/subset30/claude-opus/",
    "sonnet": "runs/subset30/claude-sonnet-5/",
}
FIELDNAMES = [
    "judgment_id", "run", "kind", "sheet_id", "arm", "repo", "pr_number",
    "file", "human_line", "model_line", "pipeline_verdict", "judge_verdict",
    "human_verdict", "human_notes",
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--key", default="work/match/match_sheet_key.json",
                    help="the sheet's unblinding map, written by build_match_sheet.py")
    ap.add_argument("--sheet", default="reports/match-verification.csv",
                    help="the rated sheet CSV")
    ap.add_argument("--out", default="reports/match-verification-joined.csv",
                    help="where the joined verification CSV is written")
    ap.add_argument("--blind", default="work/match/match_blind_pass.json",
                    help="record of the verdicts as first taken, for the second "
                         "'-blind' CSV; pass 'none' when the pass was never revised")
    ap.add_argument("--run-dir", action="append", default=[], metavar="ARM=PATH",
                    help="map an arm label to its run directory (repeatable); "
                         "defaults cover the three subset30 arms")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    run_dirs = dict(DEFAULT_RUN_DIRS)
    for pair in args.run_dir:
        if "=" not in pair:
            sys.exit("--run-dir expects ARM=PATH, got %r" % pair)
        label, path = pair.split("=", 1)
        run_dirs[label] = path

    key = {r["sheet_id"]: r for r in json.load(open(args.key, encoding="utf-8"))["picked"]}
    with open(args.sheet, newline="", encoding="utf-8") as f:
        sheet = list(csv.DictReader(f))

    missing = [r["sheet_id"] for r in sheet if not r["verdict_comments_only"].strip()]
    if missing:
        sys.exit("Unrated sheet ids: %s. Fill the sheet before joining."
                 % ", ".join(missing))
    # A key written by a current build_match_sheet.py names each match's run
    # directly. Older keys (the published subset30 one) only carry an arm
    # label, so fall back to the map for those.
    unmapped = sorted({key[r["sheet_id"]]["arm"] for r in sheet
                       if not key[r["sheet_id"]].get("run_dir")} - set(run_dirs))
    if unmapped:
        sys.exit("No run directory for arm(s): %s. Pass --run-dir ARM=PATH."
                 % ", ".join(unmapped))

    passes = [(args.out, "final")]
    blind = None
    if args.blind != "none":
        blind = json.load(open(args.blind, encoding="utf-8"))["verdicts"]
        if set(blind) != set(key):
            sys.exit("The blind record and the key cover different sheet ids.")
        stem, ext = os.path.splitext(args.out)
        passes.append((stem + "-blind" + ext, "blind"))

    for out_path, source in passes:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in sheet:
                sid = row["sheet_id"]
                k = key[sid]
                verdict = (
                    row["verdict_comments_only"].strip() if source == "final" else blind[sid]
                )
                writer.writerow({
                    "judgment_id": k["judgment_id"],
                    "run": k.get("run_dir") or run_dirs[k["arm"]],
                    "kind": MATCH_KIND,
                    "sheet_id": sid,
                    "arm": k["arm"],
                    "repo": k["repo"],
                    "pr_number": k["number"],
                    "file": row["file"],
                    "human_line": row["human_line"],
                    "model_line": row["model_line"],
                    "pipeline_verdict": "matched",
                    "judge_verdict": k["judge_verdict"],
                    "human_verdict": verdict,
                    "human_notes": row.get("notes", ""),
                })
        upheld = sum(
            1 for row in sheet
            if (row["verdict_comments_only"].strip() if source == "final" else blind[row["sheet_id"]])
            == "equivalent"
        )
        print("%s: %d/%d upheld (%s pass)" % (out_path, upheld, len(sheet), source))


if __name__ == "__main__":
    main()
