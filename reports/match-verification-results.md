# RQ1 — human verification of the matcher (two censuses, 13 verdicts)

**Subset30 (2026-08-31): 7 of 8 matches upheld (87.5%, 95% Wilson 52.9–97.8).**
One opus match was rejected. Subset-30 recall moves from 5.9% to **4.9%** for
opus; qwen and sonnet-5 are unchanged at 1.0%.

**Full corpus (2026-09-04): 5 of 5 matches upheld (100%, 95% Wilson 56.6–100).**
The 1.6% headline is unchanged at 5/318 and is no longer judge-only. See
[the full-corpus census](#the-full-corpus-census-2026-09-04) below.

Most of this document describes the subset30 census, which came first and is
the more intricate of the two.

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

## Rater inconsistency (`M1` / `M4`) — left split, deliberately

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

**It stays split by decision, and the reason is worth stating.** The
inconsistency was raised and adjudicated on 2026-08-31, with the arms already
disclosed. Harmonizing the pair at that point would have been a third post-hoc
revision made with the arms known — the same defect that already costs the
87.5% its blind provenance (`M7`, `M8` above), applied this time for no reason
better than removing a visible blemish. And harmonizing is not neutral
bookkeeping in either direction: if `M1` were `equivalent`, the matcher upheld
8/8 and opus stays at 5.9%; if `M4` were `not_equivalent`, sonnet-5 drops to
0/102. Each choice moves a published number.

So the pair is kept as recorded. `M1` / `M4` was included as a built-in
consistency check on the rater, it is the only such check the study ran, and it
returned a real result: on the hardest case in the set, a single rater is not
self-consistent. Overwriting that to make the table agree with itself would
discard the one measurement of rater reliability this study has — and it is a
measurement that argues, independently of the κ = 0.046 finding, for the second
rater recommended in the technical report.

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
- **The full-corpus qwen run is covered by a separate census**, run 2026-09-04
  and reported below — not by the 8 verdicts above. `runs/qwen` (87 PRs, 318
  human comments, recall 1.6%, 5/318) is a different run with its own 5
  matches. The two sheets overlap by exactly one comment pair.
- **Pass 2 was not completed.** `verdict_with_code` is empty for all 8; the M1
  chunk was consulted during adjudication but no with-code verdicts were
  recorded.

---

## The full-corpus census (2026-09-04)

The 2026-09-02 decision closed all further human verification. It was reopened
for this item alone: 1.6% (5/318) was the study's most-quoted number and the
only headline with no human check, the procedure and tooling already existed,
and the population is five rows.

**Result: 5 of 5 upheld, 100% [56.6–100] Wilson.** Recall is unchanged at
5/318 = 1.6%. Nothing moved; what changed is that the number is now checked.

| | subset30 | full corpus |
|---|---|---|
| run | 3 arms × 30 PRs (102 human comments) | qwen only, 87 PRs (318 human comments) |
| matches | 8 | 5 |
| upheld | 7 (87.5%) | **5 (100%)** |
| 95% Wilson | [52.9–97.8] | [56.6–100] |
| seed | 20260831 | 20260904 |
| blind to the arm | yes | n/a — one run |
| blind to the judge | yes | yes |
| verdicts revised after the fact | 2 (`M7`, `M8`) | none |
| rated | 2026-08-31 | 2026-09-04 |

Reproduce with the commands in `work/README.md`; the rated sheet is
`reports/match-verification-full87.csv` and the join is
`reports/match-verification-full87-joined.csv`.

### The accidental repeat

`M3` here — mockito#2650, `StrictnessMockAnnotationTest.java`, human line 39,
model line 38 — is **the same comment pair** as `M2` in the subset30 sheet. That
PR is in both the subset and the full corpus, and qwen produced the same comment
on it both times. The rater was not told, and five days separate the two
verdicts.

Both came out `equivalent`. Set against `M1`/`M4`, which are also the same
comment pair and came out opposite, the study now has two unplanned repeats and
they disagree about whether the rater is self-consistent. Two data points is not
a reliability estimate. It is, however, a better argument for the second rater
than either point alone.

### What it does not establish

- **n = 5.** The interval runs to 56.6% at the bottom. This says the matcher is
  not producing spurious matches at any appreciable rate on this run; it does
  not pin its precision.
- **Precision only, again.** All 5 are judge-`equivalent` verdicts, so there is
  no κ to compute and **false negatives stay entirely unbounded** — human
  comments the matcher wrongly declined would push recall *up*, and nothing in
  this study bounds how many there are.
- **One rater, who is the study's author, and no adjudication.** Same as the
  subset30 census. Neither is an inter-rater agreement.
- **Pass 2 was not rated here either.** `verdict_with_code` is empty for all 5;
  `reports/match-verification-full87-chunks.md` was generated and not used.
- **The rest of the 2026-09-02 decision stands.** The category spot-check, the
  match sheets' pass 2 and the hallucination slice's coverage gap are still
  closed by decision, not by completion.
