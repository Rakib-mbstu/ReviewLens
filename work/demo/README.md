# Demo

`demo.sh` walks the pipeline and the evaluation in about 90 seconds. It is the
script the README's GIF records.

```bash
bash work/demo/demo.sh          # from the repo root
PAUSE=0 bash work/demo/demo.sh  # no pauses, for a quick check or CI
```

**It costs $0 and needs no `OPENROUTER_API_KEY`**: every LLM call it makes is a
cache hit, and the client only demands a key on a call that actually reaches the
network. The review stage is the exception — it fetches each PR's pre-review
diff from GitHub — so it runs only when `GITHUB_TOKEN` is set and prints a
visible SKIPPED banner otherwise, rather than quietly dropping a step.

Step 3 re-runs `reviewlens.eval` on `runs/subset30/claude-opus/` and rewrites
that run's `eval_matches.json`. The replay is deterministic from the cache, so
the file comes back byte-identical; `git status` after a demo should be clean.

## Recording the GIF

No recorder is installed in this repo's environment, so this is a manual step.

```bash
brew install vhs        # or: go install github.com/charmbracelet/vhs@latest
vhs work/demo/demo.tape # writes docs/demo.gif
```

`demo.tape` pins the terminal size, theme and font size so the GIF is
reproducible rather than dependent on whoever recorded it. If the run takes
longer than the tape's `Sleep`, raise it — vhs cuts the recording at that mark
regardless of whether the script has finished.

Then link it from the README, under the title:

```markdown
![ReviewLens demo](docs/demo.gif)
```

An `asciinema rec` + `agg` pipeline works too and produces a much smaller file,
but the output is not byte-reproducible between recordings.
