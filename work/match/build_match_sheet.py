"""Draw the blind human sheet for every RQ1 match, and render it in two passes.

RQ1's whole result rests on match decisions made by `match_v1`, an LLM judge
that has never been checked against a human. The hallucination screen — the
other LLM judge in this pipeline — agreed with the owner at chance level
(kappa = 0.046, `reports/hallucination-screen.md`), so the matcher cannot be
assumed sound just because it is frozen and deterministic.

Every run this is pointed at has a handful of matches, so it takes the census
rather than the >=20% sample: sampling error is not worth carrying when the
population fits on one page.

Three design choices, each fixing something the hallucination slice got wrong
or left thin:

  * BLIND TO THE ARM. Sheet ids are M1..Mn in a seeded shuffle, and neither
    the sheet nor the CSV names the model. The hallucination slice printed the
    arm, which lets a rater lean on a prior about which model is better. The
    id -> (arm, judgment_id) mapping lives in the key JSON and is joined
    afterwards. With a single run there is no arm to hide, but the judge's
    verdict and reason are withheld either way — that is the blind that makes
    human-vs-judge agreement mean anything.
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

Invoked with no arguments it redraws the subset30 census exactly as published
(`reports/match-verification.md`, seed 20260831). The flags exist so the same
blind procedure can be pointed at another run — the full-corpus qwen census is
`--runs runs/qwen/qwen3-coder-30b-a3b-instruct --prefix match-verification-full87
--corpus-label "the 87-PR full-corpus run" --seed 20260904` — rather than
copied and edited, which is how two procedures drift apart.
"""
import argparse, csv, json, os, random, sys

sys.path.insert(0, os.getcwd())
from reviewlens.eval.hallucination import recover_chunk
from reviewlens.eval.export_verification import _judgment_id, run_slug
from reviewlens.review.prompt import load_prompt

# Short arm labels for the published subset30 census, so regenerating it keeps
# the labels its key JSON already carries. Anything else falls back to the run
# directory's own name.
ARM_LABELS = {"qwen3-coder-30b-a3b-instruct": "qwen", "claude-opus": "opus",
              "claude-sonnet-5": "sonnet"}
SUBSET30_RUNS = ["runs/subset30/qwen3-coder-30b-a3b-instruct",
                 "runs/subset30/claude-opus", "runs/subset30/claude-sonnet-5"]

ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--runs", nargs="+", default=SUBSET30_RUNS,
                help="run directories to census (default: the three subset30 arms)")
ap.add_argument("--seed", type=int, default=20260831,
                help="shuffle seed; changing it reorders the sheet ids")
ap.add_argument("--prefix", default="match-verification",
                help="basename for reports/<prefix>{.md,-chunks.md,.csv} and the key JSON")
ap.add_argument("--corpus-label", default="the three 30-PR arms",
                help="how the sheet describes where the matches came from")
ap.add_argument("--key", default="work/match/match_sheet_key.json",
                help="where the id -> (arm, judgment_id) unblinding map is written")
args = ap.parse_args()

SHEET = "reports/%s.md" % args.prefix
CHUNKS = "reports/%s-chunks.md" % args.prefix
SHEET_CSV = "reports/%s.csv" % args.prefix
KEY = args.key
REVIEW_PROMPT = load_prompt("prompts/review_v1.md")

# --- refuse to clobber completed work ------------------------------------
if os.path.exists(SHEET_CSV):
    done = [r for r in csv.DictReader(open(SHEET_CSV))
            if r.get("verdict_comments_only", "").strip() or r.get("verdict_with_code", "").strip()]
    if done:
        sys.exit("REFUSING: %s already carries %d verdict(s). "
                 "Move it aside first if you really mean to redraw the sheet."
                 % (SHEET_CSV, len(done)))

# --- collect the census --------------------------------------------------
records = []
for run_dir in args.runs:
    run_dir = run_dir.rstrip("/")
    name = os.path.basename(run_dir)
    arm = ARM_LABELS.get(name, name)
    slug = run_slug(json.load(open("%s/run_meta.json" % run_dir))["model"])
    for pr in json.load(open("%s/eval_matches.json" % run_dir)):
        for i, m in enumerate(pr.get("matches", [])):
            records.append({
                "arm": arm,
                "run_dir": run_dir,
                "judgment_id": _judgment_id(slug, pr["repo"], pr["number"], "match", i),
                "repo": pr["repo"], "number": pr["number"],
                "human": m["human"], "model": m["model"], "judge_reason": m["reason"],
            })

rng = random.Random(args.seed)
rng.shuffle(records)
for n, r in enumerate(records, 1):
    r["sheet_id"] = "M%d" % n
N = len(records)
print("%d matches: " % N + ", ".join(
    "%s=%d" % (a, sum(1 for r in records if r["arm"] == a))
    for a in sorted(set(r["arm"] for r in records))))

# With one run there is no arm to blind; saying so would be a false claim about
# the procedure, and leaving the multi-arm wording in would be worse.
if len(args.runs) > 1:
    blind_note = [
        "**Blind twice over.** The judge's verdict and reason are not shown, and neither",
        "is the arm — ids are `M1`..`M%d` in shuffled order. Both are joined afterwards" % N,
        "from `%s`." % KEY,
    ]
else:
    blind_note = [
        "**Blind to the judge.** Its verdict and reason are not shown, and the ids are",
        "`M1`..`M%d` in shuffled order. This is a single run, so there is no arm to" % N,
        "hide; the judge's own output is joined afterwards from `%s`." % KEY,
    ]

# --- pass 1: exactly what the judge saw ----------------------------------
out = [
    "# RQ1 — match verification sheet (census, all %d matches)" % N,
    "",
    "Seed %d. **Every** match from %s, not a sample: the" % (args.seed, args.corpus_label),
    "population is %d, so there is no sampling error to carry." % N,
    "",
] + blind_note + [
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
    "## Pass 2 — only after pass 1 is complete for all %d" % N,
    "",
    "Open `%s`, which shows the diff chunk the reviewer saw" % os.path.basename(CHUNKS),
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
        "## %s" % r["sheet_id"],
        "",
        "**File:** `%s`  •  human on line %s, model on line "
        "%s (Δ %d)  •  [PR #%s](%s)" % (h["file"], h["line"], m["line"], delta,
                                        r["number"], h["url"]),
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
    "**Do not open this until pass 1 is complete for all %d ids.** The diff chunk" % N,
    "the reviewer saw, per sheet id, recovered from the raw request the review",
    "engine sent. Record `verdict_with_code` in `%s`." % SHEET_CSV,
    "",
    "---",
    "",
]
for r in records:
    h, m = r["human"], r["model"]
    chunk = recover_chunk(r["run_dir"], REVIEW_PROMPT, r["repo"], r["number"], m["chunk_index"])
    out += [
        "## %s" % r["sheet_id"],
        "",
        "**File:** `%s`  •  human on line %s, model on line %s" % (h["file"], h["line"], m["line"]),
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

# run_dir is recorded per record, not inferred downstream from the arm label:
# two runs of the same model share both the label and the judgment ids, so the
# label alone cannot say which run a match came from.
json.dump({"seed": args.seed,
           "picked": [{"sheet_id": r["sheet_id"], "arm": r["arm"],
                       "run_dir": r["run_dir"].rstrip("/") + "/",
                       "judgment_id": r["judgment_id"], "repo": r["repo"],
                       "number": r["number"], "judge_verdict": "equivalent",
                       "judge_reason": r["judge_reason"]} for r in records]},
          open(KEY, "w"), indent=2)
print("wrote %s, %s, %s, %s" % (SHEET, CHUNKS, SHEET_CSV, KEY))
