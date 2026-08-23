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
| Run started | 2026-08-22T18:52:42.264772+00:00 |
| Run finished | did not finish |
| Upstream providers | SiliconFlow (736), Novita (394), Alibaba (43) |

## RQ1 — Recall of human review comments

| Metric | Value |
|---|---|
| PRs evaluated | 87 |
| Human comments (denominator) | 318 |
| Model comments | 2346 |
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

Categories were assigned LLM-assisted, one call per comment — not by hand and not by keyword rules. 328 comments carry a category, with 0 categorization failures and 7 assigned at low confidence. The rubric forces a choice among exactly four categories, so a comment that fits none is recorded at low confidence rather than given a fifth category. Category assignment is rubric-sensitive: a revision of the rubric changed a substantial share of labels, so per-category recall carries more uncertainty than overall recall. Assignments are spot-checked by hand against a reproducible sample, written by `reviewlens.eval.categorize --spotcheck-out`.

## RQ2 — Unmatched model comments

| Metric | Value |
|---|---|
| Unmatched model comments | 2341/2346 |
| Unmatched rate | 99.8% |
| **Hallucination rate** | **not measured** |

The unmatched rate is an **upper bound** on hallucination, not the hallucination rate. A model comment matching no human comment may be a genuine issue the reviewers did not raise. Separating the two requires the manual verification pass, which has not been run.

## Run health

| Metric | Value |
|---|---|
| Chunks reviewed | 1173 |
| Parse failures | 15/1173 |
| Parse-failure rate | 1.3% |

A chunk whose reply could not be parsed contributes no model comments, so it depresses recall for reasons unrelated to review ability. The rate is reported next to recall so the two are read together.

