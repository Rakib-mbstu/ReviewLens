"""Draw the blind human sheet for every RQ1 match, and render it in two passes.

RQ1's whole result rests on 8 match decisions made by `match_v1`, an LLM judge
that has never been checked against a human. The hallucination screen — the
other LLM judge in this pipeline — agreed with the owner at chance level
(kappa = 0.046, `reports/hallucination-screen.md`), so the matcher cannot be
assumed sound just because it is frozen and deterministic.

There are only 8 matches, so this takes the census rather than the >=20%
sample: sampling error is not worth carrying when the population fits on one
page.

Three design choices, each fixing something the hallucination slice got wrong
or left thin:

  * BLIND TO THE ARM. Sheet ids are M1..M8 in a seeded shuffle, and neither
    the sheet nor the CSV names the model. The hallucination slice printed the
    arm, which lets a rater lean on a prior about which model is better. The
    id -> (arm, judgment_id) mapping lives in match_sheet_key.json and is
    joined afterwards.
  * TWO PASSES, RECORDED SEPARATELY. `verdict_comments_only` mirrors exactly
    what the judge saw — the two comments and their lines, nothing else — so
    human-vs-judge agreement measures the judge on its own evidence.
    `verdict_with_code` is filled afterwards from the companion chunks file
    and answers the different question of whether the match is real. Mixing
    the two would conflate "the judge was wrong" with "the human had more
    information".
  * NON-DESTRUCTIVE. build_human_slice.py rewrites its CSV blank on every run,
    which nearly cost a completed verification pass. This one refuses to
    overwrite a CSV that already carries a verdict.

The >=3-line rule is applied mechanically by the matcher before the judge is
ever called, so both judge and human are ruling on semantic equivalence alone.
"""
import csv, json, os, random, sys

sys.path.insert(0, os.getcwd())
from reviewlens.eval.hallucination import recover_chunk
from reviewlens.eval.export_verification import _judgment_id, run_slug
from reviewlens.review.prompt import load_prompt

SEED = 20260831
ARMS = {"qwen3-coder-30b-a3b-instruct": "qwen", "claude-opus": "opus", "claude-sonnet-5": "sonnet"}
SHEET = "reports/match-verification.md"
CHUNKS = "reports/match-verification-chunks.md"
SHEET_CSV = "reports/match-verification.csv"
KEY = "work/match/match_sheet_key.json"
REVIEW_PROMPT = load_prompt("prompts/review_v1.md")

# --- refuse to clobber completed work ------------------------------------
if os.path.exists(SHEET_CSV):
    done = [r for r in csv.DictReader(open(SHEET_CSV))
            if r.get("verdict_comments_only", "").strip() or r.get("verdict_with_code", "").strip()]
    if done:
        sys.exit(f"REFUSING: {SHEET_CSV} already carries {len(done)} verdict(s). "
                 f"Move it aside first if you really mean to redraw the sheet.")

# --- collect the census --------------------------------------------------
records = []
for run, arm in ARMS.items():
    run_dir = f"runs/subset30/{run}"
    slug = run_slug(json.load(open(f"{run_dir}/run_meta.json"))["model"])
    for pr in json.load(open(f"{run_dir}/eval_matches.json")):
        for i, m in enumerate(pr.get("matches", [])):
            records.append({
                "arm": arm,
                "run_dir": run_dir,
                "judgment_id": _judgment_id(slug, pr["repo"], pr["number"], "match", i),
                "repo": pr["repo"], "number": pr["number"],
                "human": m["human"], "model": m["model"], "judge_reason": m["reason"],
            })

rng = random.Random(SEED)
rng.shuffle(records)
for n, r in enumerate(records, 1):
    r["sheet_id"] = f"M{n}"
print(f"{len(records)} matches: " + ", ".join(
    f"{a}={sum(1 for r in records if r['arm'] == a)}" for a in sorted(ARMS.values())))

# --- pass 1: exactly what the judge saw ----------------------------------
out = [
    "# RQ1 — match verification sheet (census, all 8 matches)",
    "",
    f"Seed {SEED}. **Every** match from the three 30-PR arms, not a sample: the",
    "population is 8, so there is no sampling error to carry.",
    "",
    "**Blind twice over.** The judge's verdict and reason are not shown, and neither",
    "is the arm — ids are `M1`..`M8` in shuffled order. Both are joined afterwards",
    "from `work/match/match_sheet_key.json`.",
    "",
    "Below is **exactly what `match_v1` saw**: two comments and their lines, nothing",
    "else. No code. That is deliberate — judging the judge on evidence it never had",
    "would measure your extra information, not its accuracy.",
    "",
    "## Pass 1 — record in `verdict_comments_only`",
    "",
    "`equivalent` / `not_equivalent`. The frozen rubric is `prompts/match_v1.md`;",
    "it is binary and explicit that **uncertain means `not_equivalent`** — under-match",
    "rather than over-match, because a false `equivalent` inflates recall and that is",
    "the one error this evaluation must not make. Put hedges in `notes`, not in the",
    "verdict.",
    "",
    "## Pass 2 — only after pass 1 is complete for all 8",
    "",
    f"Open `{os.path.basename(CHUNKS)}`, which shows the diff chunk the reviewer saw",
    "for each id, and record `verdict_with_code`. This answers a different question —",
    "*is the match real* — and the gap between the two columns is itself a result.",
    "",
    "---",
    "",
]
for r in records:
    h, m = r["human"], r["model"]
    delta = abs(int(h["line"]) - int(m["line"]))
    out += [
        f"## {r['sheet_id']}",
        "",
        f"**File:** `{h['file']}`  •  human on line {h['line']}, model on line "
        f"{m['line']} (Δ {delta})  •  [PR #{r['number']}]({h['url']})",
        "",
        "**Human reviewer comment:**",
        "",
        "> " + h["comment"].strip().replace("\n", "\n> "),
        "",
        "**Model reviewer comment:**",
        "",
        "> " + m["comment"].strip().replace("\n", "\n> "),
        "",
        "**Do these identify the same underlying issue?** `equivalent` / `not_equivalent`",
        "",
        "---",
        "",
    ]
open(SHEET, "w").write("\n".join(out))

# --- pass 2: the code, in a separate file so pass 1 stays blind ----------
out = [
    "# RQ1 — match verification, pass 2 (the code)",
    "",
    "**Do not open this until pass 1 is complete for all 8 ids.** The diff chunk",
    "the reviewer saw, per sheet id, recovered from the raw request the review",
    "engine sent. Record `verdict_with_code` in `reports/match-verification.csv`.",
    "",
    "---",
    "",
]
for r in records:
    h, m = r["human"], r["model"]
    chunk = recover_chunk(r["run_dir"], REVIEW_PROMPT, r["repo"], r["number"], m["chunk_index"])
    out += [
        f"## {r['sheet_id']}",
        "",
        f"**File:** `{h['file']}`  •  human on line {h['line']}, model on line {m['line']}",
        "",
        "```diff",
        chunk["chunk"].rstrip(),
        "```",
        "",
        "**Human:**", "", "> " + h["comment"].strip().replace("\n", "\n> "), "",
        "**Model:**", "", "> " + m["comment"].strip().replace("\n", "\n> "), "",
        "---", "",
    ]
open(CHUNKS, "w").write("\n".join(out))

# --- the CSV the owner types into, and the key that unblinds it ----------
with open(SHEET_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["sheet_id", "file", "human_line", "model_line",
                                      "verdict_comments_only", "verdict_with_code", "notes"])
    w.writeheader()
    for r in records:
        w.writerow({"sheet_id": r["sheet_id"], "file": r["human"]["file"],
                    "human_line": r["human"]["line"], "model_line": r["model"]["line"],
                    "verdict_comments_only": "", "verdict_with_code": "", "notes": ""})

json.dump({"seed": SEED,
           "picked": [{"sheet_id": r["sheet_id"], "arm": r["arm"],
                       "judgment_id": r["judgment_id"], "repo": r["repo"],
                       "number": r["number"], "judge_verdict": "equivalent",
                       "judge_reason": r["judge_reason"]} for r in records]},
          open(KEY, "w"), indent=2)
print(f"wrote {SHEET}, {CHUNKS}, {SHEET_CSV}, {KEY}")
