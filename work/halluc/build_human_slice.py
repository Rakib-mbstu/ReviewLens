"""Draw the stratified slice a human verifies, and render it BLIND.

The screen was run by a Claude model over three arms, two of which are Claude
models that scored far better. That is exactly the pattern self-evaluation
bias would produce, and it is also exactly what a real capability gap would
produce; the screen alone cannot separate them. So the slice is not drawn
uniformly — it is weighted toward the two verdicts where a biased judge would
do the most damage:

  * Claude-arm `founded`  — a biased judge excuses a weak Claude comment here,
    suppressing those arms' hallucination rate.
  * qwen `unfounded`      — a biased judge condemns a fine qwen comment here,
    inflating that arm's rate.

The sheet is rendered WITHOUT the model's verdict. A human shown the machine's
answer first tends to ratify it, which would turn the agreement rate into a
measure of anchoring rather than of accuracy. Verdicts are joined afterwards
from the verdicts JSON, keyed by judgment_id.
"""
import csv, json, os, random, sys, textwrap
# run from the repo root: sys.path[0] is this script's dir, not the cwd
sys.path.insert(0, os.getcwd())
from reviewlens.eval.hallucination import recover_chunk
from reviewlens.eval.export_verification import _judgment_id, run_slug
from reviewlens.review.prompt import load_prompt

SEED = 20260826
ARMS = {"qwen3-coder-30b-a3b-instruct": "qwen", "claude-opus": "opus", "claude-sonnet-5": "sonnet"}
RUNDIR = {"qwen": "runs/subset30/qwen3-coder-30b-a3b-instruct", "opus": "runs/subset30/claude-opus",
          "sonnet": "runs/subset30/claude-sonnet-5"}
REVIEW_PROMPT = load_prompt("prompts/review_v1.md")
CHUNK_IDX = {}
for _arm, _short in ARMS.items():
    # derive ids through the real function so this can never drift from the
    # ids that actually appear in an exported sample CSV
    _slug = run_slug(json.load(open(f"runs/subset30/{_arm}/run_meta.json"))["model"])
    for _pr in json.load(open(f"runs/subset30/{_arm}/eval_matches.json")):
        for _i, _c in enumerate(_pr.get("unmatched_model", [])):
            _k = _judgment_id(_slug, _pr["repo"], _pr["number"], "unmatched_model", _i)
            CHUNK_IDX[(_short, _k)] = (_pr["repo"], _pr["number"], _c["chunk_index"])

# NOTE: judgment_id is NOT unique across arms — export_verification builds it
# from pr_key + kind + index, with no arm component, so two arms that reviewed
# the same PR collide (10 such ids here). Everything below is therefore keyed
# by (arm, judgment_id); keying by judgment_id alone silently drops rows.
rows, verdicts = {}, {}
for arm in ARMS:
    for r in csv.DictReader(open(f"reports/subset30-{arm}-verification.csv")):
        r["_arm"] = ARMS[arm]
        rows[(ARMS[arm], r["judgment_id"])] = r
    for k, v in json.load(open(f"work/halluc/{arm}.verdicts.json"))["verdicts"].items():
        verdicts[(ARMS[arm], k)] = v

def pool(pred):
    return sorted(k for k, v in verdicts.items() if pred(rows[k], v))

strata = [
    ("claude-arm founded",  pool(lambda r, v: r["_arm"] in ("opus", "sonnet") and v["verdict"] == "founded"), 20),
    ("qwen unfounded",      pool(lambda r, v: r["_arm"] == "qwen" and v["verdict"] == "unfounded"), 12),
    ("qwen founded",        pool(lambda r, v: r["_arm"] == "qwen" and v["verdict"] == "founded"), 8),
    ("unverifiable (any)",  pool(lambda r, v: v["verdict"] == "unverifiable"), 6),
]

def _chunk_for(k):
    repo, number, ci = CHUNK_IDX[k]
    return recover_chunk(RUNDIR[k[0]], REVIEW_PROMPT, repo, number, ci)["chunk"].rstrip()


rng = random.Random(SEED)
picked, seen = [], set()
for name, p, n in strata:
    avail = [k for k in p if k not in seen]
    take = rng.sample(avail, min(n, len(avail)))
    seen.update(take)
    picked.extend((name, k) for k in take)
    print(f"{name:22s} pool={len(p):3d} sampled={len(take)}")

# blind review sheet
out = ["# Hallucination screen — human verification slice",
       "",
       f"{len(picked)} judgments, seed {SEED}. Stratified, not uniform: weighted toward the",
       "verdicts where a biased judge would do the most damage (see",
       "`work/halluc/build_human_slice.py` for why).",
       "",
       "**The machine's verdict is deliberately not shown.** Judge each comment against",
       "the chunk on its own, then record `founded` / `unfounded` / `unverifiable` in",
       "`reports/hallucination-human-slice.csv` against the matching id.",
       "",
       "Definitions are in `prompts/hallucination_v1.md` — the same rubric the machine got.",
       "", "---", ""]
for i, (stratum, k) in enumerate(picked, 1):
    r = rows[k]
    out += [f"## {i}. `{k[1]}`", "",
            f"**Arm:** `{r['_arm']}`  •  **File:** `{r['file']}`  •  **comment on line {r['model_line']}**  "
            f"•  [PR #{r['pr_number']}]({r['pr_url']})", "",
            "**The chunk the reviewer saw** (the machine judged from exactly this and nothing else):", "",
            "```diff", _chunk_for(k), "```", "",
            "**The reviewer's comment:**", "",
            "> " + r["model_comment"].replace("\n", "\n> "), "",
            "**Your verdict:** `founded` / `unfounded` / `unverifiable` — _____________", "",
            "---", ""]
open("reports/hallucination-human-slice.md", "w").write("\n".join(out))

with open("reports/hallucination-human-slice.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["judgment_id", "arm", "file", "model_line",
                                      "human_verdict", "human_notes"])
    w.writeheader()
    for stratum, k in picked:
        r = rows[k]
        w.writerow({"judgment_id": k[1], "arm": r["_arm"], "file": r["file"],
                    "model_line": r["model_line"], "human_verdict": "", "human_notes": ""})

json.dump({"seed": SEED, "picked": [{"stratum": s, "arm": k[0], "judgment_id": k[1]} for s, k in picked]},
          open("work/halluc/human_slice_key.json", "w"), indent=2)
print(f"\nwrote {len(picked)} to reports/hallucination-human-slice.{{md,csv}}")
