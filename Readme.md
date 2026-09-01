# ReviewLens

**An LLM-based Java pull request reviewer, evaluated against real human review comments.**

ReviewLens is both a working tool and an empirical study. Instead of demonstrating cherry-picked examples, it measures — on PRs that real maintainers reviewed — what fraction of human-flagged issues an LLM catches, what it systematically misses, and how often it hallucinates problems that aren't there.

> **Status (Sep 2, 2026):** the pipeline is complete end to end — pre-review-state ingestion (force-pushed PRs excluded), diff chunking, the review engine with a cached OpenRouter client, LLM-assisted comment categorization, comment matching, metrics, reporting, a line-window sensitivity sweep, a cross-model comparison, and the manual-verification export. **All four prompts are frozen and never edited in place:** `review_v1` (Aug 12, sha256 `3cf6f21e…`), `match_v1` (Aug 19, `ff170b79…`), `categorize_v1` (Aug 23, `bd5e4f74…`), `hallucination_v1` (Aug 26, `e05ea232…`). **The corpus is mined and its pinned PR list is committed:** 90 merged PRs (30 each from JUnit 5, Mockito, Checkstyle) carrying **328 top-level human review comments**, all of which now carry a category.
>
> **First results exist and are preliminary.** A full-corpus run of `qwen/qwen3-coder-30b-a3b-instruct` covering 87 of 90 PRs gives **1.6% recall** (5 of 318 human comments). A three-model comparison on a 30-PR subset appears in the table below; **recall differences between models are not statistically significant at this sample size**. The **hallucination screen was run (227 judgments against a frozen rubric) and then failed its own human check**: on the 46-judgment blind slice, human and machine agree 43.5% of the time (Cohen's κ = 0.046, chance level), so the screen's decisive per-arm separation is **retracted** — see `reports/hallucination-screen.md`. No model arm is currently separated from another on either RQ1 or RQ2. Numbers here are labelled preliminary and will move.

**► Full write-up: [`reports/technical-report.md`](reports/technical-report.md)** — method, results, the judge-validation result, threats to validity, and what I would do differently.

**► Demo:** `bash work/demo/demo.sh` walks the pipeline and the evaluation in ~90 seconds. It runs off the warm cache, so it costs $0 and needs no `OPENROUTER_API_KEY`. See [`work/demo/README.md`](work/demo/README.md) for recording the GIF.

## Motivation

Code review is one of the most expensive human activities in software engineering — in large teams, PRs routinely wait days for reviewer attention. LLM-based review assistants promise to absorb part of this load, but most existing tools ship without rigorous evidence about *which kinds* of review feedback they can replace and which they can't. This project is grounded in my own experience as a software engineer working in a large-team PR workflow, where review latency is a daily, measurable cost.

## Research questions

1. **RQ1 (Recall):** What fraction of human review comments on real Java PRs does an LLM reviewer independently reproduce — overall, and broken down by comment category (bug, design, style, question)?
2. **RQ2 (Precision / Hallucination):** How often does the LLM flag issues that human reviewers would judge invalid or useless?
3. **RQ3 (Model sensitivity):** How do these numbers vary across LLMs at different capability/cost tiers?

## How it works

```
GitHub PR ──► Ingestion ──► Chunking ──► Review engine ──► Markdown report
                (diff +        (per-file      (versioned         / GitHub
              file context)     hunks +        prompt, one        review
                                context)       LLM call per       comments
                                               chunk, JSON out)
```

1. **Ingestion** — pulls the PR diff and surrounding file context via the GitHub API.
2. **Chunking** — splits the diff into per-file hunks with configurable context lines, so large PRs fit the model's context window.
3. **Review engine** — a versioned prompt (prompts are markdown files with frontmatter; every result is traceable to a prompt version) produces structured comments: `{file, line, category, severity, comment}`.
4. **Output** — a markdown review report, optionally posted as GitHub review comments.
5. **Evaluation harness** — the research half (see below).

The LLM client is a thin swappable wrapper over [OpenRouter](https://openrouter.ai), so any model can be plugged in with one config change. All model responses are cached to make runs reproducible and cheap.

## Evaluation methodology

- **Corpus:** ~50–100 merged PRs that received substantive human review comments, mined from mid-size Java projects with an active review culture (JUnit 5, Mockito, Checkstyle). A PR qualifies when it is merged, is not bot-authored, touches Java files, stays under the size cap (≤50 changed files and ≤2000 changed lines), and carries **≥2 substantive human review comments** — where "substantive" means ≥30 characters after quoted text and code fences are stripped, excluding bots and the PR author's own comments.
- **One review thread counts as one human finding.** Only thread-opening comments enter RQ1's denominator; replies (`in_reply_to_id` set) continue a discussion rather than raise a new issue and are not independently matchable. On a first 90-PR mining run, replies were 35% of raw qualifying comments, so counting them would have depressed measured recall by up to a third.
- **Procedure:** ReviewLens runs on the *pre-review* state of each PR — the code as it existed when human reviewers saw it. Model comments are then matched against the historical human comments.
- **Matching rule:** a model comment matches a human comment if it targets the same file within ±3 lines *and* addresses the same underlying issue (semantic match, LLM-judged with a written rubric).
- **Line-window sensitivity:** because the ±3 window could in principle be doing the work the semantic judge is credited with, recall is also measured at ±5, ±10, and ±25 (`python -m reviewlens.eval.sensitivity`). The rule itself stays frozen at ±3 and that is the reported number; the wider windows are diagnostic. They separate two failures the headline figure fuses together — the model commenting somewhere else in the file, versus the model raising a different issue in the same place.
- **Category assignment:** each human comment's category (bug / design / style / question) is assigned LLM-assisted, one call per comment, against a frozen versioned rubric (`prompts/categorize_v1.md`) that forces a choice among exactly those four — a comment fitting none is recorded at low confidence rather than given a fifth category. A reproducible ≥20% sample of the assignments (66 of 328, fixed seed) is re-rated by a **second, independent model** (`claude-code-subagent/fable`) driven through the same frozen rubric and the same renderer via `OfflineClient`, so the prompt bytes are identical to the first pass. The two raters agree on **81.8%** of labels (54/66, 95% Wilson 70.9–89.3%, Cohen's κ = 0.70); see `reports/categorization-interrater.md`. **No human checked these labels** — the second rater is a model, so this measures inter-model consistency in applying the rubric, not correctness against human judgment. Category assignment is rubric-sensitive: two versions of the rubric disagreed on 16% of labels (51 of 328), and the residual disagreement concentrates on the design/style boundary for small local edits (removing an `else`, dropping a temporary variable), so per-category recall carries more uncertainty than overall recall.
- **Verification of judgments:** a ≥20% sample of each run's matches and unmatched model comments is exported for verification (`reviewlens.eval.export_verification`, deterministic seed). The unmatched comments in that sample are screened by a second model against frozen `hallucination_v1`; a blind, stratified human slice of those screenings is then hand-checked and the human-vs-model agreement reported. The human slice was completed Aug 31, 2026: **agreement is 20/46 = 43.5%, Cohen's κ = 0.046**, so the screened rates are contradicted rather than confirmed and the screen is not treated as a measurement instrument. The RQ1 *matches* were verified as a **census, not a sample** — all 8 matches across the three arms, blind to both the judge's verdict and the arm: **7 of 8 upheld (87.5%)**, see `reports/match-verification-results.md`. Two of the 8 verdicts were revised after the arms were disclosed; the blind-pass figure was 5/8, and both are reported.
- **Metrics:**
  - *Recall* of human comments, overall and per category (bug / design / style / question)
  - *Unfounded rate* (RQ2) — model comments making a claim the visible code contradicts, judged against a frozen rubric on exactly the chunk the reviewer saw. This is distinct from the **unmatched rate**, which the matcher alone produces and which is only an *upper bound*: a comment matching no human comment may be a real issue the reviewers never raised. The matcher never separates those two; only a judgment against the code does. The rubric's third verdict, `unverifiable`, keeps "the chunk cannot settle this" out of both buckets rather than letting it flatter or condemn the model.
  - *Usefulness score* — a manually-rated sample of model comments. **Not implemented.**

## Results

**Preliminary — 30-PR subset, 102 human comments.** Not the full 90-PR corpus, and
differences between arms are **not statistically significant** at this sample size.

| Model | Via | Comments | Recall (overall) | Recall (bug) | Recall (design) | Unfounded rate — machine screen, **retracted** † |
|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | OpenRouter | 816 | 1.0% (1/102) | 0/14 | 0/50 | **36.2%** (59/163) |
| `anthropic/claude-sonnet-5` | subagent | 76 | 1.0% (1/102) | 0/14 | 1/50 | **0.0%** (0/15) |
| `claude-code-subagent/opus` | subagent | 249 | 4.9% (5/102) ‡ | 0/14 | 2/50 ‡ | **2.0%** (1/49) |

† **These unfounded rates are retracted and shown only as the judge's raw output.** A
≥20% sample of each arm's unmatched comments (227 judgments) was judged against frozen
`hallucination_v1` by a second model, which saw exactly the diff chunk the reviewer saw
and nothing else. A blind, stratified 46-judgment human slice was then hand-checked
against the same rubric and the same chunks, with the machine's verdict hidden. **Human
and machine agree on 20/46 = 43.5%, Cohen's κ = 0.046** — chance level. In the stratum
that carries qwen's 36.2%, a seeded draw of 12 from the 59 comments the machine called
`unfounded`, the human upheld **1**. Do not cite this column.

‡ **Human-verified.** All 8 matches were hand-checked against the frozen `match_v1`
rubric; one opus match (category `design`) was rejected, moving opus from 5.9% to 4.9%
and its design recall from 3/50 to 2/50. qwen and sonnet-5 were unaffected. See
`reports/match-verification-results.md`, including the provenance caveat: two verdicts
were revised after the arms were disclosed, and the blind-pass numbers are reported
alongside the final ones.

**Neither recall nor the unfounded rate separates these models.** Recall gives p = 0.212
for the largest gap with overlapping intervals. The unfounded rates gave Fisher exact
p = 3.3×10⁻⁷ (qwen vs opus) and p = 0.0028 (qwen vs sonnet-5), but those p-values are
computed on judgments that do not survive human verification. Reweighting the human
labels back onto each arm gives roughly 12% / 11% / 14% (qwen / opus / sonnet-5) with
intervals that cover each other — indicative only, on 6–14 draws per cell, and not a
replacement result.

Two confounds travel with this table. The subagent arms were reached through an agent
harness rather than the OpenRouter API — no temperature control, and the harness's own
system prompt wrapped each call. And **the screening judge is a Claude model while two of
the three arms are Claude models**, which is exactly the shape self-evaluation bias would
take; the human slice was drawn to test that, and both of its pre-registered bias
directions moved as predicted (the judge over-credited the Claude arms and over-condemned
qwen), though the asymmetry alone is not statistically significant. See
`reports/rq3-comparison-subset30.md` and `reports/hallucination-screen.md`.

## Limitations (stated up front)

- **Human comments are not ground truth for *all* issues.** Reviewers miss things too; recall against human comments measures *agreement with humans*, not absolute defect detection.
- **The hallucination screen failed human verification and its headline is retracted.** The unfounded rates were produced by one model applying a frozen rubric to three models' comments, and its judge shares a family with two of the three arms judged. A blind 46-judgment human slice, stratified toward the two verdicts where a biased judge would do the most damage, was completed Aug 31, 2026: **agreement 20/46 = 43.5%, Cohen's κ = 0.046** — chance level, and κ = −0.008 on the 27 judgments where both sides were decisive. The judge's `high`-confidence verdicts agree with the human only 50% of the time. So RQ2 currently has **no verified per-arm hallucination rate**; what it has is a negative result about LLM-as-judge for this task. The verification is itself limited: one rater, no adjudication, 6–14 draws per cell, and the Claude arms' `unverifiable` judgments went unsampled entirely. `sonnet-5`'s screened 0% was 0-of-15 with a 95% upper bound of 20% — undetected, not absent — and the human found an unfounded comment among its 6 sampled `founded` verdicts.
- **The category labels were never validated by a human.** Categories are assigned by one model and re-rated by a second; agreement between two models on a shared rubric bounds self-consistency, not accuracy — both raters can misread the same rubric the same way. The first rater is also poorly calibrated: it marked 63 of 66 sampled assignments `high` confidence, and those `high`-confidence labels agree with the second rater only 84% of the time, so the `confidence` field on the 328 published assignments is not a reliability signal. Disagreement concentrates on the `design`/`style` boundary (7 of 12), and the first rater over-assigned `bug` and `question` — the two categories in which no arm on the 30-PR subset matched anything (0/14 `bug` for all three), so the subset's most striking result rests on its least stable denominators. On the full-corpus qwen run, 2 of the 5 matches are `bug` and 1 is `question`. A human pass over the sample was started and abandoned after 9 of 66; its labels are preserved but unscored, because they used a vocabulary outside the frozen four.
- **Semantic matching is partly LLM-judged.** Mitigated by a written rubric and manual verification on a sample, but subjectivity remains.
- **Java only, mid-size OSS projects only.** Results may not transfer to other languages, proprietary codebases, or very large monorepos.
- **Pre-review snapshot reconstruction is approximate** for PRs with force-pushed histories; such PRs are excluded.
- **No multi-turn review.** Human review is conversational; ReviewLens evaluates only first-pass comments.
- **A model ID does not pin down who served the request.** OpenRouter routes a model to one of several upstream providers, and they are not interchangeable: two providers were observed returning a billed completion with `content: null` (`finish_reason: "stop"`), which the pipeline would otherwise have recorded as that *model* failing to produce parseable output. Such replies are now retried instead of cached, and every run records which providers answered, so a provider-side defect cannot be read as a model-capability difference in RQ3.
- **Some models were reached through an agent harness, not the OpenRouter API.** The OpenRouter budget could not fund a Claude pass (a full 90-PR run prices at $5–13 per model), so the Claude arms were driven through Claude Code subagents against the same frozen prompt and the same rendered chunks. They therefore had no temperature control and carried the agent harness's own system prompt. Each run records `via` (`openrouter` or `claude-code-subagent`), and the comparison table prints it: a gap between an API arm and a subagent arm mixes model capability with delivery channel and cannot be attributed to capability alone.
- **A wrapper instruction can move the result it measures.** While building the subagent arms, an early wrapper restated the frozen prompt's "flag only what you are confident about" rule in its own words. That one redundant sentence cut the model's output rate by ~3x — on comment volume, which feeds the unmatched rate and therefore RQ2. The wrapper was reduced to pure mechanics (which file to read, which to write) and made byte-identical across every batch and both arms. Anyone evaluating an LLM reviewer through an agent should assume their scaffolding is part of the treatment.
- **Recall is bounded before any model runs.** Two structural ceilings apply equally to every model: on the 30-PR subset, 11 of 102 human comments (11%) sit on files the chunker never produced a chunk for — 9 of them on files outside the PR's changed Java set entirely (build files, or files the PR removed) — and the ±3-line matching window bounds the rest. On the full corpus the figure is 35/318, also 11%. The window was measured rather than assumed — see below.
- **The ±3-line window is not what produces the low recall.** Re-matching at ±5, ±10 and ±25 makes 104 more human comments reachable (127 → 231 of 318, 40% → 73%) and costs 284 extra judge calls, and yields **zero** additional matches; recall is flat at 1.57% across an eightfold widening. The models are raising different issues, not the right issues in the wrong place.
- **Per-category recall is rubric-sensitive, and the categories are LLM-assigned.** Two versions of `categorize_v1` disagreed on 16% of labels (51 of 328). The residual disagreement concentrates on the design/style boundary for small local edits.
- **Unparseable model replies are counted, not hidden.** Weaker models sometimes return something other than the requested JSON — one observed failure mode is copying the diff's `+`/`-` line markers into the reply. The parser recovers what it safely can; whatever remains unparseable is written to the run's `errors.json` and reported as a per-model parse-failure rate, because a lost chunk depresses measured recall for reasons that have nothing to do with review ability.

## Scope

**In:** Java diffs from GitHub PRs; per-file review with line-anchored comments; category + severity tagging; markdown report or posted GitHub review; the evaluation harness.

**Out (future work):** auto-fixing, multi-turn review conversations, IDE plugins, model fine-tuning, non-Java languages.

## Roadmap

- **Jul 2026** — ingestion + chunking + review engine on live PRs; prompt v1 frozen
- **Aug 1–15, 2026** — PR mining complete; matching pipeline; first recall numbers on one model
- **Aug 16–31, 2026** — multi-model comparison (2–3 models via OpenRouter); manual verification pass; results table, technical report, demo GIF
- **Hard feature freeze: Aug 15.** Anything not in scope goes to future work.

## Reproducing the evaluation

```bash
git clone https://github.com/Rakib-mbstu/reviewlens
cd reviewlens
pip install -r requirements.txt

export OPENROUTER_API_KEY=...   # any OpenRouter-supported model works
export GITHUB_TOKEN=...          # read-only, for PR mining

# 1. Mine the evaluation corpus
python -m reviewlens.mine --projects junit5 mockito checkstyle --out data/corpus/

# 1b. Categorize each human comment (bug/design/style/question) for RQ1's
#     per-category recall — LLM-assisted, spot-checked by hand, never hardcoded
python -m reviewlens.eval.categorize --corpus data/corpus/ --model <model-id> \
    --spotcheck-out reports/categorization-spotcheck.csv
#    --spotcheck-out writes a reproducible >=20% sample of the assignments for
#    hand-checking; the sample is determined by --seed, so it can be re-derived.

# 2. Run the reviewer on the pre-review state of each PR
python -m reviewlens.review --corpus data/corpus/ --model <model-id> --out runs/<model-id>/
#    add --no-cache to force fresh API calls instead of reusing cached responses

# 3. Match model comments to human comments and compute metrics
python -m reviewlens.eval --run runs/<model-id>/ --judge-model <model-id> --report reports/<model-id>.md
#    --judge-model is the model that judges semantic equivalence; like every
#    other model ID it is a parameter, never hardcoded. The corpus directory is
#    read from the run's run_meta.json, so a report is always tied to the corpus
#    the run actually used (override with --corpus if it has moved).

# 4. Export a reproducible sample of matches and unmatched-model comments for manual verification
python -m reviewlens.eval.export_verification --run runs/<model-id>/ --out reports/<model-id>-verification.csv

# 5. How much of the measured recall depends on the +/-3 line window?
#    The rule stays frozen at +/-3 and that is the reported number; the wider
#    windows are diagnostic, separating "commented elsewhere" from "raised a
#    different issue".
python -m reviewlens.eval.sensitivity --run runs/<model-id>/ --judge-model <model-id> \
    --windows 3,5,10,25 --report reports/<model-id>-sensitivity.md

# 6. Compare several evaluated runs on a shared corpus (RQ3). Refuses to emit a
#    table unless the runs cover the same PRs, and prints Wilson intervals plus
#    Fisher exact p-values so a non-significant gap cannot read as a finding.
python -m reviewlens.eval.compare --runs runs/<model-a>/ runs/<model-b>/ \
    --judge-model <model-id> --report reports/rq3-comparison.md
#    --verified <csv> folds human verdicts into the matched counts: pass a
#    verification CSV (step 4) with `human_verdict` filled in and a rejected
#    match stops counting toward recall, with the table showing how much of
#    each arm a human actually checked. Without the flag the table states in
#    plain text that no human verified it.
```

All LLM responses are cached under `cache/`; a full re-run with a warm cache costs $0.

## Related work

ReviewLens sits in the AI4SE / LLM4Code literature on automated code review (e.g., work on review comment generation and review automation benchmarks). The distinguishing choice here is evaluating against *historical human comments on real merged PRs* rather than synthetic benchmarks, with hallucination rate treated as a first-class metric. A short related-work discussion appears in [the technical report](reports/technical-report.md).

## About

Built by **Mir Rakibul Islam** — software engineer (Java/Spring Boot) with research experience in wireless network scheduling (paper under review at IJCNC). ReviewLens is the second project in a line of work on LLM-based evaluation of developer activity, following [AIPH](https://github.com/Rakib-mbstu/AIPH), an AI-powered interview preparation tool that evaluates how developers approach problem-solving.

Research interests: AI for software engineering — code review automation, program repair, LLM-based code generation.

## License

MIT
