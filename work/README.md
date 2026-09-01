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

## A warning about `work/halluc/build_human_slice.py`

It rewrites `reports/hallucination-human-slice.csv` **blank** on every run and
came within one command of destroying a completed verification pass.
`work/match/build_match_sheet.py` was written afterwards and refuses to
overwrite a response file that already carries a verdict; prefer that pattern.
