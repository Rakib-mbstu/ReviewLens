"""Two-pass offline `.complete()` client for driving the review engine with a
model reached outside the OpenRouter API (a Claude Code subagent, for RQ3).

The engine's determinism is what makes this sound: `review_pr` re-derives
byte-identical chunks from the same corpus and prompt, so the same
(model, messages, params) triple recurs across two separate processes. Pass 1
runs the engine with no answers file, recording every request's `cache_key`
(reviewlens.openrouter.cache_key — the same key OpenRouterClient itself uses)
to a JSONL file and returning `content: None` for each one, which the engine
records as a parse error rather than a fabricated review. Something outside
this codebase then answers those requests. Pass 2 runs the engine again
against the same corpus with the answers file supplied, and every recorded
key is found and returned in place of a live call. No network call is ever
made by this module.
"""

from __future__ import annotations

import json
import os

from reviewlens.openrouter import cache_key
from reviewlens.review.answers import load_answers


def _split_messages(messages: "list[dict]") -> "tuple[str, str]":
    """Pull the system and user message content out of a chat messages list.

    The engine always sends exactly one system and one user message
    (engine.py's `review_pr`), but this looks up by role rather than
    position so a request file stays meaningful even if that ever changes.
    """
    system = next((m["content"] for m in messages if m.get("role") == "system"), "")
    user = next((m["content"] for m in messages if m.get("role") == "user"), "")
    return system, user


class OfflineClient:
    """Drop-in replacement for `OpenRouterClient` with no network access.

    Satisfies the same `.complete(model, messages, **params) -> dict`
    interface the engine calls, plus a no-op `close()`.
    """

    def __init__(self, requests_path: str, answers_path: "str | None" = None):
        self._requests_path = requests_path
        self._answers: "dict[str, str]" = {}
        if answers_path is not None and os.path.exists(answers_path):
            self._answers = load_answers(answers_path)
        self._recorded_keys: "set[str]" = set()
        self.answered = 0
        self.recorded = 0

    def complete(self, model: str, messages: "list[dict]", **params) -> dict:
        """Return an answer if one was recorded, else record the request.

        Answered requests get a response in OpenRouter shape carrying the
        stored reply text, so `parse_review_response` reads it exactly as it
        would a live OpenRouter response. Unanswered requests get
        `content: None` (what `content_is_missing` detects) and are appended
        to `requests_path` as one JSON line, deduplicated by key within this
        run so a repeated chunk is written once.
        """
        key = cache_key(model, messages, params)

        if key in self._answers:
            self.answered += 1
            return {
                "provider": "claude-code-subagent",
                "model": model,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": self._answers[key]},
                    }
                ],
            }

        if key not in self._recorded_keys:
            self._recorded_keys.add(key)
            self.recorded += 1
            system, user = _split_messages(messages)
            record = {"key": key, "model": model, "system": system, "user": user}
            with open(self._requests_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=True) + "\n")
                f.flush()

        return {
            "provider": "claude-code-subagent",
            "model": model,
            "choices": [
                {"finish_reason": "stop", "message": {"role": "assistant", "content": None}}
            ],
        }

    def close(self) -> None:
        """No-op: no connection is ever held open."""
