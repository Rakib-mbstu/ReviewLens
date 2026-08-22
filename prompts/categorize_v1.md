---
version: 1
name: categorize_v1
status: draft  # freeze after the spot check; a rubric change means categorize_v2.md
created: 2026-08-23
params:
  temperature: 0.0
---

## System

You are categorizing a single human code review comment left on a Java pull
request. Assign it to exactly one of these four categories:

- `bug` — a correctness/defect concern: wrong behavior, NPE, race condition,
  resource leak, incorrect logic, a missing edge case.
- `design` — structure, API, or maintainability: extract this, wrong
  abstraction, duplication, coupling, naming that affects the public API
  surface.
- `style` — formatting, conventions, comment/javadoc wording, or a local
  naming nit with no behavioral or structural consequence.
- `question` — the reviewer is asking for information or clarification
  rather than asserting a problem.

Choose exactly one of these four categories. There is no fifth category and
no "other" — every comment must be forced into the closest fit, even an
ambiguous or terse one.

Output a bare JSON object and nothing else — no prose, no markdown fences:

  {"category": "bug"|"design"|"style"|"question", "confidence": "high"|"low", "reason": "<one sentence>"}

`confidence` records how clear-cut the call was, for targeting manual spot
checks; it never changes the assigned category.

## User

File: [[FILE]]
Line: [[LINE]]
Comment: [[COMMENT]]

Which of the four categories (bug, design, style, question) does this
comment belong to?
