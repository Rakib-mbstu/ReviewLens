# RQ3 — cross-model comparison

All arms reviewed the **same 30 PRs** carrying **102 human review comments**, through the same frozen prompt, the same chunker, and the same matcher (same file, ±3 lines, semantic equivalence judged by `google/gemini-2.5-flash-lite`).

## Recall

| Arm | Via | Model comments | Matched | Recall | 95% CI | p vs lowest |
|---|---|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | openrouter | 816 | 1 | **1.0%** | [0.2%, 5.3%] | — |
| `anthropic/claude-sonnet-5` | claude-code-subagent | 76 | 1 | **1.0%** | [0.2%, 5.3%] | 1.000 (n.s.) |
| `claude-code-subagent/opus` | claude-code-subagent | 249 | 6 | **5.9%** | [2.7%, 12.2%] | 0.119 (n.s.) |

A gap marked **n.s.** is not evidence of an ordering. On a corpus this size recall rests on single-digit match counts, and the intervals overlap.

## Efficiency and reach

| Arm | Comments per chunk | Matches per comment | Reachable | Parse failures |
|---|---|---|---|---|
| `qwen/qwen3-coder-30b-a3b-instruct` | 1.97 | 0.1% | 36/102 (35.3%) | 5/414 |
| `anthropic/claude-sonnet-5` | 0.18 | 1.3% | 8/102 (7.8%) | 0/414 |
| `claude-code-subagent/opus` | 0.60 | 2.4% | 28/102 (27.5%) | 0/414 |

`Reachable` counts human comments with at least one model comment inside the ±3 window — the ceiling recall could reach if the judge accepted every pair it saw. A low recall with high reachability means the model looked in the right place and raised a different issue; a low recall with low reachability means it never looked.

`Matches per comment` is the closest thing here to precision against human judgement. It is the column least sensitive to a single match landing or not.

## Confounds

Arms differ in **delivery channel**, not only in model. An arm marked `claude-code-subagent` was reached through an agent harness rather than the OpenRouter API: no temperature control, and the harness's own system prompt wrapped every call. A difference between an `openrouter` arm and a `claude-code-subagent` arm mixes model capability with that channel, and cannot be attributed to capability alone.

