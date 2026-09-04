# Demo

`demo.sh` walks the pipeline and the evaluation in about 90 seconds. It is the
script the README's GIF records.

```bash
bash work/demo/demo.sh          # from the repo root
PAUSE=0 bash work/demo/demo.sh  # no pauses, for a quick check or CI
```

**It costs $0 and needs no `OPENROUTER_API_KEY`**: every LLM call it makes is a
cache hit, and the client only demands a key on a call that actually reaches the
network.

**It does need the artifacts.** `runs/`, `cache/` and the mined corpus under
`data/` are gitignored, so a fresh clone has none of them. The demo fetches the
3.1MB bundle from the v0.1.0 release on first run (`DEMO_NO_FETCH=1` suppresses
that), verifies its sha256, and prints SKIPPED for the dependent steps if the
fetch fails. `bash work/demo/fetch_artifacts.sh` does it on its own and is
idempotent.

The review stage needs credentials on top of that — it fetches each PR's
pre-review diff from GitHub — so it runs only when `GITHUB_TOKEN` is set and
prints a visible SKIPPED banner otherwise, rather than quietly dropping a step.

Step 3 re-runs `reviewlens.eval` on `runs/subset30/claude-opus/` and rewrites
that run's `eval_matches.json`. The replay is deterministic from the cache, so
the file comes back byte-identical; `git status` after a demo should be clean.

## Re-recording the GIF

`docs/demo.gif` is recorded and linked from the README. Recorded 2026-09-04
with vhs 0.11.0; 5.0MB, ~95s, the full run through step 6.

```bash
brew install vhs        # or: go install github.com/charmbracelet/vhs@latest
vhs work/demo/demo.tape # writes docs/demo.gif
```

`demo.tape` pins the terminal size, theme and font size so the GIF is
reproducible rather than dependent on whoever recorded it, and **the committed
GIF is the tape's unmodified output** — no post-processing step sits between
them, so re-running the tape is enough to reproduce it. If the run takes longer
than the tape's `Sleep`, raise it: vhs cuts the recording at that mark whether
or not the script has finished. Check the last frame before committing.

**On the file size.** 5.0MB is large for a README, and the obvious fixes were
tried and rejected. Dropping the tape to `Set Framerate 12` made it *bigger*
(5.4MB) — fewer frames means larger inter-frame deltas. `gifsicle -O3` would
help, but it puts a post-processing step between the tape and the artifact, so
the tape would no longer reproduce what is committed. An `asciinema rec` + `agg`
pipeline produces a much smaller file and is not byte-reproducible between
recordings. Reproducibility won; if the size ever becomes the problem, shorten
the demo rather than post-processing the GIF.
