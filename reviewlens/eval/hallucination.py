"""CLI entry point: `python -m reviewlens.eval.hallucination --run … --sample … --model … --out …`.

RQ2's unmatched-model count is only an *upper bound* on hallucinations: a
model comment nobody matched might still be a true observation the human
reviewer happened to miss. This module screens the unmatched-model slice of
`reviewlens.eval.export_verification`'s sample against the frozen rubric
`prompts/hallucination_v1.md`, turning that upper bound into a measured
count of founded / unfounded / unverifiable comments. It reports counts
only — the denominator choice for a "hallucination rate" belongs to the
reporting step, not here.

Matches (`kind == "match"`) verify RQ1 matching, a different question, and
are passed through this module's CSV untouched.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

from reviewlens.eval.export_verification import (
    UNMATCHED_MODEL_KIND,
    _judgment_id,
    run_slug,
    load_eval_matches,
)
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.offline_client import OfflineClient
from reviewlens.review.prompt import Prompt, load_prompt

_REVIEW_PROMPT_RELATIVE_PATH = os.path.join("prompts", "review_v1.md")
_HALLUCINATION_PROMPT_RELATIVE_PATH = os.path.join("prompts", "hallucination_v1.md")

_REVIEW_PLACEHOLDERS = ["[[FILE]]", "[[START_LINE]]", "[[END_LINE]]", "[[CHUNK]]"]

_VALID_VERDICTS = {"founded", "unfounded", "unverifiable"}
_VALID_CONFIDENCE = {"high", "low"}

_NEW_CSV_COLUMNS = ["model_verdict", "model_confidence", "model_reason"]


def _repo_root() -> str:
    """The repo root, derived from this file's location (never cwd), so the
    prompt paths resolve the same way regardless of where the CLI is run."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- chunk recovery: invert review_v1's rendered user message ---


def _extract_anchor(message: str, pos: int, anchor: str) -> "tuple[str, int]":
    """Return (text before `anchor`, index just past it), searching from `pos`.

    Fails loudly if the anchor is not found: a missing anchor means this
    message was not rendered by review_v1's exact template, and returning a
    partial or empty field here would silently hand a wrong chunk to the
    hallucination judge instead of refusing to guess.
    """
    idx = message.find(anchor, pos)
    if idx == -1:
        raise ValueError(
            f"expected literal text {anchor!r} not found in the rendered review_v1 "
            f"user message after offset {pos} — refusing to guess a chunk field."
        )
    return message[pos:idx], idx + len(anchor)


def invert_rendered_user(template: str, message: str) -> dict:
    """Recover {file, start_line, end_line, chunk} from a message rendered by
    `reviewlens.review.prompt.render_user` against `template`.

    The bytes the reviewer actually saw are the only fair input to a
    hallucination judgment (see `recover_chunk`'s docstring for why this
    matters more than it might seem). `render_user` builds the message with
    a plain sequential `str.replace` over four literal `[[TOKEN]]`
    placeholders, so the literal text *between* those tokens in the template
    never changes at render time — it is written verbatim into the message
    on both sides of whatever was substituted. That makes those in-between
    segments reliable anchors: whatever text sits between two known anchors
    in the rendered message is exactly the value `render_user` put there.
    This inversion is exact for any message actually produced by
    `render_user(template, ...)`, and raises rather than guesses for
    anything else.
    """
    segments: "list[str]" = []
    remaining = template
    for placeholder in _REVIEW_PLACEHOLDERS:
        before, sep, remaining = remaining.partition(placeholder)
        if not sep:
            raise ValueError(
                f"review_v1 user template is missing the {placeholder} placeholder — "
                "cannot invert it to recover chunk fields."
            )
        segments.append(before)
    tail = remaining  # literal template text after [[CHUNK]]; empty for review_v1

    if not message.startswith(segments[0]):
        raise ValueError(
            "rendered message does not start with review_v1's expected literal prefix "
            f"{segments[0]!r} — this message was not produced by review_v1's user "
            "template, refusing to guess a chunk."
        )
    pos = len(segments[0])

    file, pos = _extract_anchor(message, pos, segments[1])
    start_line_str, pos = _extract_anchor(message, pos, segments[2])
    end_line_str, pos = _extract_anchor(message, pos, segments[3])

    if tail:
        if not message.endswith(tail):
            raise ValueError(
                "rendered message does not end with review_v1's expected literal "
                f"suffix {tail!r} — refusing to guess where the chunk ends."
            )
        chunk = message[pos : len(message) - len(tail)]
    else:
        # review_v1's template ends with "Chunk:\n\n[[CHUNK]]", so the chunk
        # is simply everything left in the message.
        chunk = message[pos:]

    try:
        start_line = int(start_line_str)
        end_line = int(end_line_str)
    except ValueError as exc:
        raise ValueError(
            "recovered start/end line was not an integer: "
            f"start={start_line_str!r} end={end_line_str!r}"
        ) from exc

    return {"file": file, "start_line": start_line, "end_line": end_line, "chunk": chunk}


def _raw_chunk_path(run_dir: str, repo: str, number, chunk_index: int) -> str:
    pr_key = f"{repo.replace('/', '__')}__{number}"
    return os.path.join(run_dir, pr_key, "raw", f"chunk_{chunk_index}.json")


def recover_chunk(run_dir: str, review_prompt: Prompt, repo: str, number, chunk_index: int) -> dict:
    """Recover {file, start_line, end_line, chunk} for one reviewed chunk,
    from the raw request the review engine actually sent.

    The bytes the reviewer saw are the only fair input to a hallucination
    judgment: re-deriving the chunk from the mined corpus instead would
    require a fresh GitHub fetch and could silently drift from what was
    actually sent (a re-mined corpus, a different context window, a
    since-edited PR) — judging against a chunk the model never saw would
    invalidate the verdict without anyone noticing. `raw/chunk_<n>.json`
    already stores the rendered request, so recovering fields from it by
    inverting the template is exact by construction, not an approximation.
    """
    path = _raw_chunk_path(run_dir, repo, number, chunk_index)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No raw chunk file at {path} for {repo}#{number} chunk {chunk_index} — "
            "cannot judge this comment without the exact chunk the reviewer saw."
        )
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    try:
        messages = raw["request"]["messages"]
        user_message = next(m["content"] for m in messages if m.get("role") == "user")
    except (KeyError, TypeError, StopIteration) as exc:
        raise ValueError(f"{path}: does not have the expected request.messages shape ({exc})") from exc

    return invert_rendered_user(review_prompt.user_template, user_message)


def _unmatched_chunk_indices(records: list, slug: str) -> dict:
    """Map every unmatched_model judgment_id to the chunk_index its model
    comment came from, so a judgment can be traced back to the exact chunk.

    Reuses `export_verification`'s own id scheme (`_judgment_id`) rather
    than re-deriving it, so this lookup can never silently desync from the
    ids that actually appear in a `--sample` CSV exported by that module.
    """
    chunk_indices: dict = {}
    for pr in records:
        repo = pr["repo"]
        number = pr["number"]
        for i, model in enumerate(pr.get("unmatched_model", [])):
            judgment_id = _judgment_id(slug, repo, number, UNMATCHED_MODEL_KIND, i)
            chunk_indices[judgment_id] = model["chunk_index"]
    return chunk_indices


# --- rendering and judging ---


def render_hallucination_user(
    template: str,
    file: str,
    start_line: int,
    end_line: int,
    chunk: str,
    model_line,
    model_category: str,
    model_severity: str,
    model_comment: str,
) -> str:
    """Substitute the literal `[[TOKEN]]` placeholders in the hallucination_v1 user template.

    Plain str.replace, not str.format: the rubric's system section contains
    literal JSON braces (the output schema example) that str.format would
    misinterpret as replacement fields — same reason render_user exists in
    reviewlens/review/prompt.py.
    """
    text = template.replace("[[FILE]]", file)
    text = text.replace("[[START_LINE]]", str(start_line))
    text = text.replace("[[END_LINE]]", str(end_line))
    text = text.replace("[[CHUNK]]", chunk)
    text = text.replace("[[MODEL_LINE]]", str(model_line))
    text = text.replace("[[MODEL_CATEGORY]]", model_category)
    text = text.replace("[[MODEL_SEVERITY]]", model_severity)
    text = text.replace("[[MODEL_COMMENT]]", model_comment)
    return text


def _parse_hallucination_reply(response: dict) -> "tuple[dict | None, str | None]":
    """Parse one raw OpenRouter response into (verdict, error).

    Exactly one of the two is set. A malformed structure, non-JSON content,
    a missing/invalid `verdict`, or an invalid `confidence` all become an
    error rather than a guessed verdict: CLAUDE.md requires a judgment that
    fails to parse be recorded as a failure, never defaulted to a verdict.
    Mirrors `reviewlens.eval.categorize._parse_categorize_reply`.
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return None, f"malformed response structure ({exc})"

    if not isinstance(content, str):
        return None, f"response content was {type(content).__name__}, not a string"

    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[len("json") :]
        text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"reply was not valid JSON ({exc}): {content!r}"

    if not isinstance(parsed, dict):
        return None, f"expected a JSON object, got {type(parsed).__name__}: {content!r}"

    verdict = parsed.get("verdict")
    if verdict not in _VALID_VERDICTS:
        return None, f"'verdict' must be one of {sorted(_VALID_VERDICTS)}: {verdict!r}"

    confidence = parsed.get("confidence")
    if confidence not in _VALID_CONFIDENCE:
        return None, f"'confidence' must be one of {sorted(_VALID_CONFIDENCE)}: {confidence!r}"

    reason = parsed.get("reason", "")
    if not isinstance(reason, str):
        reason = str(reason)

    return {"verdict": verdict, "confidence": confidence, "reason": reason}, None


def judge_hallucination(
    client, model: str, prompt: Prompt, chunk_fields: dict, row: dict
) -> "tuple[dict | None, str | None]":
    """Judge one unmatched-model comment, returning (verdict, error).

    A thin wrapper around one `client.complete` call plus parsing, kept
    separate from the CLI loop so the LLM interaction is independently
    testable with a fake client.
    """
    user_content = render_hallucination_user(
        prompt.user_template,
        chunk_fields["file"],
        chunk_fields["start_line"],
        chunk_fields["end_line"],
        chunk_fields["chunk"],
        row["model_line"],
        row["model_category"],
        row["model_severity"],
        row["model_comment"],
    )
    messages = [
        {"role": "system", "content": prompt.system},
        {"role": "user", "content": user_content},
    ]
    response = client.complete(model, messages, **prompt.params)
    return _parse_hallucination_reply(response)


# --- CLI ---


def _read_sample(path: str) -> "tuple[list, list]":
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def _write_sample(path: str, fieldnames: list, rows: list) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    os.replace(tmp_path, path)


def main(argv: "list[str] | None" = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval.hallucination",
        description=(
            "Judge whether unmatched model review comments are founded in the exact "
            "code the reviewer saw, turning RQ2's unmatched rate into a measured "
            "hallucination count."
        ),
    )
    parser.add_argument(
        "--run",
        required=True,
        help="Run directory produced by reviewlens.review (e.g. runs/subset30/<arm>/).",
    )
    parser.add_argument(
        "--sample",
        required=True,
        help="Verification CSV produced by reviewlens.eval.export_verification.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="OpenRouter model ID used to judge hallucination.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output path for the judgment JSON.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the LLM response cache and force fresh calls.",
    )
    parser.add_argument(
        "--offline-requests",
        default=None,
        help=(
            "Drive judging with OfflineClient instead of OpenRouter, recording every "
            "unanswered request to this JSONL file. Used for RQ3 arms served by a "
            "model reached outside the OpenRouter API."
        ),
    )
    parser.add_argument(
        "--offline-answers",
        default=None,
        help="JSONL of {key, content} answers to replay (requires --offline-requests).",
    )
    args = parser.parse_args(argv)

    if args.offline_answers and not args.offline_requests:
        sys.exit("--offline-answers requires --offline-requests.")
    offline = args.offline_requests is not None

    try:
        records = load_eval_matches(args.run)
    except FileNotFoundError as exc:
        sys.exit(str(exc))
    run_meta_path = os.path.join(args.run, "run_meta.json")
    try:
        with open(run_meta_path, encoding="utf-8") as f:
            review_model = json.load(f)["model"]
    except (FileNotFoundError, KeyError) as exc:
        sys.exit(f"{run_meta_path}: cannot read the run's model, needed to rebuild judgment ids ({exc})")
    chunk_indices = _unmatched_chunk_indices(records, run_slug(review_model))

    try:
        fieldnames, rows = _read_sample(args.sample)
    except FileNotFoundError:
        sys.exit(
            f"No sample CSV at {args.sample}. Run "
            "`python -m reviewlens.eval.export_verification --run ... --out ...` first."
        )

    for column in _NEW_CSV_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    review_prompt = load_prompt(os.path.join(_repo_root(), _REVIEW_PROMPT_RELATIVE_PATH))
    hallucination_prompt = load_prompt(os.path.join(_repo_root(), _HALLUCINATION_PROMPT_RELATIVE_PATH))

    if offline:
        llm_client = OfflineClient(args.offline_requests, args.offline_answers)
    else:
        llm_client = OpenRouterClient(use_cache=not args.no_cache)

    verdicts: dict = {}
    failures: list = []

    try:
        for row in rows:
            if row.get("kind") != UNMATCHED_MODEL_KIND:
                continue

            judgment_id = row["judgment_id"]
            chunk_index = chunk_indices.get(judgment_id)
            if chunk_index is None:
                sys.exit(
                    f"{judgment_id}: no matching unmatched_model entry in "
                    f"{args.run}/eval_matches.json — --sample and --run are inconsistent "
                    "(re-export the sample from this run before judging it)."
                )

            try:
                chunk_fields = recover_chunk(
                    args.run, review_prompt, row["repo"], row["pr_number"], chunk_index
                )
            except (FileNotFoundError, ValueError) as exc:
                sys.exit(str(exc))

            verdict, error = judge_hallucination(
                llm_client, args.model, hallucination_prompt, chunk_fields, row
            )
            if error is not None:
                failures.append(
                    {
                        "judgment_id": judgment_id,
                        "repo": row["repo"],
                        "pr_number": row["pr_number"],
                        "error": error,
                    }
                )
                print(f"{judgment_id}: FAILED ({error})")
                continue

            verdicts[judgment_id] = verdict
            row["model_verdict"] = verdict["verdict"]
            row["model_confidence"] = verdict["confidence"]
            row["model_reason"] = verdict["reason"]
            print(f"{judgment_id}: {verdict['verdict']} ({verdict['confidence']})")
    finally:
        llm_client.close()

    _write_sample(args.sample, fieldnames, rows)

    counts = {"founded": 0, "unfounded": 0, "unverifiable": 0}
    for verdict in verdicts.values():
        counts[verdict["verdict"]] += 1

    output = {
        "judged_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "via": "claude-code-subagent" if offline else "openrouter",
        "prompt": {
            "name": hallucination_prompt.name,
            "version": hallucination_prompt.version,
            "sha256": hallucination_prompt.sha256,
        },
        "run": args.run,
        "sample": args.sample,
        "verdicts": verdicts,
        "failures": failures,
        "counts": counts,
    }
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    tmp_out = f"{args.out}.tmp"
    with open(tmp_out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=True)
    os.replace(tmp_out, args.out)

    total = len(verdicts) + len(failures)
    print(
        f"Judged {len(verdicts)}/{total} unmatched-model comments, {len(failures)} failures. "
        f"Wrote {args.out} and {args.sample}."
    )


if __name__ == "__main__":
    main()
