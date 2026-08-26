# ReviewLens evaluation — `qwen/qwen3-coder-30b-a3b-instruct`

> **Incomplete run.** This report covers only the PRs the review run finished (87 of 90 in the corpus). Treat these numbers as a partial pass, not as the study's result.

## Provenance

| Field | Value |
|---|---|
| Review model | `qwen/qwen3-coder-30b-a3b-instruct` |
| Review prompt | `review_v1` v1 |
| Review prompt sha256 | `3cf6f21ef8343e79…` |
| Judge model | `google/gemini-2.5-flash-lite` |
| Match rubric | `match_v1` v1 |
| Match rubric sha256 | `ff170b79dc8921ec…` |
| Comment categorizer | `google/gemini-2.5-flash-lite` |
| Category rubric | `categorize_v1` v1 |
| Category rubric sha256 | `bd5e4f74bd473858…` |
| Corpus | `data/corpus/` |
| Run started | 2026-08-23T04:59:06.372640+00:00 |
| Run finished | did not finish |
| Upstream providers | SiliconFlow (739), Novita (391), Alibaba (43) |

## RQ1 — Recall of human review comments

| Metric | Value |
|---|---|
| PRs evaluated | 87 |
| Human comments (denominator) | 318 |
| Model comments | 2356 |
| Matched | 5/318 |
| **Recall** | **1.6%** |

Recall here means agreement with the humans who reviewed these PRs, not absolute defect detection — reviewers miss issues too.

### Recall by category

| Category | Matched | Total | Recall |
|---|---|---|---|
| bug | 2 | 34 | 5.9% |
| design | 1 | 150 | 0.7% |
| question | 1 | 52 | 1.9% |
| style | 1 | 82 | 1.2% |

Categories were assigned LLM-assisted, one call per comment — not by hand and not by keyword rules. 328 comments carry a category, with 0 categorization failures and 7 assigned at low confidence. The rubric forces a choice among exactly four categories, so a comment that fits none is recorded at low confidence rather than given a fifth category. Category assignment is rubric-sensitive: a revision of the rubric changed a substantial share of labels, so per-category recall carries more uncertainty than overall recall. A reproducible sample of the assignments is re-rated by a second, independent model against the same frozen rubric (see `reports/categorization-interrater.md`); no human validated these labels, so that check measures inter-model consistency in applying the rubric, not correctness.

## RQ2 — Unmatched model comments

| Metric | Value |
|---|---|
| Unmatched model comments | 2351/2356 |
| Unmatched rate | 99.8% |
| **Hallucination rate** | **not measured** |

The unmatched rate is an **upper bound** on hallucination, not the hallucination rate. A model comment matching no human comment may be a genuine issue the reviewers did not raise. Separating the two requires the manual verification pass, which has not been run.

## Run health

| Metric | Value |
|---|---|
| Chunks reviewed | 1173 |
| Chunks lost (no output) | 6/1173 |
| **Chunk loss rate** | **0.5%** |
| Chunks with a parse error | 11/1173 |
| Error-chunk rate | 0.9% |
| Malformed items per chunk | 1.2% |
| &nbsp;&nbsp;— of which provider-caused | 8/14 |
| &nbsp;&nbsp;— of which model-caused | 6/14 |

**Chunk loss rate** is the headline coverage number: a lost chunk contributed zero model comments, so it depresses recall for reasons unrelated to review ability, and is reported next to recall so the two are read together. **Malformed items per chunk** counts individual rejected items rather than lost chunks — a chunk can carry a malformed item and still contribute other, valid comments — so this rate is not a chunk-loss rate and can exceed 1. Provider-caused failures are delivery faults (the model was billed and generated tokens, but the provider returned a null content field) and are not attributable to the model.

