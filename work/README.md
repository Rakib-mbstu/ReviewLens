# `work/` — study scaffolding, retained for provenance

**Not part of the pipeline.** Nothing in `reviewlens/` imports from here, and no
published number is produced by this directory alone. It exists so that the
one-off steps behind the study's human-verification passes are inspectable
rather than described.

The pipeline proper is `reviewlens/{mine,review,eval}`; the commands that
produce every report are in the README's "Reproducing the evaluation" section.

## What is in here

| path | what it is |
|---|---|
| `demo/` | The ~90s demo script, its `vhs` tape, and recording instructions. |
| `match/` | RQ1's match verification: the blind sheet builder, the sheet→key join, and the record of the blind pass. |
| `halluc/` | RQ2's hallucination screen: the human-slice builder and the batch relay. |
| `spotcheck-fable/` | The second rater's pass over the category spot-check. |
| `rq3/` | The subagent relay for the Claude arms of the model comparison. |
| `rebuild_run_meta.py` | One-off repair of run metadata after the `judgment_id` fix. |

## Why the relay directories exist at all

The OpenRouter budget could not fund a Claude pass, so three arms — two review
arms, one judging arm — were driven through Claude Code subagents instead of the
API. To keep that comparable, the *real* engine was driven via `OfflineClient`:
identical chunks, identical prompt bytes, identical parser. The relay is the
mechanical part of that — render requests to JSONL, hand them over, replay the
answers back through the parser.

Those wrappers are **part of the treatment, not around it**, which is why they
are committed. An early version of one restated the frozen prompt's rules in its
own words and cut the model's output rate by ~3x. Every wrapper here is pure
mechanics (which file to read, which to write), byte-identical across batches,
and never restates a rubric. That claim is checkable because the files are here.

## Two things that are deliberately absent

`.gitignore` excludes `work/*/batches/` and `work/halluc/backups/`. Batches are
mechanical splits of the committed `*.requests.jsonl` and backups are
pre-regeneration copies of committed CSVs — neither is a record of what a model
was actually sent or answered, so committing them would add weight without
adding evidence.

## The two match-verification sheets

`build_match_sheet.py` and `join_verdicts.py` both default to the **subset30**
census (8 matches, rated 2026-08-31, published as
`reports/match-verification*.md`). Running either with no arguments regenerates
that census byte-for-byte; the builder refuses to redraw a sheet whose CSV
already carries verdicts, so this is safe.

The same scripts also draw the **full-corpus** census — the 5 matches behind the
1.6% headline, which the 2026-09-02 decision originally left unverified and
which was reopened on 2026-09-04:

```bash
python work/match/build_match_sheet.py \
    --runs runs/qwen/qwen3-coder-30b-a3b-instruct \
    --prefix match-verification-full87 \
    --key work/match/match_full87_key.json \
    --corpus-label "the 87-PR full-corpus qwen run" --seed 20260904
```

Rate `verdict_comments_only` in `reports/match-verification-full87.csv` from
the sheet, then join and score:

```bash
python work/match/join_verdicts.py \
    --key work/match/match_full87_key.json \
    --sheet reports/match-verification-full87.csv \
    --out reports/match-verification-full87-joined.csv --blind none

python -m reviewlens.eval.compare --runs runs/qwen/qwen3-coder-30b-a3b-instruct \
    --judge-model google/gemini-2.5-flash-lite \
    --verified reports/match-verification-full87-joined.csv \
    --report reports/qwen3-coder-30b-a3b-instruct-full87-verified.md
```

`--blind none` is deliberate. The subset30 sheet emits a second `-blind` CSV
only because its verdicts were revised after the arms were disclosed; a single
pass that is never revised has the stronger provenance and needs one file. This
census has one arm, so there is nothing to unblind and no reason to revise.

**Rated 2026-09-04: 5 of 5 upheld.** Recall is unchanged at 5/318 = 1.6% and is
no longer judge-only; see `reports/match-verification-results.md`. The commands
above are the ones that produced
`reports/qwen3-coder-30b-a3b-instruct-full87-verified.md`, and they replay from
the committed CSVs.

`--run-dir` is not needed here: a key written by the current
`build_match_sheet.py` records each match's run directory, because two runs of
the same model share both the arm label and the judgment ids, so the label alone
cannot tell them apart. The published subset30 key predates that field, which is
why the label map is kept as a fallback.

## A warning about `work/halluc/build_human_slice.py`

It rewrites `reports/hallucination-human-slice.csv` **blank** on every run and
came within one command of destroying a completed verification pass.
`work/match/build_match_sheet.py` was written afterwards and refuses to
overwrite a response file that already carries a verdict; prefer that pattern.
