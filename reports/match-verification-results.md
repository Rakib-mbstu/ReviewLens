# RQ1 — human verification of the matcher (census, all 8 matches)

**Result: 7 of 8 matches upheld (87.5%, 95% Wilson 52.9–97.8).** One opus match
was rejected. Subset-30 recall moves from 5.9% to **4.9%** for opus; qwen and
sonnet-5 are unchanged at 1.0%.

Unlike the hallucination screen, **the matcher survived its check.** That
contrast is the point of running both: `match_v1` and `hallucination_v1` are
both frozen LLM judges in the same pipeline, and only one of them turned out to
be a usable instrument.

## Why a census rather than the ≥20% sample

The three 30-PR arms produced 8 matches in total (opus 6, sonnet-5 1, qwen 1).
The ≥20% rule would have sampled 4. At that population there is no reason to
carry sampling error, so every match was verified.

The motivation was RQ2. The hallucination screen — the *other* frozen LLM judge
in this pipeline — agreed with the human rater at chance level (κ = 0.046, see
`reports/hallucination-screen.md`). A frozen, deterministic, rubric-driven judge
is not thereby a correct one, and the matcher had never been checked. Every RQ1
number in the study rests on these 8 decisions.

## Design

`work/match/build_match_sheet.py`, seed 20260831.

- **Blind to the judge and to the arm.** Sheet ids are `M1`–`M8` in seeded
  shuffle order; neither the sheet nor the response CSV names a model. The
  hallucination slice printed the arm, which lets a prior about which model is
  better leak into the verdict. The id → (arm, judgment_id) map is
  `work/match/match_sheet_key.json`, joined after the fact.
- **Pass 1 shows exactly what `match_v1` saw**: the two comments and their
  lines, no code. Judging the judge on evidence it never had would measure the
  rater's extra information rather than the judge's accuracy.
- **Pass 2 (`reports/match-verification-chunks.md`)** adds the diff chunk, in a
  separate file so pass 1 stays blind. It answers the different question of
  whether the match is *real*.
- **The builder refuses to overwrite a CSV that already carries a verdict.**
  `build_human_slice.py` rewrites its response CSV blank on every run, which
  came close to destroying a completed verification pass.

The ±3-line rule is applied mechanically by the matcher before the judge is
called, so judge and human both ruled on semantic equivalence alone.

## Results

| arm | as published | after verification | 95% Wilson |
|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | 1.0% (1/102) | 1.0% (1/102) | [0.2–5.3] |
| `anthropic/claude-sonnet-5` | 1.0% (1/102) | 1.0% (1/102) | [0.2–5.3] |
| `claude-code-subagent/opus` | **5.9%** (6/102) | **4.9%** (5/102) | [2.1–11.0] |

The rejected match was `design`, so opus's per-category design recall moves
3/50 → 2/50 (4.0%). Bug recall stays 0/14 for every arm.

opus vs qwen was not significant before (Fisher exact p = 0.119) and is not
significant after (**p = 0.212**). Verification did not change that conclusion,
only the point estimate.

## Provenance of the verdicts — stated because it matters

The 8 verdicts were not all produced under blind conditions, and the report
would be misleading without saying so.

| | matcher upheld | opus recall | opus vs qwen |
|---|---|---|---|
| **blind pass, as first recorded** | 5/8 = 62.5% [30.6–86.3] | 2.9% (3/102) | p = 0.621 |
| **final, after revision** | 7/8 = 87.5% [52.9–97.8] | 4.9% (5/102) | p = 0.212 |

Sequence: all 8 were rated blind. The verdicts were then joined to the key and
the arms disclosed — at which point the rater learned that all three rejections
were opus and that they halved its recall. Two of those three (`M7`, `M8`) were
subsequently revised to `equivalent`. Both revisions moved the result in the
same direction.

The revisions may well be reconsideration on the merits; `M8`'s model comment
does name the missing `@deprecated` tag the human asked for. But they were made
with the arm known, so the 87.5% figure is not a blind measurement and should
not be presented as one. **Both rows above are reported; the blind row is the
one with the stronger provenance, and the final row is the rater's considered
judgment.** A reader should be able to see which is which.

## Unresolved rater inconsistency (`M1` / `M4`)

`M1` and `M4` are **the same human comment** — mockito#3129 line 58, where the
PR adds `MockMaker getMockMaker(String mockMaker);` to the public
`MockitoPlugins` interface — matched independently by opus and by sonnet-5.
This is the "convergent detection" noted in the study's findings, and it was
included as a built-in consistency check on the rater.

They received opposite verdicts: `M1` (opus) `not_equivalent`, `M4` (sonnet-5)
`equivalent`. Both model comments identify a new abstract method on a published
interface breaking downstream implementors, and both propose a default method.
The rater's stated reason for hesitating on `M1` was that the wording differs
and the suggested fix may not be the same; `match_v1` treats neither as
grounds for `not_equivalent` ("even if worded differently or proposing
different fixes"). The rater elected to keep the two split after the
inconsistency was raised.

The disagreement is recorded, not resolved. Its size: if `M1` were
`equivalent`, the matcher upheld 8/8 and opus stays at 5.9%; if `M4` were
`not_equivalent`, sonnet-5 drops to 0/102.

## What this check cannot tell you

- **It measures precision, not agreement.** All 8 are judge-`equivalent`
  verdicts — a non-match never becomes a match, so there is nothing to compute
  a κ against. It says nothing about **false negatives**: human comments the
  matcher wrongly declined to match, which would push recall *up*. Nothing in
  this study bounds that.
- **n = 8.** The interval on 7/8 runs from 53% to 98%. This establishes that the
  matcher is not chance-level; it does not pin down its precision.
- **Six of the 8 are opus**, because those are the only matches that exist. This
  is close to a check on one arm.
- **The full-corpus qwen run is not covered.** `runs/qwen` (87 PRs, 318 human
  comments, recall 1.6%, 5/318) is a different run with its own 5 matches, none
  of them verified. The 1.6% headline is unchecked.
- **Pass 2 was not completed.** `verdict_with_code` is empty for all 8; the M1
  chunk was consulted during adjudication but no with-code verdicts were
  recorded.
