from __future__ import annotations

import csv
import json
import os

import pytest

import reviewlens.eval.hallucination as cli
from reviewlens.eval.export_verification import (
    FIELDNAMES,
    MATCH_KIND,
    UNMATCHED_MODEL_KIND,
    _judgment_id,
    run_slug,
)
from reviewlens.review.prompt import load_prompt, render_user

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REVIEW_PROMPT_PATH = os.path.join(_REPO_ROOT, "prompts", "review_v1.md")

# The model recorded in run_meta.json for these fixtures' review run — distinct
# from the `--model` the hallucination CLI uses to judge, which is a separate
# OpenRouter model ("test/judge" in _run_cli) entirely.
REVIEW_MODEL = "test/reviewer"
REVIEW_SLUG = run_slug(REVIEW_MODEL)


def _review_prompt():
    return load_prompt(_REVIEW_PROMPT_PATH)


# --- template inversion (no LLM, no CLI involved) ---


def test_template_inversion_round_trips_through_render_user():
    prompt = _review_prompt()
    chunk_content = "+ 10: foo();\n  11: bar();\n- 12: baz();\n+ 13: qux();"
    message = render_user(prompt.user_template, "src/main/Foo.java", 10, 13, chunk_content)

    recovered = cli.invert_rendered_user(prompt.user_template, message)

    assert recovered == {
        "file": "src/main/Foo.java",
        "start_line": 10,
        "end_line": 13,
        "chunk": chunk_content,
    }


def test_template_inversion_fails_loudly_on_a_garbled_message():
    prompt = _review_prompt()

    with pytest.raises(ValueError, match="refusing to guess"):
        cli.invert_rendered_user(prompt.user_template, "this is not a rendered review_v1 message at all")


# --- fixtures for CLI-level tests ---


class FakeHallucinationClient:
    """Stands in for OpenRouterClient so the CLI never touches the network.

    `replies` maps a substring of the rendered user content -> raw content
    string the "model" returns, so individual tests can make one specific
    judgment come back malformed without disturbing the others.
    """

    def __init__(self, replies=None, default_verdict="founded"):
        self.replies = replies or {}
        self.default_verdict = default_verdict
        self.calls = 0
        self.seen_user_contents = []

    def complete(self, model, messages, **params):
        self.calls += 1
        user_content = messages[-1]["content"]
        self.seen_user_contents.append(user_content)
        body = None
        for marker, content in self.replies.items():
            if marker in user_content:
                body = content
                break
        if body is None:
            body = json.dumps(
                {"verdict": self.default_verdict, "confidence": "high", "reason": "test verdict"}
            )
        return {
            "provider": "TestProvider",
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": body}}],
        }

    def close(self):
        pass


def _write_raw_chunk(run_dir, repo, number, chunk_index, file, start_line, end_line, chunk_content):
    prompt = _review_prompt()
    user_content = render_user(prompt.user_template, file, start_line, end_line, chunk_content)
    pr_key = f"{repo.replace('/', '__')}__{number}"
    raw_dir = os.path.join(run_dir, pr_key, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    payload = {
        "request": {
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": user_content},
            ]
        },
        "response": {
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "[]"}}]
        },
    }
    with open(os.path.join(raw_dir, f"chunk_{chunk_index}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _write_run_meta(run_dir, model=REVIEW_MODEL):
    with open(os.path.join(run_dir, "run_meta.json"), "w", encoding="utf-8") as f:
        json.dump({"model": model}, f)


def _write_eval_matches(run_dir, repo, number, unmatched_model):
    payload = [
        {
            "repo": repo,
            "number": number,
            "matches": [],
            "unmatched_human": [],
            "unmatched_model": unmatched_model,
            "judge_log": [],
        }
    ]
    with open(os.path.join(run_dir, "eval_matches.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _match_row(judgment_id, repo, number, human_verdict="", human_notes=""):
    return {
        "judgment_id": judgment_id,
        "kind": MATCH_KIND,
        "repo": repo,
        "pr_number": number,
        "pr_url": f"https://github.com/{repo}/pull/{number}",
        "file": "src/main/Foo.java",
        "human_line": 12,
        "human_comment": "please add a null check",
        "human_url": "",
        "model_line": 12,
        "model_category": "bug",
        "model_severity": "medium",
        "model_comment": "missing null check",
        "pipeline_verdict": "matched",
        "judge_reason": "same issue",
        "human_verdict": human_verdict,
        "human_notes": human_notes,
    }


def _unmatched_row(judgment_id, repo, number, model_line, model_comment,
                    human_verdict="", human_notes=""):
    return {
        "judgment_id": judgment_id,
        "kind": UNMATCHED_MODEL_KIND,
        "repo": repo,
        "pr_number": number,
        "pr_url": f"https://github.com/{repo}/pull/{number}",
        "file": "src/main/Foo.java",
        "human_line": "",
        "human_comment": "",
        "human_url": "",
        "model_line": model_line,
        "model_category": "bug",
        "model_severity": "medium",
        "model_comment": model_comment,
        "pipeline_verdict": "unmatched",
        "judge_reason": "",
        "human_verdict": human_verdict,
        "human_notes": human_notes,
    }


def _write_sample_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_sample_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _setup_one_unmatched(tmp_path, repo="org/repo", number=1, chunk_index=0,
                          model_line=12, model_comment="this can NPE",
                          review_model=REVIEW_MODEL):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_run_meta(str(run_dir), model=review_model)
    _write_raw_chunk(
        str(run_dir), repo, number, chunk_index,
        file="src/main/Foo.java", start_line=10, end_line=15,
        chunk_content="+ 12: doSomething(x);",
    )
    _write_eval_matches(
        str(run_dir), repo, number,
        unmatched_model=[
            {
                "file": "src/main/Foo.java",
                "line": model_line,
                "category": "bug",
                "severity": "medium",
                "comment": model_comment,
                "chunk_index": chunk_index,
            }
        ],
    )
    judgment_id = _judgment_id(run_slug(review_model), repo, number, UNMATCHED_MODEL_KIND, 0)
    sample = tmp_path / "sample.csv"
    return run_dir, sample, judgment_id


def _run_cli(monkeypatch, run_dir, sample, out, replies=None, default_verdict="founded",
             offline_requests=None, offline_answers=None, no_cache=False):
    client = FakeHallucinationClient(replies=replies, default_verdict=default_verdict)
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)
    args = [
        "--run", str(run_dir),
        "--sample", str(sample),
        "--model", "test/judge",
        "--out", str(out),
    ]
    if offline_requests is not None:
        args += ["--offline-requests", str(offline_requests)]
    if offline_answers is not None:
        args += ["--offline-answers", str(offline_answers)]
    if no_cache:
        args += ["--no-cache"]
    cli.main(args)
    return client


# --- happy path / kind filtering ---


def test_only_unmatched_model_rows_are_judged(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    match_id = _judgment_id(REVIEW_SLUG, "org/repo", 1, MATCH_KIND, 0)
    _write_sample_csv(
        sample,
        [
            _match_row(match_id, "org/repo", 1),
            _unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE"),
        ],
    )
    out = tmp_path / "hallucination.json"

    client = _run_cli(monkeypatch, run_dir, sample, out)

    assert client.calls == 1
    output = json.loads(out.read_text(encoding="utf-8"))
    assert list(output["verdicts"]) == [unmatched_id]
    assert output["counts"] == {"founded": 1, "unfounded": 0, "unverifiable": 0}

    rows = {r["judgment_id"]: r for r in _read_sample_csv(sample)}
    assert rows[match_id]["model_verdict"] == ""
    assert rows[match_id]["model_confidence"] == ""
    assert rows[match_id]["model_reason"] == ""
    assert rows[unmatched_id]["model_verdict"] == "founded"
    assert rows[unmatched_id]["model_confidence"] == "high"
    assert rows[unmatched_id]["model_reason"] == "test verdict"


def test_row_order_and_all_original_columns_are_preserved(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    match_id = _judgment_id(REVIEW_SLUG, "org/repo", 1, MATCH_KIND, 0)
    original_rows = [
        _match_row(match_id, "org/repo", 1),
        _unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE"),
    ]
    _write_sample_csv(sample, original_rows)
    out = tmp_path / "hallucination.json"

    _run_cli(monkeypatch, run_dir, sample, out)

    rows = _read_sample_csv(sample)
    assert [r["judgment_id"] for r in rows] == [match_id, unmatched_id]
    for original_field in FIELDNAMES:
        assert original_field in rows[0]


# --- human_verdict is hand-entered and must survive untouched ---


def test_preexisting_human_verdict_survives_a_run_untouched(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    _write_sample_csv(
        sample,
        [
            _unmatched_row(
                unmatched_id, "org/repo", 1, 12, "this can NPE",
                human_verdict="unfounded", human_notes="I disagree with the judge",
            )
        ],
    )
    out = tmp_path / "hallucination.json"

    _run_cli(monkeypatch, run_dir, sample, out, default_verdict="founded")

    rows = _read_sample_csv(sample)
    assert rows[0]["human_verdict"] == "unfounded"
    assert rows[0]["human_notes"] == "I disagree with the judge"
    # The model's own verdict is still recorded alongside the human's.
    assert rows[0]["model_verdict"] == "founded"


# --- failure handling: never a fabricated verdict ---


def test_invalid_verdict_is_recorded_as_a_failure_not_a_verdict(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path, model_comment="weird comment")
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "weird comment")])
    out = tmp_path / "hallucination.json"
    bad_reply = json.dumps({"verdict": "definitely-wrong", "confidence": "high", "reason": "x"})

    _run_cli(monkeypatch, run_dir, sample, out, replies={"weird comment": bad_reply})

    output = json.loads(out.read_text(encoding="utf-8"))
    assert output["verdicts"] == {}
    assert len(output["failures"]) == 1
    assert output["failures"][0]["judgment_id"] == unmatched_id
    assert "definitely-wrong" in output["failures"][0]["error"]
    assert output["counts"] == {"founded": 0, "unfounded": 0, "unverifiable": 0}

    rows = _read_sample_csv(sample)
    assert rows[0]["model_verdict"] == ""


def test_invalid_confidence_is_recorded_as_a_failure_not_a_verdict(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path, model_comment="weird comment")
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "weird comment")])
    out = tmp_path / "hallucination.json"
    bad_reply = json.dumps({"verdict": "founded", "confidence": "medium", "reason": "x"})

    _run_cli(monkeypatch, run_dir, sample, out, replies={"weird comment": bad_reply})

    output = json.loads(out.read_text(encoding="utf-8"))
    assert output["verdicts"] == {}
    assert len(output["failures"]) == 1
    assert "medium" in output["failures"][0]["error"]

    rows = _read_sample_csv(sample)
    assert rows[0]["model_verdict"] == ""


def test_non_json_reply_is_recorded_as_a_failure_not_a_verdict(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path, model_comment="weird comment")
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "weird comment")])
    out = tmp_path / "hallucination.json"

    _run_cli(monkeypatch, run_dir, sample, out, replies={"weird comment": "not json at all"})

    output = json.loads(out.read_text(encoding="utf-8"))
    assert output["verdicts"] == {}
    assert len(output["failures"]) == 1
    assert "not valid JSON" in output["failures"][0]["error"]

    rows = _read_sample_csv(sample)
    assert rows[0]["model_verdict"] == ""


# --- offline mode / via ---


def test_offline_answers_without_offline_requests_exits_with_error(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE")])
    out = tmp_path / "hallucination.json"
    answers = tmp_path / "answers.jsonl"
    answers.write_text("", encoding="utf-8")
    client = FakeHallucinationClient()
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)

    with pytest.raises(SystemExit, match="--offline-answers requires --offline-requests"):
        cli.main(
            [
                "--run", str(run_dir),
                "--sample", str(sample),
                "--model", "test/judge",
                "--out", str(out),
                "--offline-answers", str(answers),
            ]
        )


def test_via_is_openrouter_by_default(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE")])
    out = tmp_path / "hallucination.json"

    _run_cli(monkeypatch, run_dir, sample, out)

    output = json.loads(out.read_text(encoding="utf-8"))
    assert output["via"] == "openrouter"


def test_via_is_claude_code_subagent_in_offline_mode(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE")])
    out = tmp_path / "hallucination.json"
    requests_path = tmp_path / "requests.jsonl"

    # No FakeHallucinationClient/OpenRouterClient patch needed: --offline-requests
    # makes the CLI build a real (network-free) OfflineClient itself.
    cli.main(
        [
            "--run", str(run_dir),
            "--sample", str(sample),
            "--model", "test/judge",
            "--out", str(out),
            "--offline-requests", str(requests_path),
        ]
    )

    output = json.loads(out.read_text(encoding="utf-8"))
    assert output["via"] == "claude-code-subagent"
    # Pass 1: no answers yet, so the request was recorded and the reply
    # (content: None) is an unparseable failure rather than a fabricated verdict.
    assert output["verdicts"] == {}
    assert len(output["failures"]) == 1
    assert requests_path.exists()


# --- run_meta.json is required to rebuild judgment ids ---


def test_main_exits_with_actionable_message_when_run_meta_json_is_missing(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    (run_dir / "run_meta.json").unlink()
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE")])
    out = tmp_path / "hallucination.json"
    client = FakeHallucinationClient()
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "--run", str(run_dir),
                "--sample", str(sample),
                "--model", "test/judge",
                "--out", str(out),
            ]
        )

    assert "run_meta.json" in str(excinfo.value)


def test_main_exits_with_actionable_message_when_run_meta_json_has_no_model_key(tmp_path, monkeypatch):
    run_dir, sample, unmatched_id = _setup_one_unmatched(tmp_path)
    (run_dir / "run_meta.json").write_text(json.dumps({"other": "field"}), encoding="utf-8")
    _write_sample_csv(sample, [_unmatched_row(unmatched_id, "org/repo", 1, 12, "this can NPE")])
    out = tmp_path / "hallucination.json"
    client = FakeHallucinationClient()
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "--run", str(run_dir),
                "--sample", str(sample),
                "--model", "test/judge",
                "--out", str(out),
            ]
        )

    assert "run_meta.json" in str(excinfo.value)
