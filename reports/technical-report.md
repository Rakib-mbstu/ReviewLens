# ReviewLens — technical report

**An LLM code reviewer evaluated against historical human review comments on
merged Java pull requests, and the two LLM judges that did the evaluating.**

Mir Rakibul Islam · September 2026

---

## Summary

ReviewLens reviews Java pull requests with an LLM and measures the result
against what human reviewers actually said on those same PRs. It was built to
answer three questions: how much of human review an LLM reproduces (RQ1), how
often it invents problems (RQ2), and whether either varies by model (RQ3).

The measured answers are small numbers with wide intervals. **Recall against
human review comments is 1.6%** on the full 90-PR corpus for the one model a
$1 budget could afford end to end, and **1.0% / 1.0% / 4.9%** for three models
on a 30-PR subset, with no pair separated at p < 0.05. Neither RQ1 nor RQ2
distinguishes the three arms.

The result worth reading is not in that table. Both of the metrics above are
produced by **LLM judges applying frozen rubrics**, and this study checked both
against a human rater. They did not fare the same way:

| judge | what it decides | human check | outcome |
|---|---|---|---|
| `match_v1` | is this model comment the same issue as this human comment? | census, all 8 matches, blind | **7/8 upheld (87.5%)** — usable |
| `hallucination_v1` | does the visible code support this model comment? | 46-judgment stratified blind slice | **20/46 agree (43.5%), κ = 0.046** — chance level |

Two judges, one pipeline, the same freeze-and-version discipline, the same
"deterministic" claim on the tin. One is a measurement instrument and the other
is not, and **nothing except the human check could tell them apart.** The
hallucination screen had already produced a clean, decisive, highly significant
per-arm separation (36.2% vs 2.0% vs 0.0%, Fisher exact p = 3.3×10⁻⁷) before it
was checked. That result is retracted.

If this report has one claim to make, it is that **an LLM-as-judge metric
reported without a human validation slice is not a measurement**, and that the
cost of finding this out was 46 hand-rated judgments.

---

## 1. Research questions

As posed at the start:

1. **RQ1 — Recall.** What fraction of human review comments does the LLM
   reviewer also raise, overall and by comment category?
2. **RQ2 — Hallucination.** What fraction of LLM comments are incorrect or
   unfounded?
3. **RQ3 — Model sensitivity.** How do results vary across model capability
   tiers?

As answered:

1. **RQ1: 1.6%** (5/318) on the full corpus for `qwen3-coder-30b`; 1.0–4.9%
   across three models on a 30-PR subset. Per-category recall exists but sits
   on single-digit numerators. Answered, with the caveat in §5.
2. **RQ2: not answered.** The instrument built to answer it failed validation.
   What RQ2 produced instead is a negative result about the instrument, plus an
   upper bound (the unmatched rate, 99.8%) that is far too loose to be
   interesting.
3. **RQ3: no significant difference** on the available corpus, on either
   metric, and the arms are confounded by delivery channel (§4.4).

---

## 2. Corpus

90 merged pull requests, 30 from each of **JUnit 5**, **Mockito** and
**Checkstyle**, carrying **328 top-level human review comments**.

A PR qualifies when it is merged, is not bot-authored, touches Java files,
stays under a size cap (≤50 changed files, ≤2000 changed lines) and carries
**≥2 substantive human review comments**, where substantive means ≥30
characters after quoted text and code fences are stripped, excluding bots and
the PR author's own comments. The criteria are recorded in
`data/corpus/manifest.json`, and the PR list is pinned.

**One review thread counts as one human finding.** Only thread-opening comments
enter RQ1's denominator; replies (`in_reply_to_id` set) continue a discussion
rather than raise a new issue and are not independently matchable. Replies were
35% of raw qualifying comments on a first mining run, so counting them would
have depressed measured recall by up to a third — a methodological choice worth
stating because it moves the headline number substantially.

Category distribution over the 328 (assigned by LLM against a frozen rubric,
see §5.3): `design` 150, `style` 82, `question` 52, `bug` 34.

Reviews run on the **pre-review state** — the code as it existed when the human
reviewers saw it (`pre_review_sha`), never the merged state. PRs with
force-pushed histories, where that state cannot be reconstructed, are excluded.
Evaluating on the post-review state would leak the reviewers' fixes into the
model's input and contaminate recall.

---

## 3. System

```
GitHub PR ──► Ingestion ──► Chunking ──► Review engine ──► structured comments
              (pre-review    (per-file    (frozen prompt,     {file, line,
               diff + file     hunks +     one LLM call        category,
               context)        context)    per chunk)          severity, comment}
```

- **Chunking**: per-file hunks with 10 lines of context. Each chunk is rendered
  with new-side line numbers and `+`/`-`/context markers, so the model can
  anchor a comment to a line the matcher can later find.
- **Review prompt**: `prompts/review_v1.md`, frozen 2026-08-12, sha256
  `3cf6f21e…`, `temperature: 0.0`. It instructs the reviewer to flag only what
  it is confident about, to judge only what is visible in the chunk, and to
  emit a JSON array. It has not been edited since the freeze; a change would
  mean a `review_v2.md` and would invalidate cross-arm comparison.
- **Client**: a thin swappable wrapper over OpenRouter. The model id is always
  a parameter. Every response is cached, keyed on the full request, so a warm
  re-run costs $0.
- **Provenance**: every run directory carries `run_meta.json` (model, prompt
  name/version/sha256, params, corpus, start/finish, delivery channel,
  exclusions) and the raw request/response bytes for every chunk. A report can
  be reproduced from a run directory alone.

Unparseable replies are counted rather than hidden. The parser recovers what it
safely can; the remainder goes to the run's `errors.json` and is reported as a
per-model parse-failure rate, because a lost chunk depresses recall for reasons
unrelated to review ability.

---

## 4. Results

### 4.1 RQ1 — recall (full corpus, one model)

`qwen/qwen3-coder-30b-a3b-instruct`, 87 of 90 PRs completed before the
OpenRouter key expired.

| metric | value |
|---|---|
| PRs evaluated | 87 |
| Human comments (denominator) | 318 |
| Model comments | 2356 |
| Matched | 5 |
| **Recall** | **1.6%** |
| Chunk loss rate | 6/1173 = 0.5% |
| Chunks with a parse error | 11/1173 = 0.9% |

By category: `bug` 2/34 (5.9%), `question` 1/52 (1.9%), `style` 1/82 (1.2%),
`design` 1/150 (0.7%). Five matches spread over four categories is not a
per-category result; it is four numerators of ≤2.

**All 5 of these matches were checked by a human, and all 5 held** (2026-09-04,
census not sample, blind to the judge's verdict and reason;
`reports/match-verification-full87.csv`). The 1.6% is therefore not a judge-only
number: 5/5 upheld, 100% [56.6–100] Wilson, so recall is unchanged at 5/318.
The interval is what n = 5 allows — this establishes the matcher is not
producing spurious matches at any appreciable rate on this run, not that its
precision is 100%. §5.2 has the limits, which are real.

### 4.2 RQ3 — three models, shared 30-PR subset

All arms reviewed the same 30 PRs (102 human comments) through the same frozen
prompt, chunker and matcher. `Matched` is human-corrected: all 8 matches were
hand-checked (§5.2).

| Arm | Via | Model comments | Matched | Recall | 95% CI | p vs lowest |
|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | OpenRouter | 816 | 1 | 1.0% | [0.2, 5.3] | — |
| `anthropic/claude-sonnet-5` | subagent | 76 | 1 | 1.0% | [0.2, 5.3] | 1.000 n.s. |
| `claude-code-subagent/opus` | subagent | 249 | 5 | 4.9% | [2.1, 11.0] | 0.212 n.s. |

**Volume is not capability.** qwen wrote **816** comments to opus's **249** and
sonnet-5's **76**, and finished with the fewest matches per comment: 0.1% for
qwen against 2.0% for opus. Sixteen times the output for one fifth of the
matches. A tool that comments everywhere will look productive and be useless,
and the unmatched rate is where that shows up.

**Reachability** — human comments with at least one model comment inside the ±3
window, the ceiling recall could reach if the judge accepted every pair — is
36/102 (qwen), 28/102 (opus), 8/102 (sonnet-5). qwen looked in the right place
three times as often as it converged with the human, and sonnet-5 mostly did
not look at all.

### 4.3 RQ2 — the hallucination screen, and its retraction

The unmatched rate is 99.8% (2351/2356 on the full run). That is an **upper
bound** on hallucination and nothing more: a model comment matching no human
comment may be a real issue the reviewers never raised. Separating the two
requires a judgment against the code.

That judgment was built. Each arm's unmatched comments were sampled at ≥20%
(deterministic seed) and screened against frozen `hallucination_v1` by a second
model, which saw **exactly the diff chunk the reviewer saw** — recovered
byte-for-byte from the stored raw request — and nothing else: no Java sources,
no PR pages, no web, enforced in the wrapper and audited across all nine judge
transcripts afterwards. 227 judgments, 0 parse failures. The rubric has three
verdicts: `founded`, `unfounded`, and `unverifiable` for "this chunk cannot
settle it", so undecidable cases are neither flattering nor condemning.

What the screen reported:

| arm | judged | founded | unfounded | unverifiable | unfounded / judged |
|---|---|---|---|---|---|
| qwen | 163 | 62 | 59 | 42 | **36.2%** [29–44] |
| sonnet-5 | 15 | 13 | 0 | 2 | **0.0%** [0–20] |
| opus | 49 | 37 | 1 | 11 | **2.0%** [0–11] |

Fisher exact: qwen vs opus p = 3.3×10⁻⁷; qwen vs sonnet-5 p = 0.0028.

This was, briefly, the study's headline: RQ2 separates the models decisively
where RQ1 cannot. **It is retracted.** §5.1 is why.

### 4.4 Confounds carried by the table

Two, both recorded rather than smoothed over.

**Delivery channel.** The $1 OpenRouter budget could not fund a Claude pass — a
full 90-PR run prices at $5–13 per model — so the Claude arms were driven
through Claude Code subagents. To keep the treatment comparable, the *real*
engine was driven via an `OfflineClient`: identical chunks, identical prompt
bytes, identical parser. What could not be made identical is the channel: no
temperature control, and the harness's own system prompt wrapping every call.
Every run records `via`, and the comparison table prints it. A gap between an
API arm and a subagent arm mixes model capability with delivery channel and
cannot be attributed to capability alone.

**Scaffolding is part of the treatment.** While building the subagent arms, an
early wrapper restated `review_v1`'s "flag only what you are confident about"
rule in its own words. That one redundant sentence cut the model's output rate
by roughly **3×** — on comment volume, which feeds the unmatched rate and
therefore RQ2. The wrapper was reduced to pure mechanics (which file to read,
which to write) and made byte-identical across every batch and both arms.
Anyone evaluating an LLM through an agent harness should assume their
scaffolding is a treatment variable until they have shown it is not.

---

## 5. The measurement instruments

Everything above rests on LLM judgments. This section is the part of the study
that produced a durable result.

### 5.1 `hallucination_v1` — failed

**Design of the check.** 46 judgments, seed 20260826, drawn stratified rather
than uniformly: oversampled toward the two cells where a biased judge does the
most damage — Claude-arm `founded` (excusing a weak Claude comment) and qwen
`unfounded` (condemning a sound qwen comment). Both directions were registered
as hypotheses *before* the slice was rated, because the screening judge is a
Claude model and two of the three arms are Claude models, which is exactly the
shape self-evaluation bias would take. The sheet was rendered without the
machine's verdict, from the same chunk and the same frozen rubric.

**Result.** Agreement **20/46 = 43.5%**, Cohen's **κ = 0.046** (p_o = 0.435,
p_e = 0.407). Restricting to the 27 judgments where both sides were decisive:
18/27 = 67%, **κ = −0.008**. Collapsing the third category does not rescue it.

| machine \ human | founded | unfounded | unverifiable |
|---|---|---|---|
| **founded** | 17 | 3 | 8 |
| **unfounded** | 6 | 1 | 5 |
| **unverifiable** | 2 | 2 | 2 |

**The load-bearing cell.** The 36.2% headline rests on 59 qwen comments the
machine called `unfounded`. Twelve of those 59 were drawn at random and the
human upheld **one** — 1/12 = 8% [1–35]. At that rate roughly 5 of the 59
survive scrutiny.

**Both pre-registered bias directions moved as predicted**: the judge
over-credited the Claude arms (7 of 20 `founded` verdicts did not hold) and
over-condemned qwen (11 of 12 `unfounded` verdicts did not hold). Stated
carefully, the **directional asymmetry alone is not significant** — among the 9
flat `founded`↔`unfounded` contradictions, 3 went one way and 6 the other,
McNemar exact p = 0.508. The finding that stands independently is the collapse
of the qwen `unfounded` cell, which holds regardless of mechanism.

**Confidence did not help.** The judge's `high`-confidence verdicts agreed with
the human 13/26 (50%); its `low`-confidence ones 7/20 (35%). Better ordered than
chance, and still a coin flip where it claimed certainty.

**The chunk-only constraint binds harder than the judge admitted.** The human
used `unverifiable` 2.5× as often on the same 46 (15 vs 6). The judge resolved
genuinely undecidable cases rather than declining them — in both directions.

Reweighting the human labels back onto each arm (post-stratified, with
stratified variance and a finite-population correction) gives roughly 11.6% /
10.8% / 14.4% for qwen / opus / sonnet-5, every interval covering every other
arm's point estimate. **These are not offered as the RQ2 result.** They rest on
6–14 draws per cell, and 12 of opus's 49 judgments and 2 of sonnet-5's 15 have
no human coverage at all, which flatters the Claude arms; imputing those at the
rate observed in qwen's `unverifiable` cell moves opus to 19.0% and sonnet-5 to
18.9%. The defensible reading is that after verification **RQ2 does not separate
these three arms**, for the same reason RQ1 does not.

The screen's failure has at least three candidate causes this study cannot
separate: self-evaluation bias, batched judging (227 judgments ran as 9
subagent batches, so within a batch one judgment could influence another —
the wrapper instructed against it, and instruction is not isolation), and the
absence of temperature control on the subagent channel.

### 5.2 `match_v1` — held

Because the other judge failed, the matcher — which every RQ1 number depends on
— could not be assumed sound just because it was frozen and deterministic.

There are only 8 matches across the three subset arms, so this was a **census,
not the ≥20% sample**: the rule would have drawn 4, and sampling error is not
worth carrying when the population fits on one page.

The sheet was **blind to the arm** (ids `M1`–`M8` in seeded shuffle order,
seed 20260831; no model named in the sheet or the response CSV) and blind to
the judge's verdict, and **pass 1 showed exactly what `match_v1` saw** — the
two comments and their lines, no code. Judging the judge on evidence it never
had would measure the rater's extra information instead of the judge's
accuracy.

**Result: 7 of 8 upheld, 87.5% [52.9–97.8].** One opus match (category
`design`) was rejected, moving opus from 5.9% to 4.9% and its design recall
from 3/50 to 2/50. opus vs qwen was not significant before (p = 0.119) and is
not significant after (p = 0.212): verification moved the point estimate, not
the conclusion.

**Provenance, stated because it matters.** The 8 verdicts were not all produced
under blind conditions. All 8 were rated blind; the verdicts were then joined to
the key and the arms disclosed — at which point the rater learned that all three
rejections were opus and that they halved its recall. Two of those three (`M7`,
`M8`) were subsequently revised to `equivalent`, both moving the result the same
way.

| | matcher upheld | opus recall | opus vs qwen |
|---|---|---|---|
| blind pass, as first recorded | 5/8 = 62.5% [30.6–86.3] | 2.9% (3/102) | p = 0.621 |
| final, after revision | 7/8 = 87.5% [52.9–97.8] | 4.9% (5/102) | p = 0.212 |

Both rows are reported and both are reproducible from committed CSVs
(`reports/match-verification-joined{,-blind}.csv`). The revisions may well be
reconsideration on the merits — `M8`'s model comment does name the missing
`@deprecated` tag the human asked for — but they were made with the arm known,
so 87.5% is not a blind measurement and is not presented as one. The blind row
has the stronger provenance; the final row is the rater's considered judgment.

**One rater inconsistency, left split deliberately.** `M1` and `M4` are the
*same human comment* — mockito#3129 line 58, where the PR adds an abstract method to the
published `MockitoPlugins` interface — matched independently by opus and by
sonnet-5, and included as a built-in consistency check on the rater. They
received opposite verdicts: `M1` (opus) `not_equivalent`, `M4` (sonnet-5)
`equivalent`. Both model comments identify a new abstract method on a published
interface breaking downstream implementors, and both propose a default method;
`match_v1` treats differing wording and differing proposed fixes as *not*
grounds for rejection. The rater elected to keep them split after the
inconsistency was raised on 2026-08-31, and that is a decision rather than an
omission: harmonizing the pair with the arms already disclosed would have been a
third post-hoc revision of exactly the kind that already costs 87.5% its blind
provenance, and it is not neutral in either direction — if `M1` were
`equivalent` the matcher upheld 8/8 and opus stays at 5.9%; if `M4` were
`not_equivalent`, sonnet-5 drops to 0/102. The pair was the only built-in check
on rater consistency this study ran, and it returned a real result: on the
hardest case in the set, one rater is not self-consistent. That is kept as data,
and it argues for a second rater independently of κ = 0.046. See
`reports/match-verification-results.md`.

**The full-corpus census, added 2026-09-04.** The paragraphs above cover the
30-PR subset. The full 87-PR qwen run has its own 5 matches — the ones behind
the 1.6% headline — and they were left unverified by the 2026-09-02 decision.
That decision was reopened for this item alone and the same procedure was run
again: census not sample, seed 20260904, blind to the judge's verdict and
reason, pass 1 showing only the two comments and their lines.

**Result: 5 of 5 upheld, 100% [56.6–100].** Recall is unchanged at 5/318 =
1.6%, and it is no longer a judge-only number. Across both censuses 12 of 13
verdicts were upheld, on 12 distinct comment pairs — the two sheets overlap by
one, see below.

Three things this second census does **not** inherit from the first, and one it
adds:

- **There was no arm to blind.** One run, one model. The judge's verdict and
  reason were still withheld, which is the blind that makes human-vs-judge
  agreement mean anything, but the arm-blinding that gave the subset30 sheet
  its provenance has no analogue here.
- **No verdict was revised.** The subset30 figure needs two rows (blind 5/8,
  final 7/8) because two verdicts changed after unblinding. This pass was taken
  once and never revisited, so one number is the whole record — the stronger
  provenance of the two.
- **n = 5, and the interval runs from 56.6% to 100%.** It establishes the
  matcher is not producing spurious matches at any appreciable rate on this
  run. It does not pin its precision, and like the subset30 census it measures
  precision only: every one of the 5 is a judge-`equivalent` verdict, so
  **false negatives remain entirely unbounded**.
- **It contains an accidental repeat, and the repeat was consistent.** Sheet id
  `M3` here (mockito#2650, `StrictnessMockAnnotationTest.java`, human line 39,
  model line 38) is the *same comment pair* as `M2` in the subset30 sheet —
  the same PR appears in both the subset and the full corpus, and qwen produced
  the same comment on it. It was rated `equivalent` on 2026-08-31 and
  `equivalent` again on 2026-09-04, unprompted and five days apart. That is the
  study's second unplanned rater-consistency check, and unlike `M1`/`M4` it came
  out consistent. One hit and one miss on two repeats is not a reliability
  estimate; it is two data points, and they disagree with each other about
  whether the rater is self-consistent.

Both censuses share the limits that matter most: **a single rater, who is the
study's author, and no adjudication.** Neither figure is an inter-rater
agreement, and neither can be.

**What this check cannot tell you.** All 8 subset30 verdicts and all 5
full-corpus verdicts are judge-`equivalent`, so both censuses measure
**precision, not agreement** — a non-match never becomes a match, there is
nothing to compute a κ against, and **false negatives are entirely unbounded**.
Human comments the matcher wrongly declined would push recall *up*, and nothing
in this study bounds how many there are. On the subset30 sheet n = 8 and 6 of
the 8 are opus, so that one is close to a check on a single arm.

### 5.3 `categorize_v1` — checked against a model, never against a human

Each human comment's category is assigned by one LLM call against a frozen
four-way rubric (`bug` / `design` / `style` / `question`); a comment fitting
none is recorded at low confidence rather than given a fifth category. A
reproducible ≥20% sample (66 of 328, seed 20260823) was re-rated by a **second,
independent model** driven through the same frozen rubric and the same renderer
via `OfflineClient`, so the prompt bytes are identical.

Agreement **54/66 = 81.8%** [70.9–89.3], Cohen's **κ = 0.70**. Rater 2 is
substantially the more capable model, so this is closer to adjudication of a
weak rater by a strong one than to symmetric inter-rater agreement — and
nothing here establishes that rater 2 is right. **No human validated these
labels.** Seven of the 12 disagreements are the `design`/`style` boundary, the
same seam that produced 16% label churn (51 of 328) between two rubric
versions.

**The `confidence` field is inert.** Rater 1 marked 63/66 assignments `high`
(95%); rater 2, on identical prompts, marked 34/66 `low` (52%). Rater 1's
`high`-confidence labels agree with rater 2 only 84% of the time. The rubric
routes low confidence to human spot-checking, and rater 1 used that escape
hatch 3 times in 66 — the mechanism never fired. The same defect appeared
independently in `hallucination_v1` (§5.1), where `high` confidence
coin-flipped. **Self-reported confidence from an LLM judge was uninformative in
both instruments in this study** — two independently built judges, two
different rubrics, the same defect. That is a recurrence worth a reader's
attention, not a general law: n = 2.

A human pass over this sample was started and abandoned after 9 of 66. Its
labels are preserved verbatim but unscored: they used a vocabulary outside the
frozen four (`Doc`, `Practise`), so disagreement against a rubric that forbids a
fifth category would be guaranteed by construction rather than informative. That
the labeller reached for two categories the rubric does not have is itself weak
evidence the four-category taxonomy does not cleanly cover this corpus.

---

## 6. Why recall is this low

Three explanations were separated rather than assumed.

**It is not the matching window.** The ±3-line rule is the obvious suspect: a
narrow window could reject matches the semantic judge would have accepted, and
the judge would get credit for the window's strictness. Re-matching the full
qwen run at ±5, ±10 and ±25 makes **104 more human comments reachable**
(127 → 231 of 318, 40% → 73%) and costs 284 extra judge calls, and yields
**zero** additional matches. Recall is flat at 1.6% across an eightfold
widening. The models are raising *different issues*, not the right issues in
the wrong place.

**A structural ceiling accounts for some of it.** On the 30-PR subset, 11 of
102 human comments (11%) sit on files the chunker never produced a chunk for —
9 of them on files outside the PR's changed Java set entirely (comments on
build files, or on files the PR removed). Those are unreachable before any
model runs, for every arm equally. On the full corpus the figure is 35/318
(11%).

**The rest is disagreement about what is worth saying.** Reachability minus
recall is the gap: opus had a model comment within ±3 lines of 28 of the 102
human comments and converged with the human on 5. The models are commenting on
the same code the humans commented on, and saying something else about it.

There is a fourth possibility this study cannot exclude: that human review
comments are a poor ground truth for "issues in this diff". Reviewers miss
things, comment on what happens to catch their eye, and raise matters of local
convention no model could anticipate. Recall against human comments measures
**agreement with humans**, not absolute defect detection, and a low number is
consistent with both a weak reviewer and a badly-posed target.

---

## 7. Threats to validity

**Construct.** Recall against historical human comments is agreement, not
defect detection (§6). The `unmatched` rate is an upper bound on hallucination
that the failed screen never converted into a measurement. Category labels are
LLM-assigned and human-unvalidated, so per-category recall inherits that
uncertainty on top of single-digit numerators.

**Internal.** Two frozen LLM judges, one validated as usable and one not. The
matcher's validation covers precision only and leaves false negatives
unbounded. The match verification's final row was produced after unblinding.
The category rubric is only self-consistent, not verified. The three arms differ
in delivery channel as well as model.

**Statistical.** 102 human comments in the shared subset, and matched counts of
1, 1 and 5. Every reported interval is wide, every pairwise comparison is
non-significant, and this report avoids ordering the arms anywhere. The
reweighted RQ2 estimates rest on 6–14 draws per cell and are marked do-not-cite
in place.

**External.** Java only; three mid-size OSS projects with an active review
culture; first-pass review only, where real review is conversational; 90 PRs.
Nothing here should be assumed to transfer to other languages, proprietary
codebases, or monorepos.

**A model id does not pin down who served the request.** OpenRouter routes a
model to one of several upstream providers and they are not interchangeable:
two providers were observed returning a billed completion with `content: null`
and `finish_reason: "stop"`, which the pipeline would otherwise have recorded as
that *model* failing to produce parseable output. Such replies are now retried
rather than cached, and every run records which providers answered (SiliconFlow
739, Novita 391, Alibaba 43 on the full qwen run), so a provider-side defect
cannot be read as a model-capability difference. On that run, 8 of the 14
malformed items were provider-caused and 6 model-caused.

**Verification depth.** One rater, no adjudication pass, no second human
anywhere in the study. κ = 0.046 establishes that the hallucination screen is
unreliable; it does not establish which side is right.

---

## 8. What is not done, and what was decided against

Stated plainly rather than left for a reader to discover. Most of what follows
is **deferred by decision, not pending**. On 2026-09-02 the verification effort
was stopped: the items marked † were each within reach — their tooling is
committed and their procedure is written up in §5 — and were closed unfilled
anyway. They are properties of these results rather than work in progress, and
what each one costs the study is stated with it.

One item was reopened. On 2026-09-04 the full-corpus census was run after all,
on the argument that the 1.6% was the most-quoted number in the study and the
only headline with no human check, and that five rows is an hour rather than an
afternoon. The rest of the 2026-09-02 decision stands.

- ~~**The full-corpus 1.6% has no human verification.**~~ **Closed 2026-09-04.**
  The 2026-09-02 decision was reopened for this one item and the census was
  run: all 5 matches checked, all 5 upheld (§5.2). The headline no longer rests
  on a judge alone. What remains is the size of the check — n = 5, one rater,
  no adjudication, and pass 2 still unrated.
- † **The category spot-check has no human labels.** 66 rows exported, 0 filled.
  The second rater is a model, so every per-category recall figure inherits an
  unchecked model-vs-model labelling.
- **RQ2 has no verified per-arm rate.** It has a retracted machine estimate, an
  indicative reweighting marked do-not-cite, and a negative result about the
  instrument. Closing this needs a second rater, not more of the same one.
- † **Pass 2 of the match verification** (does the *code* support the match, not
  just the two comments) was designed and exported but not rated. The 87.5%
  therefore says the two comments agree, not that either is right about the code.
- † **The hallucination slice has a coverage gap**: the `unverifiable` stratum's 6
  draws all landed on qwen, so the Claude arms' `unverifiable` verdicts went
  unsampled entirely — which is why the reweighted rates are marked do-not-cite.
- **`usefulness score` is not implemented.** It appears in the metrics design
  and was never built.
- **Only one model ran the full corpus.** The 30-PR subset cannot separate 1%
  from 5%, and it is the only shared denominator the three arms have. This one
  is not the verification decision — it is orchestration cost, and it is the
  single change that would most improve the study.

---

## 9. What I would do differently

1. **Validate the judge before reporting anything it produces.** The
   hallucination screen ran to 227 judgments, produced a p = 3.3×10⁻⁷ result,
   and was written up before a single human verdict existed. The 46-judgment
   slice that dismantled it took an afternoon. It should have been the first 46
   judgments, not the last.
2. **Never trust a judge's self-reported confidence.** Both instruments here
   emitted a confidence field, both fields were uninformative, and one was
   wired to a human-escalation mechanism that consequently never fired.
3. **Blind the rater to the arm from the start.** The hallucination sheet
   printed the model name; the match sheet did not, and the match sheet is the
   one whose provenance survives scrutiny. Unblinding after the fact cost this
   study a clean 87.5% — the number is now reported in two rows instead of one.
4. **Budget the denominator, not the model list.** Three arms on 102 human
   comments cannot separate 1% from 5%. One arm on 328 would have said more
   than three arms on 102.
5. **Treat the harness as a treatment variable.** A single redundant sentence
   in a wrapper moved output volume 3×.
6. **Make the response file non-destructive on day one.** The hallucination
   slice builder rewrites its CSV blank on every run and came within one command
   of destroying a completed verification pass.

---

## 10. Reproducing this

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=...   # LLM calls
export GITHUB_TOKEN=...          # read-only, mining

python -m reviewlens.mine   --projects junit5 mockito checkstyle --out data/corpus/
python -m reviewlens.eval.categorize --corpus data/corpus/ --model <model-id> \
    --spotcheck-out reports/categorization-spotcheck.csv
python -m reviewlens.review --corpus data/corpus/ --model <model-id> --out runs/<model-id>/
python -m reviewlens.eval   --run runs/<model-id>/ --judge-model <model-id> \
    --report reports/<model-id>.md
python -m reviewlens.eval.export_verification --run runs/<model-id>/ \
    --out reports/<model-id>-verification.csv
python -m reviewlens.eval.sensitivity --run runs/<model-id>/ --judge-model <model-id> \
    --windows 3,5,10,25 --report reports/<model-id>-sensitivity.md
python -m reviewlens.eval.compare --runs runs/<a>/ runs/<b>/ --judge-model <model-id> \
    --verified reports/match-verification-joined.csv --report reports/rq3-comparison.md
```

`--verified` takes a verification CSV with `human_verdict` filled in; human
verdicts override the judge's on the match judgments they cover, and the table
reports how much of each arm carries a human verdict. Without the flag the
table says in plain text that no human verified it.

**Replaying this study needs no API key and no money, but it does need the
artifacts.** `runs/`, `cache/` and the mined corpus under `data/` are gitignored
— the first two are build products and the third is 90 PRs of raw GitHub data
that a pinned PR list plus a mining script records better than a git blob — so a
clone alone cannot replay anything. They ship as a 3.1MB bundle on the v0.1.0
release, checksummed and fetched by:

```bash
bash work/demo/fetch_artifacts.sh
```

With that in place the evaluation replays offline: every judge and reviewer call
these runs made is in the cache, and the client defers its API-key check to the
first call that misses it, so the whole eval runs byte-identical with no
OpenRouter account. The one stage still needing credentials is ingestion, which
fetches each PR's pre-review diff from GitHub and therefore wants a read-only
`GITHUB_TOKEN`.

260 unit tests cover chunking boundaries, the matching rule, cache-key
stability, metric computation and the verification join; none of them call a
live API, and they need no artifacts.

### Artifact index

| file | what it holds |
|---|---|
| `reports/qwen3-coder-30b-a3b-instruct-full87.md` | RQ1, full corpus, one model — the judge's own counts |
| `reports/qwen3-coder-30b-a3b-instruct-full87-verified.md` | the same run with the 5 human verdicts applied |
| `reports/rq3-comparison-subset30.md` | RQ3 table, human-corrected |
| `reports/qwen3-coder-30b-line-window-sensitivity.md` | ±3/5/10/25 sweep |
| `reports/hallucination-screen.md` | RQ2 screen and its retraction |
| `reports/hallucination-human-slice.{md,csv}` | the 46 human verdicts |
| `reports/match-verification-results.md` | both matcher censuses, 13 verdicts |
| `reports/match-verification.{md,csv}` | subset30 blind sheet and its verdicts |
| `reports/match-verification-joined{,-blind}.csv` | subset30 final and blind passes, joined |
| `reports/match-verification-full87.{md,csv}` | full-corpus blind sheet and its verdicts |
| `reports/match-verification-full87-joined.csv` | full-corpus pass, joined |
| `reports/categorization-interrater.md` | two models on the category rubric |
| `prompts/*.md` | the four frozen prompts, with freeze dates and hashes |

---

## 11. Related work

ReviewLens sits in the AI4SE / LLM4Code literature on automated code review —
review comment generation, review automation benchmarks, and the growing body
of work using LLMs as evaluators of other LLMs. Two choices distinguish it.

First, **the evaluation target is historical human comments on real merged
PRs**, not a synthetic benchmark or a curated defect set. That makes the metric
harder to game and harder to interpret in equal measure: §6 argues the low
recall is partly a property of the target, not only of the reviewers.

Second, **the judges are themselves treated as objects of study.** LLM-as-judge
is now routine in this literature, usually reported with an agreement statistic
if at all. Here two judges from the same pipeline, built to the same standard,
were validated against a human and came apart: one upheld on 7 of its 8
decisions, the other agreeing at κ = 0.046. That gap is invisible without the
human slice, and it is the finding this artifact would want a reader to take
away.

---

## 12. Conclusion

An LLM reviewer reproduces on the order of **1–5%** of what human reviewers say
on real merged Java PRs, and widening the matching window eightfold does not
move that number: the models comment on the same code and say different things.
No model tier tested separates from another at this corpus size, on either
metric.

The hallucination rate this study set out to measure as a first-class metric
**was not measured**. The instrument built for it produced a clean, significant,
publishable-looking separation and then agreed with a human rater at chance
level. Its sibling instrument, built to the same standard in the same pipeline,
held at 7 of 8.

Frozen, versioned, deterministic, rubric-driven, hash-pinned — the discipline
that makes an LLM judge *reproducible* did nothing to make it *correct*, and
was equally satisfied by the judge that worked and the one that did not. The
46 hand-rated judgments that told them apart are the cheapest and most load-
bearing part of this study.
