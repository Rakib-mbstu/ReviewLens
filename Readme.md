# ReviewLens

**An LLM-based Java pull request reviewer, evaluated against real human review comments.**

ReviewLens is both a working tool and an empirical study. Instead of demonstrating cherry-picked examples, it measures — on PRs that real maintainers reviewed — what fraction of human-flagged issues an LLM catches, what it systematically misses, and how often it hallucinates problems that aren't there.

> **Status (Aug 19, 2026):** the review pipeline is implemented — pre-review-state ingestion (force-pushed PRs excluded), diff chunking, and the review engine with a cached OpenRouter client; **prompt v1 is frozen** as of Aug 12 (`prompts/review_v1.md`, sha256 `3cf6f21e…`) and is never edited in place — a prompt change means a new versioned file. **The corpus is mined:** 90 merged PRs (30 each from JUnit 5, Mockito, Checkstyle) carrying **328 top-level human review comments**, which form RQ1's recall denominator. The mining manifest records the selection criteria, per-project skip tallies, and the pinned PR list with pre-review SHAs. **The evaluation harness is now complete end to end:** comment matching (same file, ±3 lines, LLM-judged semantic equivalence), metric computation, and the `reviewlens.eval` CLI, which emits a markdown report plus an auditable per-comment match record. Still outstanding: human-comment categorization (so per-category recall is reported as unavailable rather than as zeros), the manual-verification export, and the manual pass itself.
>
> **No evaluation has been run, so there are no results yet.** The first review run — the small capability tier, `qwen/qwen3-coder-30b-a3b-instruct` — aborted on Aug 12 after two PRs when the API budget ran out, and its output is not a usable pass. The table below stays empty until real numbers exist.

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
- **Category assignment:** each human comment's category (bug / design / style / question) is assigned LLM-assisted, one call per comment, against a frozen versioned rubric (`prompts/categorize_v1.md`) that forces a choice among exactly those four — a comment fitting none is recorded at low confidence rather than given a fifth category. A reproducible ≥20% sample of the assignments (66 of 328, fixed seed) is exported for hand-checking at `reports/categorization-spotcheck.csv`; the checked agreement rate is reported once that pass is complete. Category assignment is rubric-sensitive: two versions of the rubric disagreed on 16% of labels (51 of 328), and the residual disagreement concentrates on the design/style boundary for small local edits (removing an `else`, dropping a temporary variable), so per-category recall carries more uncertainty than overall recall.
- **Manual verification:** ≥ 20% of automated matches are manually verified; inter-check agreement is reported.
- **Metrics:**
  - *Recall* of human comments, overall and per category (bug / design / style / question)
  - *Hallucination rate* — model comments judged invalid or useless on manual inspection. The automated pipeline reports only the **unmatched rate**, which is an upper bound: a model comment matching no human comment may be a real issue the reviewers never raised. The two are separated by the manual pass, never by the matcher.
  - *Usefulness score* — a manually-rated sample of model comments

## Results

*Pending — evaluation runs scheduled for August 2026. This section will contain the recall/hallucination table per model, per comment category.*

| Model | Recall (overall) | Recall (bug) | Recall (design) | Hallucination rate |
|---|---|---|---|---|
| — | — | — | — | — |

## Limitations (stated up front)

- **Human comments are not ground truth for *all* issues.** Reviewers miss things too; recall against human comments measures *agreement with humans*, not absolute defect detection.
- **Semantic matching is partly LLM-judged.** Mitigated by a written rubric and manual verification on a sample, but subjectivity remains.
- **Java only, mid-size OSS projects only.** Results may not transfer to other languages, proprietary codebases, or very large monorepos.
- **Pre-review snapshot reconstruction is approximate** for PRs with force-pushed histories; such PRs are excluded.
- **No multi-turn review.** Human review is conversational; ReviewLens evaluates only first-pass comments.
- **A model ID does not pin down who served the request.** OpenRouter routes a model to one of several upstream providers, and they are not interchangeable: two providers were observed returning a billed completion with `content: null` (`finish_reason: "stop"`), which the pipeline would otherwise have recorded as that *model* failing to produce parseable output. Such replies are now retried instead of cached, and every run records which providers answered, so a provider-side defect cannot be read as a model-capability difference in RQ3.
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
```

All LLM responses are cached under `cache/`; a full re-run with a warm cache costs $0.

## Related work

ReviewLens sits in the AI4SE / LLM4Code literature on automated code review (e.g., work on review comment generation and review automation benchmarks). The distinguishing choice here is evaluating against *historical human comments on real merged PRs* rather than synthetic benchmarks, with hallucination rate treated as a first-class metric. A short related-work discussion appears in the technical report.

## About

Built by **Mir Rakibul Islam** — software engineer (Java/Spring Boot) with research experience in wireless network scheduling (paper under review at IJCNC). ReviewLens is the second project in a line of work on LLM-based evaluation of developer activity, following [AIPH](https://github.com/Rakib-mbstu/AIPH), an AI-powered interview preparation tool that evaluates how developers approach problem-solving.

Research interests: AI for software engineering — code review automation, program repair, LLM-based code generation.

## License

MIT
