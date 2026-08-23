# Line-window sensitivity — `qwen/qwen3-coder-30b-a3b-instruct`

Recall as a function of the matching rule's line window. **The frozen rule is ±3, and that row is the study's reported recall.** The wider windows are diagnostic only — they are not a re-definition of the rule, and comparing them across models would be invalid.

Judge model: `google/gemini-2.5-flash-lite`. Run: `qwen/qwen3-coder-30b-a3b-instruct`, PARTIAL.

| Window | Reachable | Reachable % | Matched | Recall | Judge calls |
|---|---|---|---|---|---|
| ±3 (frozen rule) | 109/255 | 42.7% | 4 | **1.6%** | 126 |
| ±5 | 123/255 | 48.2% | 4 | **1.6%** | 155 |
| ±10 | 149/255 | 58.4% | 4 | **1.6%** | 211 |
| ±25 | 186/255 | 72.9% | 4 | **1.6%** | 354 |

`Reachable` counts human comments with at least one model comment inside the window — the ceiling recall could reach at that tolerance if the judge accepted every pair. The gap between Reachable % and Recall is disagreement about the issue; the gap between 100% and Reachable % is the model commenting somewhere else entirely.
