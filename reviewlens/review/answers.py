"""Load a two-pass offline run's answer file (see `offline_client.py`).

Kept separate from `offline_client.py` so the JSONL format has one owner:
`OfflineClient` only ever reads answers through this function, and a
malformed line fails loudly here rather than surfacing later as a
mysteriously missing answer that looks like a routine cache miss.
"""

from __future__ import annotations

import json


def load_answers(path: str) -> dict[str, str]:
    """Read a JSONL answers file into a key -> content dict.

    Each line is `{"key": "<cache_key>", "content": "<raw reply text>"}`.
    A line missing either field raises ValueError naming its 1-based line
    number, because a silently dropped answer would otherwise show up much
    later as an unexplained parse error in pass 2 with no clue why.
    """
    answers: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "key" not in record or "content" not in record:
                raise ValueError(
                    f"{path}:{line_no}: answer line missing 'key' or 'content': {line!r}"
                )
            answers[record["key"]] = record["content"]
    return answers
