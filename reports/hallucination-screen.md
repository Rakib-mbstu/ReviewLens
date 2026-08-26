# RQ2 — hallucination screen (227 judgments)

**Status: machine-screened, not yet human-verified.** Every number here was
produced by one model judging three models' output. A 46-judgment blind human
slice is drawn and pending (`reports/hallucination-human-slice.md`); until it
is filled in, treat these as provisional.

## Method

Each arm's unmatched model comments were sampled at >=20% by
`reviewlens.eval.export_verification` (deterministic seed), then judged against
frozen `hallucination_v1` (sha256 `e05ea232e3eacc15…`). The judge saw **exactly
the diff chunk the reviewer saw** — recovered byte-for-byte from
`raw/chunk_N.json` by inverting `review_v1`'s rendered user message — and
nothing else: no Java sources, no PR pages, no web. That was enforced in the
wrapper and verified afterwards against all nine judge transcripts.

Judge: `claude-code-subagent/fable`, via `claude-code-subagent` (the OpenRouter
key expired 2026-08-25). 227/227 judged, **0 parse failures**.

The rubric has three verdicts, not two. `unverifiable` exists so that "the
chunk cannot settle this" is not forced into either `founded` (which would
flatter the tool) or `unfounded` (which would manufacture hallucinations). It
was used 55 times in 227 — collapsing it either way would have moved the
headline substantially.

## Results

| arm | via | unmatched pop. | judged | founded | unfounded | unverifiable | unfounded / all judged | unfounded / (founded+unfounded) |
|---|---|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | openrouter | 815 | 163 | 62 | 59 | 42 | **36.2%** [29–44] | 48.8% [40–58] |
| `anthropic/claude-sonnet-5` | subagent | 75 | 15 | 13 | 0 | 2 | **0.0%** [0–20] | 0.0% [0–23] |
| `claude-code-subagent/opus` | subagent | 243 | 49 | 37 | 1 | 11 | **2.0%** [0–11] | 2.6% [0–13] |

Both denominators are reported because neither is obviously right: the first
counts `unverifiable` against the model, the second excludes it. The ordering
is identical under both.

**These differences are significant, unlike the recall differences.**

| comparison | Fisher exact (two-sided) |
|---|---|
| qwen vs opus | **p = 3.32e-07** |
| qwen vs sonnet-5 | **p = 0.0028** |
| opus vs sonnet-5 | p = 1.0000 |

## What this changes

RQ1 could not separate these models: recall was 1.0% / 1.0% / 5.9% with
overlapping intervals and p = 0.119. **RQ2 separates them decisively.** qwen
emits an unfounded comment roughly 36% of the time; both Claude arms sit near
zero and are statistically indistinguishable from each other (p = 1.00).

This also sharpens the volume finding. qwen produced 815 unmatched comments to
opus's 243 — and a far larger *share* of them are unfounded. The cost of the
extra volume is not just noise, it is wrong claims about the code.

## The threat to this result, stated plainly

**The judge is a Claude model. Two of the three arms are Claude models. They
scored dramatically better.** That is exactly the pattern self-evaluation bias
produces — and exactly the pattern a real capability gap produces. This screen
cannot separate those two explanations, and no amount of internal consistency
in the judgments would.

This is why the human slice is stratified rather than uniform: it oversamples
the two verdicts where a biased judge does the most damage — Claude-arm
`founded` (excusing a weak Claude comment) and qwen `unfounded` (condemning a
sound qwen comment). If the human agrees with the machine on both strata, the
capability explanation survives. If disagreement concentrates in one direction,
the bias explanation does.

## Secondary observations

- **The judge was markedly less certain about qwen.** 96/163 of qwen judgments
  were `low` confidence (59%) against 10/49 for opus (20%).
- **sonnet-5's 0% is not "clean".** 0 of 15 has a 95% upper bound of 20%. It
  means no hallucination was detected in 15 judgments, not that none exist.
- **The screen is 72% qwen by construction.** >=20% of a large unmatched
  population yields 163 qwen judgments against 15 for sonnet-5, so per-arm
  precision is very uneven. The sonnet-5 interval is nearly uninformative.

## Defect found while joining the arms — since fixed

`export_verification` built `judgment_id` from pr_key + kind + index with **no
run component**, so ids were not unique across runs: 10 ids collided between
the qwen and opus samples (231 rows, 220 distinct ids). Anything joining
several arms' verification CSVs on `judgment_id` alone silently dropped rows —
it cost 11 rows in the first draw of the human slice before it was caught.

Fixed: ids now lead with the run's model slug and the CSV carries a `run`
column. The uniqueness contract is stated rather than implied — an id is unique
within a run and across runs of *different* models, while two runs of the same
model still require the (`run`, `judgment_id`) pair. 231 rows now yield 231
distinct ids.

The fix does not disturb any measurement here. The slug is a constant prefix
within each sampled population, so `sorted()` preserves relative order and the
seeded draw selects the same positions — verified by re-running the export and
the screen end to end: all three arms returned **identical verdict
distributions**, and the human slice redrew the **same 46 judgments**.

## Deviations from an API-served judge

Recorded because they are part of the treatment:

1. **Shared context.** 227 judgments ran as 9 subagent batches (11–36 each,
   split on a ~240KB budget), so within a batch one judgment could influence
   another. The wrapper instructed against it; instruction is not isolation.
2. **No temperature control.** Keys were computed with the frozen
   `temperature: 0.0`, which the subagent channel cannot honor.
3. **Tool access.** Forbidden in the wrapper and audited afterwards: no
   WebFetch, WebSearch, Grep or Glob in any transcript, and no file touched
   outside each batch's own input/output.
4. **Hand-copied keys.** One batch made a key transcription error and
   self-corrected. Every batch was checked for key validity, completeness, and
   cross-batch duplicates before merging.
