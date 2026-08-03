# CLAUDE.md — ReviewLens

Project instructions for Claude Code. Read this fully before making changes.

## What this project is

ReviewLens is an LLM-based code review tool **and an empirical study**. It reviews Java pull requests and is evaluated against real historical human review comments on merged PRs from open-source projects (JUnit 5, Mockito, Checkstyle). It is a research portfolio artifact for PhD applications in AI4SE — code quality, reproducibility, and honest evaluation matter more than features.

The study answers three research questions:

1. **RQ1 (Recall):** What fraction of human review comments does the LLM reviewer also raise, overall and by comment category?
2. **RQ2 (Hallucination):** What fraction of LLM comments are incorrect or unfounded (hallucination rate is a first-class metric, not an afterthought)?
3. **RQ3 (Model sensitivity):** How do results vary across model capability tiers (2–3 models via OpenRouter)?

Every code decision should be traceable to one of these RQs. If a change doesn't serve an RQ or the evaluation pipeline, it's out of scope.

## Scope discipline — read this first

- **Hard feature freeze: August 15, 2026.** After this date: bug fixes, evaluation, and reporting only.
- **Explicitly out of scope (do not build, do not scaffold "for later"):** auto-fixing code, multi-turn review conversations, IDE plugins, model fine-tuning, non-Java languages.
- Do not add features, abstractions, or config options that weren't asked for. When in doubt, ask before building. The owner prefers decisions locked explicitly before execution — propose the approach, get confirmation, then implement.

## Architecture

Five stages, three CLI modules:

```
reviewlens/
  mine/     # PR mining: pull merged PRs + human review comments from GitHub
  review/   # ingestion → chunking → review engine → structured output
  eval/     # match model comments to human comments, compute metrics, emit report
```

Pipeline invocations (keep these stable — the public README documents them):

```bash
python -m reviewlens.mine   --projects junit5 mockito checkstyle --out data/corpus/
python -m reviewlens.review --corpus data/corpus/ --model <model-id> --out runs/<model-id>/
python -m reviewlens.eval   --run runs/<model-id>/ --report reports/<model-id>.md
```

If a change would break these commands or their flags, update `README.md` in the same commit.

## Key technical rules

- **Language/stack:** Python. LLM calls go through a single swappable **OpenRouter client** — never hardcode a provider or model; model ID is always a parameter.
- **Caching:** every LLM response is cached under `cache/`, keyed so that a full re-run with a warm cache costs $0. Never bypass the cache silently; add a `--no-cache` flag if a fresh call is genuinely needed.
- **Determinism/reproducibility:** persist prompts, model IDs, parameters, and raw responses alongside outputs in `runs/`. Anyone should be able to reproduce a report from a run directory.
- **Review on pre-review state:** the review engine must run on the PR's *pre-review* code state, never the post-review merged state (otherwise recall is contaminated).
- **Matching rule:** a model comment matches a human comment if it targets the same issue within **±3 lines** and is semantically equivalent. Matching logic lives in `reviewlens.eval` only.
- **Manual verification:** the pipeline must support sampling **≥20%** of matches/hallucination judgments for manual review — build export for this, don't skip it.
- **Corpus size:** 50–100 merged Java PRs total across the three projects.
- **Env vars:** `OPENROUTER_API_KEY` (LLM calls), `GITHUB_TOKEN` (read-only, mining). Never commit keys; never log them.
- **Prompt v1 is frozen once locked.** Prompt changes after freeze invalidate comparisons — version prompts explicitly (e.g., `prompts/review_v1.md`) and never edit a frozen version in place.

## Data and directory conventions

```
data/corpus/    # mined PRs + human comments (input to review)
runs/<model>/   # model outputs + raw responses + run metadata
reports/        # per-model evaluation reports (markdown)
cache/          # LLM response cache (gitignored)
prompts/        # versioned prompt files
```

`cache/`, `runs/`, and any file containing tokens are gitignored. `data/corpus/` handling: check size before committing; prefer a mining script + pinned PR list over committing large raw data.

## Code style

- Small, single-purpose modules; standard library + `requests`/`httpx` level dependencies — justify anything heavier before adding it.
- Type hints on public functions. Docstrings state *what* and *why*, not restating the code.
- No dead code, no speculative abstraction, no TODO scaffolding for out-of-scope features.
- Errors from GitHub/OpenRouter APIs: fail loudly with actionable messages (rate limit vs. auth vs. network), retry with backoff only on transient errors.

## Testing

- Unit tests for: chunking boundaries, matching rule (±3-line + semantic equivalence edge cases), cache key stability, metric computation.
- Matching and metrics tests use small fixed fixtures — never live API calls in tests.
- Run tests before declaring any task complete.

## Honesty rules (this is a research artifact)

- Never fabricate, extrapolate, or "placeholder" metric numbers anywhere — reports, README, commit messages. Empty results tables stay empty until real numbers exist.
- Limitations are documented, not hidden. If a shortcut is taken (e.g., smaller corpus for a dry run), it's labeled as such in the report.
- The README's claims must always match what the code actually does.

## Timeline context (affects prioritization)

- **July 2026:** ingestion + chunking + review engine working on live PRs; prompt v1 frozen.
- **Aug 1–15:** mining complete; matching pipeline; first recall numbers on one model.
- **Aug 16–31:** multi-model comparison, manual verification pass, results table + technical report + demo GIF.

When asked "what should I work on," prioritize whatever is on the critical path for the current window above.
