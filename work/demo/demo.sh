#!/usr/bin/env bash
# ReviewLens demo — the pipeline and the honesty machinery, in about 90 seconds.
#
# Everything here runs against the warm LLM cache, so it costs $0 and needs no
# OPENROUTER_API_KEY. Two things it does need, both handled visibly rather than
# silently:
#
#   * The artifacts (runs/, cache/, the mined corpus under data/) are gitignored,
#     so a fresh clone has none of them. They are fetched from the v0.1.0 release
#     on first run; if that fails the dependent steps print SKIPPED.
#   * The review stage fetches each PR's pre-review diff from GitHub, so it needs
#     a read-only GITHUB_TOKEN and prints SKIPPED without one.
#
# The demo never silently pretends to have run something it did not.
#
# Usage:  bash work/demo/demo.sh            # from the repo root
#         PAUSE=0 bash work/demo/demo.sh    # no pauses, for CI or a quick check
#         DEMO_NO_FETCH=1 bash …            # never touch the network
set -uo pipefail

PY=${PY:-.venv/bin/python}
PAUSE=${PAUSE:-1.6}
DEMO_PR=mockito__mockito__2650
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

step() { printf '\n\033[1;36m── %s\033[0m\n' "$1"; sleep "$PAUSE"; }
run()  { printf '\033[2m$ %s\033[0m\n' "$*"; sleep 0.4; "$@"; sleep "$PAUSE"; }

step "ReviewLens — an LLM code reviewer, and the evaluation that grades it"
run head -c 400 Readme.md

ARTIFACTS=1
if ! bash work/demo/fetch_artifacts.sh --check; then
  if [ -n "${DEMO_NO_FETCH:-}" ]; then
    ARTIFACTS=0
  else
    step "0. Fetching the evaluation artifacts (gitignored; ~3MB, one time)"
    bash work/demo/fetch_artifacts.sh || ARTIFACTS=0
  fi
fi

step "1. Frozen prompts. A prompt change means a new version, never an edit."
$PY - <<'PYEOF'
import hashlib, glob, re, os
for path in sorted(glob.glob("prompts/*.md")):
    head = open(path, encoding="utf-8").read(400)
    frozen = re.search(r"^frozen: (\S+)", head, re.M)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()[:12]
    print(f"  {os.path.basename(path):22s} frozen {frozen.group(1) if frozen else '?':12s} sha256 {digest}…")
PYEOF
sleep "$PAUSE"

if [ "$ARTIFACTS" = 1 ] && [ -n "${GITHUB_TOKEN:-}" ]; then
  step "2. Review one PR on its PRE-REVIEW state (warm cache: no API key, \$0)"
  mkdir -p "$TMP/corpus"
  cp "data/corpus-subset30/$DEMO_PR.json" "data/corpus-subset30/categories.json" "$TMP/corpus/"
  $PY - "$TMP/corpus" "$DEMO_PR" <<'PYEOF'
import json, sys
out, key = sys.argv[1], sys.argv[2]
manifest = json.load(open("data/corpus-subset30/manifest.json", encoding="utf-8"))
manifest["prs"] = [p for p in manifest["prs"] if key.endswith(str(p.get("number")))]
json.dump(manifest, open(f"{out}/manifest.json", "w", encoding="utf-8"), indent=1)
PYEOF
  run env -u OPENROUTER_API_KEY "$PY" -m reviewlens.review \
      --corpus "$TMP/corpus" --model qwen/qwen3-coder-30b-a3b-instruct --out "$TMP/run"
elif [ "$ARTIFACTS" = 1 ]; then
  step "2. Review step SKIPPED — GITHUB_TOKEN unset (it fetches the pre-review diff)"
  printf '   Set a read-only GITHUB_TOKEN to include it. Everything below is offline.\n'
  sleep "$PAUSE"
fi

if [ "$ARTIFACTS" != 1 ]; then
  step "Steps 2-5 SKIPPED — no evaluation artifacts"
  cat <<'MSG'
   runs/, cache/ and the mined corpus are gitignored build products, so a fresh
   clone cannot replay them. Fetch them and re-run:

       bash work/demo/fetch_artifacts.sh

   Step 6 below reads a committed report and works either way.
MSG
  sleep "$PAUSE"
fi

if [ "$ARTIFACTS" = 1 ]; then

step "3. Match model comments to what the humans actually said (±3 lines + semantic judge)"
run env -u OPENROUTER_API_KEY "$PY" -m reviewlens.eval \
    --run runs/subset30/claude-opus/ \
    --judge-model google/gemini-2.5-flash-lite \
    --report "$TMP/opus.md"

step "4. RQ3 — three models, one corpus, with the uncertainty printed"
run env -u OPENROUTER_API_KEY "$PY" -m reviewlens.eval.compare \
    --runs runs/subset30/qwen3-coder-30b-a3b-instruct/ runs/subset30/claude-sonnet-5/ runs/subset30/claude-opus/ \
    --judge-model google/gemini-2.5-flash-lite \
    --verified reports/match-verification-joined.csv \
    --report "$TMP/rq3.md"
run sed -n '5,16p' "$TMP/rq3.md"

step "5. Every match here was checked by a human. Without that, the table says so."
run env -u OPENROUTER_API_KEY "$PY" -m reviewlens.eval.compare \
    --runs runs/subset30/qwen3-coder-30b-a3b-instruct/ runs/subset30/claude-sonnet-5/ runs/subset30/claude-opus/ \
    --judge-model google/gemini-2.5-flash-lite \
    --report "$TMP/rq3-unverified.md"
run grep -m1 "No human verified" "$TMP/rq3-unverified.md"

fi

step "6. The other LLM judge in this pipeline did NOT survive its human check"
run head -9 reports/hallucination-screen.md

step "Full write-up: reports/technical-report.md"
