"""Join the blind match sheet to its key and emit verification CSVs.

`reports/match-verification.csv` is deliberately blind: it is keyed by sheet
id and names no model, so the rater cannot lean on a prior about which arm
produced a match. That makes it unreadable by anything downstream. This
script performs the join that was previously done by hand, and writes it in
the schema `reviewlens.eval.export_verification` produces, so
`python -m reviewlens.eval.compare --verified ...` can consume it directly.

Two files come out, because two different numbers are defensible and the
study reports both:

  * `-blind.csv`  — verdicts as first recorded, arms hidden. 5/8 upheld.
  * `.csv`        — verdicts after the arms were disclosed and two were
                    revised. 7/8 upheld.

The blind pass has the stronger provenance and the final pass is the rater's
considered judgment. Emitting both means neither figure can be quoted without
the other existing beside it, and both are reproducible by command rather
than only asserted in prose.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from reviewlens.eval.export_verification import MATCH_KIND

KEY = "work/match/match_sheet_key.json"
BLIND = "work/match/match_blind_pass.json"
SHEET_CSV = "reports/match-verification.csv"
OUT_FINAL = "reports/match-verification-joined.csv"
OUT_BLIND = "reports/match-verification-joined-blind.csv"

# The sheet is blind to the arm, so the run directory is recovered from the key.
RUN_DIRS = {
    "qwen": "runs/subset30/qwen3-coder-30b-a3b-instruct/",
    "opus": "runs/subset30/claude-opus/",
    "sonnet": "runs/subset30/claude-sonnet-5/",
}
FIELDNAMES = [
    "judgment_id", "run", "kind", "sheet_id", "arm", "repo", "pr_number",
    "file", "human_line", "model_line", "pipeline_verdict", "judge_verdict",
    "human_verdict", "human_notes",
]


def main() -> None:
    key = {r["sheet_id"]: r for r in json.load(open(KEY, encoding="utf-8"))["picked"]}
    blind = json.load(open(BLIND, encoding="utf-8"))["verdicts"]
    with open(SHEET_CSV, newline="", encoding="utf-8") as f:
        sheet = list(csv.DictReader(f))

    missing = [r["sheet_id"] for r in sheet if not r["verdict_comments_only"].strip()]
    if missing:
        sys.exit(f"Unrated sheet ids: {', '.join(missing)}. Fill the sheet before joining.")
    if set(blind) != set(key):
        sys.exit("The blind record and the key cover different sheet ids.")

    for out_path, source in ((OUT_FINAL, "final"), (OUT_BLIND, "blind")):
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
                    "run": RUN_DIRS[k["arm"]],
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
        print(f"{out_path}: {upheld}/{len(sheet)} upheld ({source} pass)")


if __name__ == "__main__":
    main()
