# Category assignment — inter-rater check (66 of 328)

**What this is.** The >=20% spot-check sample of the LLM category assignments
(66 of 328, seed 20260823) re-rated by a second, independent model against the
same frozen rubric. **No human validated these labels.** This measures whether
two models applying `categorize_v1` agree, not whether either is correct.

| | rater 1 | rater 2 |
|---|---|---|
| model | `google/gemini-2.5-flash-lite` | `claude-code-subagent/fable` |
| via | `openrouter` | `claude-code-subagent` |
| temperature | 0.0 (honored) | **not controllable on this channel** |
| rubric | `categorize_v1` sha256 `bd5e4f74bd473858…` | identical (byte-verified) |
| run | 2026-08-22 | 2026-08-26 |

Rater 2 is substantially the more capable model, so this is closer to
**adjudication of a weak rater by a strong one** than to symmetric inter-rater
agreement. A disagreement is more likely rater 1 being wrong than the rubric
being ambiguous — but nothing here establishes that rater 2 is right.

## Agreement

**54/66 = 81.8%** (95% Wilson 70.9–89.3%). Cohen's kappa = **0.70**.

### Confusion (rows = rater 1, columns = rater 2)

| | `bug` | `design` | `style` | `question` | **total** |
|---|---|---|---|---|---|
| **`bug`** | 4 | 2 | 0 | 0 | **6** |
| **`design`** | 0 | 30 | 3 | 0 | **33** |
| **`style`** | 0 | 4 | 15 | 0 | **19** |
| **`question`** | 0 | 2 | 1 | 5 | **8** |
| **total** | 4 | 38 | 19 | 5 | **66** |

### Where the disagreements are

- **7 of the 12 disagreements are the `design`/`style` boundary** — the same
  seam that produced 16% label churn between two rubric versions. The rubric's
  own shape test does not resolve cases like "group these constants adjacently"
  (reordering within one file) or "replace `nullValue(Example.class)` with a
  `(Example) null` cast" (a trivial local edit that still changes the code).
- Rater 1 over-assigned the two rarest categories: 6 `bug` against rater 2's
  4, and 8 `question` against 5. Both surpluses drained into `design`.
  Because **no arm on the 30-PR subset matched a single `bug` or `question`
  comment** (0/14 `bug` for all three), the denominators of the two categories
  carrying that subset's most striking result are also the two least stable
  ones. The full-corpus qwen run is the exception: 2 of its 5 matches are
  `bug` and 1 is `question`.

## Confidence is not calibrated — the main finding

Rater 1 marked **63/66 assignments `high` confidence (95%)**. Rater 2, on
identical prompts, marked **34/66 `low` (52%)**.

Rater 1's `high`-confidence labels agree with rater 2 only **53/63 (84%)** of the time.

The rubric routes low confidence to human spot-checking: *"Low confidence never
changes the category you assign; it marks the comment for a human spot check."*
Rater 1 used that escape hatch 3 times in 66. **The mechanism was effectively
inert**, and the `confidence` field on all 328 published assignments should not
be read as a reliability signal.

## Deviations from rater 1's conditions

Recorded because they are part of the treatment, not around it:

1. **Shared context.** Rater 1 made 66 independent API calls. Rater 2 was run
   as 3 subagents of 22 requests each, so within a batch one judgment could
   influence another. The wrapper instructed against it; instruction is not
   isolation.
2. **No temperature control.** The cache keys were computed with the frozen
   `temperature: 0.0`, but the subagent channel cannot honor it. The keys claim
   a determinism the generation did not have.
3. **Tool access.** An API call has no tools; a subagent could have read the
   Java files or the PRs, which would make it a strictly stronger and
   non-comparable rater. The wrapper forbade it, and the transcripts were
   checked afterwards: all three raters touched only their batch file and their
   answers file.
4. **Wrapper text.** Pure mechanics, byte-identical across the three batches
   apart from file paths, and it never restates the rubric.

## Abandoned partial human pass

A human pass over the sample was started and stopped after 9 of 66. Its labels
are preserved verbatim in `reports/categorization-interrater.csv`
(`partial_human_label`) and are **not scored**: they used a vocabulary outside
the frozen four (`Doc`, `Practise`), so disagreements against a rubric that
forbids a fifth category would be guaranteed by construction rather than
informative. That the labeller reached for two categories the rubric does not
have is itself weak evidence the four-category taxonomy does not cleanly cover
this corpus.

## Reproduction

```bash
# pass 1 — export the 66 rendered prompts; no network, nothing fabricated
python -m reviewlens.eval.categorize --corpus data/corpus/ \
  --model claude-code-subagent/fable \
  --only-ids work/spotcheck-fable/spotcheck_ids.txt \
  --offline-requests work/spotcheck-fable/fable.requests.jsonl \
  --out work/spotcheck-fable/categories-fable.json

# (the rater answers those prompts -> work/spotcheck-fable/fable.answers.jsonl)

# pass 2 — replay the answers through the real parser
python -m reviewlens.eval.categorize --corpus data/corpus/ \
  --model claude-code-subagent/fable \
  --only-ids work/spotcheck-fable/spotcheck_ids.txt \
  --offline-requests work/spotcheck-fable/fable.requests.jsonl \
  --offline-answers work/spotcheck-fable/fable.answers.jsonl \
  --out work/spotcheck-fable/categories-fable.json

python work/spotcheck-fable/build_interrater.py
```
