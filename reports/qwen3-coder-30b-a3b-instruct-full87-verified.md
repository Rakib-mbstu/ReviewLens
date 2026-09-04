# RQ1 — recall on one run, with human verdicts applied

One arm over 87 PRs carrying **318 human review comments**, through the frozen prompt, the chunker, and the matcher (same file, ±3 lines, semantic equivalence judged by `google/gemini-2.5-flash-lite`). There is nothing to compare it against here; the cross-model table is a separate report.

## Recall

| Arm | Via | Model comments | Matched | Recall | 95% CI | p vs lowest | Human-checked |
|---|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | unrecorded | 2356 | 5 | **1.6%** | [0.7%, 3.6%] | — | 5/5 checked, 0 rejected |

A gap marked **n.s.** is not evidence of an ordering. On a corpus this size recall rests on single-digit match counts, and the intervals overlap.

**The `Matched` column is human-corrected.** Every match is first proposed by an LLM judge applying the frozen rubric; where a human ruled on that judgment, the human's verdict is the one counted, and a rejected match is removed from the numerator. `Human-checked` says how much of each arm's matched count carries a human verdict — an arm reading `none` is scored by the judge alone. This matters because the same pipeline's *other* frozen LLM judge agreed with a human at chance level, so a judge-only count states more than it knows.

## Efficiency and reach

| Arm | Comments per chunk | Matches per comment | Reachable | Parse failures |
|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | 2.01 | 0.2% | 125/318 (39.3%) | 14/1173 |

`Reachable` counts human comments with at least one model comment inside the ±3 window — the ceiling recall could reach if the judge accepted every pair it saw. A low recall with high reachability means the model looked in the right place and raised a different issue; a low recall with low reachability means it never looked.

`Matches per comment` is the closest thing here to precision against human judgement. It is the column least sensitive to a single match landing or not.

## Confounds

Arms differ in **delivery channel**, not only in model. An arm marked `claude-code-subagent` was reached through an agent harness rather than the OpenRouter API: no temperature control, and the harness's own system prompt wrapped every call. A difference between an `openrouter` arm and a `claude-code-subagent` arm mixes model capability with that channel, and cannot be attributed to capability alone.

