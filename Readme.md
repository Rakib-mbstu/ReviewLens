# ReviewLens

**An LLM-based Java pull request reviewer, evaluated against real human review comments.**

ReviewLens is both a working tool and an empirical study. Instead of demonstrating cherry-picked examples, it measures — on PRs that real maintainers reviewed — what fraction of human-flagged issues an LLM catches, what it systematically misses, and how often it hallucinates problems that aren't there.

> **Status (Aug 12, 2026):** the review pipeline is implemented — pre-review-state ingestion (force-pushed PRs excluded), diff chunking, and the review engine with a cached OpenRouter client; **prompt v1 is frozen** as of Aug 12 (`prompts/review_v1.md`, sha256 `3cf6f21e…`) and is never edited in place — a prompt change means a new versioned file. **The corpus is mined:** 90 merged PRs (30 each from JUnit 5, Mockito, Checkstyle) carrying **328 top-level human review comments**, which form RQ1's recall denominator. The mining manifest records the selection criteria, per-project skip tallies, and the pinned PR list with pre-review SHAs. The evaluation harness is only partly built — comment matching (same file, ±3 lines, LLM-judged semantic equivalence) is implemented and tested, but metric computation and the `reviewlens.eval` CLI are not, so that CLI still exits with a pointer to its tracking issue. **No review or evaluation run has been executed yet, so there are no results.** The table below stays empty until real numbers exist.

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
- **Manual verification:** ≥ 20% of automated matches are manually verified; inter-check agreement is reported.
- **Metrics:**
  - *Recall* of human comments, overall and per category (bug / design / style / question)
  - *Hallucination rate* — model comments judged invalid or useless on manual inspection
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

# 2. Run the reviewer on the pre-review state of each PR
python -m reviewlens.review --corpus data/corpus/ --model <model-id> --out runs/<model-id>/

# 3. Match model comments to human comments and compute metrics
python -m reviewlens.eval --run runs/<model-id>/ --report reports/<model-id>.md
```

All LLM responses are cached under `cache/`; a full re-run with a warm cache costs $0.

## Related work

ReviewLens sits in the AI4SE / LLM4Code literature on automated code review (e.g., work on review comment generation and review automation benchmarks). The distinguishing choice here is evaluating against *historical human comments on real merged PRs* rather than synthetic benchmarks, with hallucination rate treated as a first-class metric. A short related-work discussion appears in the technical report.

## About

Built by **Mir Rakibul Islam** — software engineer (Java/Spring Boot) with research experience in wireless network scheduling (paper under review at IJCNC). ReviewLens is the second project in a line of work on LLM-based evaluation of developer activity, following [AIPH](https://github.com/Rakib-mbstu/AIPH), an AI-powered interview preparation tool that evaluates how developers approach problem-solving.

Research interests: AI for software engineering — code review automation, program repair, LLM-based code generation.

## License

MIT
