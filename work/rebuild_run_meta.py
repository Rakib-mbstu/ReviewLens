"""Rebuild the `pr_summaries` a truncated rerun dropped from run_meta.json.

Why this exists: `reviewlens.review` rewrites run_meta.json from zero on a
rerun instead of resuming, so an interrupted rerun leaves the file describing
fewer PRs than the directory actually contains. The full-corpus qwen run was
left describing 32 PRs while holding output for 87, which made its published
recall figure unreproducible from its own run directory.

Every field written here is DERIVED from artifacts already on disk, never
invented:
  chunk_count       <- number of raw/chunk_*.json files
  comment_count     <- len(comments.json)
  parse_error_count <- len(errors.json), absent file meaning zero
  providers         <- tally of response.provider across the raw responses
  repo / number     <- the corpus record for that directory

What is NOT touched: `started`, `finished`, and `complete`. The run genuinely
was interrupted (it died creating an empty directory for the next PR), so
`complete` stays false and `finished` stays null. This script restores lost
bookkeeping; it does not upgrade a partial run into a finished one.

Directories with zero chunks are skipped: they are where the run stopped, not
PRs that were reviewed.
"""
import glob, json, os, shutil
from datetime import datetime, timezone

RUN = "runs/qwen/qwen3-coder-30b-a3b-instruct"
META = os.path.join(RUN, "run_meta.json")

corpus = {}
for p in glob.glob("data/corpus/*.json"):
    if os.path.basename(p) in ("categories.json", "manifest.json"):
        continue
    d = json.load(open(p))
    corpus[os.path.basename(p)[:-5]] = (d["repo"], d["number"])

meta = json.load(open(META))
backup = META + ".pre-reconstruction"
if not os.path.exists(backup):
    shutil.copy2(META, backup)

summaries, skipped = [], []
for d in sorted(glob.glob(RUN + "/*")):
    if not os.path.isdir(d):
        continue
    key = os.path.basename(d)
    raws = glob.glob(os.path.join(d, "raw", "chunk_*.json"))
    if not raws:
        skipped.append(key)
        continue
    comments = json.load(open(os.path.join(d, "comments.json")))
    ep = os.path.join(d, "errors.json")
    errors = json.load(open(ep)) if os.path.exists(ep) else []
    providers = {}
    for rp in raws:
        prov = (json.load(open(rp)).get("response") or {}).get("provider")
        if prov is not None:
            providers[prov] = providers.get(prov, 0) + 1
    repo, number = corpus[key]
    summaries.append({
        "repo": repo, "number": number,
        "chunk_count": len(raws),
        "comment_count": len(comments),
        "parse_error_count": len(errors),
        "providers": providers,
    })

meta["pr_summaries"] = sorted(summaries, key=lambda s: (s["repo"], s["number"]))
meta["reconstructed"] = {
    "at": datetime.now(timezone.utc).isoformat(),
    "by": "work/rebuild_run_meta.py",
    "reason": "an interrupted rerun truncated pr_summaries to 32 of the 87 PRs on disk",
    "derived_from": ["raw/chunk_*.json", "comments.json", "errors.json", "data/corpus/"],
    "fields_rebuilt": ["pr_summaries"],
    "fields_left_untouched": ["started", "finished", "complete", "exclusions"],
    "skipped_empty_dirs": skipped,
    "original_backed_up_to": os.path.basename(backup),
}
json.dump(meta, open(META, "w"), indent=2)
print(f"rebuilt {len(summaries)} pr_summaries "
      f"({sum(s['chunk_count'] for s in summaries)} chunks, "
      f"{sum(s['parse_error_count'] for s in summaries)} parse-error items)")
print("skipped empty dirs:", skipped)
print("complete stays:", meta["complete"], "| finished stays:", meta["finished"])
