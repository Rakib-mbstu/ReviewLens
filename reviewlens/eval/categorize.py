"""CLI entry point: `python -m reviewlens.eval.categorize --corpus … --model … [--out …]`.

RQ1 needs recall broken down by comment category (bug/design/style/question),
but the mined corpus carries no category — human reviewers don't tag their
own comments. This module assigns one via a single LLM call per human
comment, using the frozen-shape rubric `prompts/categorize_v1.md` (parsed by
`reviewlens.review.prompt.load_prompt`, same as `match_v1.md`).

A reply that fails to parse, or names anything outside the four categories,
is recorded as a failure and never becomes a category: fabricating one would
corrupt RQ1's per-category denominator (see reviewlens/eval/metrics.py,
which only turns on the per-category breakdown once every human comment
carries a real category).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from reviewlens.eval.corpus import CATEGORIES_FILENAME, load_corpus
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.prompt import Prompt, load_prompt

_CATEGORIZE_PROMPT_RELATIVE_PATH = os.path.join("prompts", "categorize_v1.md")
_VALID_CATEGORIES = {"bug", "design", "style", "question"}
_VALID_CONFIDENCE = {"high", "low"}


def _repo_root() -> str:
    """The repo root, derived from this file's location (never cwd), so the
    rubric path resolves the same way regardless of where the CLI is run."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def render_categorize_user(template: str, file: str, line: int, comment: str) -> str:
    """Substitute the literal `[[TOKEN]]` placeholders in the categorize_v1 user template.

    Plain str.replace, not str.format: the rubric's system section contains
    literal JSON braces (the output schema example) that str.format would
    misinterpret as replacement fields — same reason render_match_user exists
    in reviewlens/eval/matching.py.
    """
    text = template.replace("[[FILE]]", file)
    text = text.replace("[[LINE]]", str(line))
    text = text.replace("[[COMMENT]]", comment)
    return text


def _parse_categorize_reply(response: dict) -> tuple[dict | None, str | None]:
    """Parse one raw OpenRouter response into (verdict, error).

    Exactly one of the two is set. A malformed structure, non-JSON content,
    a missing `category` key, or a `category` outside the four valid values
    all become an error rather than a guessed category — mirrors
    `reviewlens.eval.matching._parse_judge_reply`'s defensiveness.
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

    category = parsed.get("category")
    if category not in _VALID_CATEGORIES:
        return None, f"'category' must be one of {sorted(_VALID_CATEGORIES)}: {category!r}"

    confidence = parsed.get("confidence")
    if confidence not in _VALID_CONFIDENCE:
        return None, f"'confidence' must be one of {sorted(_VALID_CONFIDENCE)}: {confidence!r}"

    reason = parsed.get("reason", "")
    if not isinstance(reason, str):
        reason = str(reason)

    return {"category": category, "confidence": confidence, "reason": reason}, None


def categorize_comment(
    client: OpenRouterClient, model: str, prompt: Prompt, comment: dict
) -> tuple[dict | None, str | None]:
    """Categorize one mined human comment, returning (verdict, error).

    A thin wrapper around one `client.complete` call plus parsing, kept
    separate from the CLI loop so the LLM interaction is independently
    testable with a fake client.
    """
    user_content = render_categorize_user(
        prompt.user_template, comment["path"], comment["line"], comment["body"]
    )
    messages = [
        {"role": "system", "content": prompt.system},
        {"role": "user", "content": user_content},
    ]
    response = client.complete(model, messages, **prompt.params)
    return _parse_categorize_reply(response)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m reviewlens.eval.categorize",
        description="Assign each mined human review comment a category (bug/design/style/question).",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        help="Corpus directory produced by reviewlens.mine (e.g. data/corpus/).",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="OpenRouter model ID used to categorize comments.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=f"Output path (default: <corpus>/{CATEGORIES_FILENAME}).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the LLM response cache and force fresh calls.",
    )
    args = parser.parse_args(argv)

    try:
        corpus = load_corpus(args.corpus)
    except FileNotFoundError as exc:
        sys.exit(str(exc))

    out_path = args.out or os.path.join(args.corpus, CATEGORIES_FILENAME)
    prompt = load_prompt(os.path.join(_repo_root(), _CATEGORIZE_PROMPT_RELATIVE_PATH))
    llm_client = OpenRouterClient(use_cache=not args.no_cache)

    categories: dict[str, dict] = {}
    failures: list[dict] = []
    seen_ids: set = set()

    try:
        for key in sorted(corpus):
            record = corpus[key]
            repo = record["repo"]
            number = record["number"]
            for comment in record.get("human_comments", []):
                comment_id = comment.get("id")
                if comment_id is None:
                    failures.append(
                        {"id": comment_id, "repo": repo, "number": number, "error": "comment has no id"}
                    )
                    continue
                # Comment ids must be unique across the whole corpus (they key
                # the output file); a collision would silently overwrite one
                # PR's categorization with another's, so this fails loudly
                # instead of assuming the assumption holds.
                if comment_id in seen_ids:
                    sys.exit(
                        f"Duplicate human comment id {comment_id} across the corpus "
                        f"(seen again on {repo}#{number}) — categories.json is keyed by id "
                        "and cannot represent this."
                    )
                seen_ids.add(comment_id)

                verdict, error = categorize_comment(llm_client, args.model, prompt, comment)
                if error is not None:
                    failures.append({"id": comment_id, "repo": repo, "number": number, "error": error})
                    print(f"{repo}#{number} comment {comment_id}: FAILED ({error})")
                    continue
                categories[str(comment_id)] = verdict
                print(f"{repo}#{number} comment {comment_id}: {verdict['category']} ({verdict['confidence']})")
    finally:
        llm_client.close()

    output = {
        "categorized_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "prompt": {"name": prompt.name, "version": prompt.version, "sha256": prompt.sha256},
        "categories": categories,
        "failures": failures,
    }
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = f"{out_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=True)
    os.replace(tmp_path, out_path)

    total = len(categories) + len(failures)
    print(f"Categorized {len(categories)}/{total} comments, {len(failures)} failures. Wrote {out_path}.")


if __name__ == "__main__":
    main()
