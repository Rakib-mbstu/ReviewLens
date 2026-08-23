# ReviewLens evaluation — `qwen/qwen3-coder-30b-a3b-instruct`

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
| Corpus | `data/corpus-subset30/` |
| Run started | 2026-08-23T19:07:35.741681+00:00 |
| Run finished | 2026-08-23T19:12:35.549017+00:00 |
| Upstream providers | SiliconFlow (264), Novita (135), Alibaba (15) |

## RQ1 — Recall of human review comments

| Metric | Value |
|---|---|
| PRs evaluated | 30 |
| Human comments (denominator) | 102 |
| Model comments | 816 |
| Matched | 1/102 |
| **Recall** | **1.0%** |

Recall here means agreement with the humans who reviewed these PRs, not absolute defect detection — reviewers miss issues too.

### Recall by category

| Category | Matched | Total | Recall |
|---|---|---|---|
| bug | 0 | 14 | 0.0% |
| design | 0 | 50 | 0.0% |
| question | 0 | 17 | 0.0% |
| style | 1 | 21 | 4.8% |

Categories were assigned LLM-assisted, one call per comment — not by hand and not by keyword rules. 328 comments carry a category, with 0 categorization failures and 7 assigned at low confidence. The rubric forces a choice among exactly four categories, so a comment that fits none is recorded at low confidence rather than given a fifth category. Category assignment is rubric-sensitive: a revision of the rubric changed a substantial share of labels, so per-category recall carries more uncertainty than overall recall. Assignments are spot-checked by hand against a reproducible sample, written by `reviewlens.eval.categorize --spotcheck-out`.

## RQ2 — Unmatched model comments

| Metric | Value |
|---|---|
| Unmatched model comments | 815/816 |
| Unmatched rate | 99.9% |
| **Hallucination rate** | **not measured** |

The unmatched rate is an **upper bound** on hallucination, not the hallucination rate. A model comment matching no human comment may be a genuine issue the reviewers did not raise. Separating the two requires the manual verification pass, which has not been run.

## Run health

| Metric | Value |
|---|---|
| Chunks reviewed | 414 |
| Parse failures | 5/414 |
| Parse-failure rate | 1.2% |

A chunk whose reply could not be parsed contributes no model comments, so it depresses recall for reasons unrelated to review ability. The rate is reported next to recall so the two are read together.

