# RQ2 — hallucination screen (227 machine judgments, 46 human-verified)

**Status: the machine screen's headline is retracted.** A 46-judgment blind
human slice was completed 2026-08-31 (`reports/hallucination-human-slice.csv`).
Human and machine agree on **20/46 = 43.5%** of judgments, Cohen's
**κ = 0.046** — chance level. The screen's decisive per-arm separation
(qwen 36.2% unfounded vs. Claude arms ~0%, p = 3.3e-07) **does not survive
verification** and must not be cited as a finding.

What the screen produced is reported below as *what the judge said*, followed by
what the human check did to it. The machine numbers are kept in place, not
deleted: the gap between the two is the result.

## Method — the machine screen

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
flatter the tool) or `unfounded` (which would manufacture hallucinations). The
machine used it 55 times in 227. The human used it far more often — see below;
that difference turns out to be a substantial part of the disagreement.

## Method — the human slice

46 judgments, seed 20260826, drawn by `work/halluc/build_human_slice.py`.
Stratified, not uniform: oversampled toward the two verdicts where a biased
judge does the most damage — Claude-arm `founded` (excusing a weak Claude
comment) and qwen `unfounded` (condemning a sound qwen comment).

The sheet was rendered **without the machine's verdict**, from the same chunk
and the same frozen rubric the machine got. Verdicts were joined afterwards by
(`arm`, `judgment_id`). Single rater, no adjudication pass.

| stratum | pool | sampled |
|---|---|---|
| claude-arm `founded` | 50 | 20 |
| qwen `unfounded` | 59 | 12 |
| qwen `founded` | 62 | 8 |
| `unverifiable` (any arm) | 55 | 6 |

Because the draw is stratified, raw counts over the 46 are **not** an estimate
of anything about the population. Only within-stratum rates, and estimates
reweighted by stratum, are interpretable.

## What the machine screen said

| arm | via | unmatched pop. | judged | founded | unfounded | unverifiable | unfounded / all judged | unfounded / (founded+unfounded) |
|---|---|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | openrouter | 815 | 163 | 62 | 59 | 42 | 36.2% [29–44] | 48.8% [40–58] |
| `anthropic/claude-sonnet-5` | subagent | 75 | 15 | 13 | 0 | 2 | 0.0% [0–20] | 0.0% [0–23] |
| `claude-code-subagent/opus` | subagent | 243 | 49 | 37 | 1 | 11 | 2.0% [0–11] | 2.6% [0–13] |

| comparison | Fisher exact (two-sided) |
|---|---|
| qwen vs opus | p = 3.32e-07 |
| qwen vs sonnet-5 | p = 0.0028 |
| opus vs sonnet-5 | p = 1.0000 |

**These are the judge's outputs, not measurements of the arms.** The section
below is why.

## What the human check did to it

### Agreement

| machine \ human | founded | unfounded | unverifiable |
|---|---|---|---|
| **founded** | 17 | 3 | 8 |
| **unfounded** | 6 | 1 | 5 |
| **unverifiable** | 2 | 2 | 2 |

- Raw agreement **20/46 = 43.5%**; **Cohen's κ = 0.046** (p_o = 0.435,
  p_e = 0.407). The screen's per-judgment verdicts carry essentially no signal.
- Restricting to the 27 judgments where *both* sides were decisive
  (neither said `unverifiable`): 18/27 = 67%, **κ = −0.008**. Collapsing the
  third category does not rescue it.
- The 26 disagreements decompose as: 13 where the human escalated a decided
  machine verdict to `unverifiable`, 4 where the human decided something the
  machine would not, and **9 flat contradictions** between `founded` and
  `unfounded`.

### Per stratum — the part that dismantles the headline

| stratum | machine verdict upheld by human | 95% (Wilson) | human's own mix |
|---|---|---|---|
| claude-arm `founded` | 13/20 = 65% | — | 13 founded, 3 unfounded, 4 unverifiable |
| — of which opus | 8/14 = 57% | [33–79] | |
| — of which sonnet-5 | 5/6 = 83% | [44–97] | |
| qwen `founded` | 4/8 = 50% | [22–78] | 4 founded, 0 unfounded, 4 unverifiable |
| **qwen `unfounded`** | **1/12 = 8%** | **[1–35]** | 6 founded, 1 unfounded, 5 unverifiable |
| `unverifiable` (any) | 2/6 = 33% | — | 2 founded, 2 unfounded, 2 unverifiable |

The qwen `unfounded` row is the load-bearing one. Those 12 are a seeded random
draw from the 59 qwen comments the machine condemned, and the human upheld
**one**. The 36.2% headline is built on those 59 verdicts; at the observed rate
roughly 5 of them survive scrutiny.

Both of the pre-registered bias hypotheses moved in the predicted direction:
the judge over-credited the Claude arms (7 of 20 `founded` verdicts did not
hold) and over-condemned qwen (11 of 12 `unfounded` verdicts did not hold).
Stated carefully: **the directional asymmetry is suggestive but not itself
significant** — among the 9 flat contradictions, 3 went one way and 6 the other,
McNemar exact p = 0.508. The finding that stands on its own is the collapse of
the qwen `unfounded` cell, which holds regardless of what mechanism produced it.

The judge's self-reported confidence does not help. Agreement was 13/26 (50%)
on its `high`-confidence judgments and 7/20 (35%) on its `low`-confidence ones —
better ordered than chance, but `high` confidence still coin-flips.

### Reweighted rates — indicative only

Post-stratifying the human labels back onto each arm's judged population, with
stratified variance and a finite-population correction:

| arm | screen said (unfounded / all judged) | human-reweighted | 95% CI |
|---|---|---|---|
| qwen | 36.2% | 11.6% | [0.3, 22.9] |
| opus | 2.0% | 10.8% | [0.0, 22.3] |
| sonnet-5 | 0.0% | 14.4% | [0.0, 36.1] |

**Do not cite these as the RQ2 result.** They rest on 6–14 draws per cell,
every interval covers every other arm's point estimate, and the ordering the
screen reported is not merely weakened but inverted-to-flat. Two further
problems:

- **Coverage gap.** The `unverifiable` stratum's 6 draws all landed on qwen, so
  12 of opus's 49 judgments (11 `unverifiable` + 1 `unfounded`) and 2 of
  sonnet-5's 15 have no human coverage. The table above credits those with zero
  unfounded, which flatters the Claude arms. Imputing them at the rate observed
  in qwen's `unverifiable` cell (2/6) moves opus to 19.0% and sonnet-5 to 18.9%.
- **One rater.** There is no second human and no adjudication, so κ = 0.046
  establishes that the screen is unreliable, not which side is right.

The defensible reading is that after verification **RQ2 does not separate these
three arms**, for the same reason RQ1 did not.

## What this changes

- The claim "RQ2 separates them decisively" is **withdrawn**. Neither RQ1
  (recall 1.0% / 1.0% / 4.9% after human verification, p = 0.212) nor RQ2
  distinguishes the three arms at this corpus size.
- **RQ1's judge survived the same treatment RQ2's did not.** All 8 matches were
  hand-checked blind and 7 held (`reports/match-verification-results.md`). Two
  frozen LLM judges, one pipeline: the matcher is usable, the hallucination
  screen is not. "Frozen and deterministic" is not evidence of correctness for
  either — only the human check separated them.
- The volume finding survives only in its weaker form: qwen produced 815
  unmatched comments to opus's 243. The claim that a *larger share* of them are
  unfounded is no longer supported.
- The self-evaluation-bias threat named in the previous draft was the right
  threat to name, and the slice was the right instrument. It fired.
- An LLM judge, chunk-only and on a frozen rubric, was **not** a usable
  measurement instrument for this task. That is itself a reportable RQ2 result,
  and a more robust one than the number it was meant to produce.

## Secondary observations

- **The human used `unverifiable` 2.5× as often as the machine** on the same 46
  (15 vs. 6). The chunk-only constraint binds harder than the judge admitted;
  the judge resolved genuinely undecidable cases rather than declining them,
  in both directions.
- **The judge was markedly less certain about qwen** — 96/163 qwen judgments at
  `low` confidence (59%) against 10/49 for opus (20%). Read alongside the
  stratum table, low confidence on qwen coincided with the verdicts that failed
  verification worst.
- **sonnet-5's 0% was never "clean"** — 0 of 15 has a 95% upper bound of 20%,
  and the human found an unfounded comment in its 6 sampled `founded` verdicts.
- **The screen is 72% qwen by construction.** >=20% of a large unmatched
  population yields 163 qwen judgments against 15 for sonnet-5, so per-arm
  precision is very uneven regardless of judge quality.

## Reproducing this

```bash
python work/halluc/build_human_slice.py     # DESTRUCTIVE: rewrites the CSV blank
```

The slice builder writes both `reports/hallucination-human-slice.{md,csv}` and
blanks `human_verdict`. **Re-running it destroys the completed verification.**
The filled CSV is backed up at
`work/halluc/backups/hallucination-human-slice.filled.csv`; restore from there
before re-running anything that touches the slice.

The completed sheet in `reports/hallucination-human-slice.md` was round-tripped
through an external editor and its markdown escaping/code fences are damaged.
The verdicts were extracted from it into the CSV, which is the system of record.

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
(No id in the final 46 is ambiguous across arms; the human/machine join above
is keyed by the (`arm`, `judgment_id`) pair regardless.)

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

Deviations 1 and 2 are candidate explanations for the unreliability the human
slice found, alongside self-evaluation bias. This study cannot separate them.
