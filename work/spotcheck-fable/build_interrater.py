"""Join the two category raters into the inter-rater artifacts.

Kept in work/ rather than reviewlens/eval/ deliberately: this is a one-off
join over two existing outputs, not a pipeline stage, and the package is
under feature freeze. Inputs are the frozen-rubric outputs of both raters;
it computes nothing that is not derivable from them.
"""
import csv, json, collections

R1 = json.load(open("data/corpus/categories.json"))
R2 = json.load(open("work/spotcheck-fable/categories-fable.json"))
c1, c2 = R1["categories"], R2["categories"]
src = {r["comment_id"]: r for r in csv.DictReader(open("reports/categorization-spotcheck.csv"))}
hum = {r["comment_id"]: r for r in csv.DictReader(open("work/spotcheck-fable/partial-human-pass.csv", encoding="utf-8-sig"))}
ids = sorted(c2, key=lambda x: int(x))

FIELDS = ["comment_id", "repo", "pr_number", "comment_url", "file", "line", "comment",
          "rater1_category", "rater1_confidence", "rater2_category", "rater2_confidence",
          "rater2_reason", "raters_agree", "partial_human_label", "partial_human_agrees"]
with open("reports/categorization-interrater.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
    for i in ids:
        s = src.get(i, {})
        w.writerow({
            "comment_id": i, "repo": s.get("repo",""), "pr_number": s.get("pr_number",""),
            "comment_url": s.get("comment_url",""), "file": s.get("file",""), "line": s.get("line",""),
            "comment": s.get("comment",""),
            "rater1_category": c1[i]["category"], "rater1_confidence": c1[i]["confidence"],
            "rater2_category": c2[i]["category"], "rater2_confidence": c2[i]["confidence"],
            "rater2_reason": c2[i].get("reason",""),
            "raters_agree": "yes" if c1[i]["category"] == c2[i]["category"] else "no",
            # Preserved verbatim from an abandoned partial human pass (9 of 66).
            # Recorded, never scored: it used a vocabulary outside the frozen four.
            "partial_human_label": (hum.get(i, {}).get("human_category") or "").strip(),
            "partial_human_agrees": (hum.get(i, {}).get("human_agrees") or "").strip(),
        })

agree = [i for i in ids if c1[i]["category"] == c2[i]["category"]]
print(f"wrote reports/categorization-interrater.csv — {len(agree)}/{len(ids)} agree")
