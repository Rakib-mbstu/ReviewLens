from __future__ import annotations

import csv
import json

import pytest

import reviewlens.eval.categorize as cli
from reviewlens.eval.corpus import (
    CATEGORIES_FILENAME,
    load_categories,
    load_corpus,
    load_eval_inputs,
    normalize_human_comment,
)
from reviewlens.eval.metrics import compute_metrics
from reviewlens.eval.matching import match_comments


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class FakeCategorizeClient:
    """Stands in for OpenRouterClient so the CLI never touches the network.

    `replies` maps comment body -> raw content string the "model" returns,
    so individual tests can make one specific comment come back malformed
    without disturbing the others.
    """

    def __init__(self, replies=None, default_category="bug"):
        self.replies = replies or {}
        self.default_category = default_category
        self.calls = 0

    def complete(self, model, messages, **params):
        self.calls += 1
        user_content = messages[-1]["content"]
        body = None
        for comment, content in self.replies.items():
            if comment in user_content:
                body = content
                break
        if body is None:
            body = json.dumps(
                {"category": self.default_category, "confidence": "high", "reason": "test verdict"}
            )
        return {
            "provider": "TestProvider",
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": body}}],
        }

    def close(self):
        pass


def _mined_comment(comment_id, line, body):
    return {
        "id": comment_id,
        "path": "src/Main.java",
        "line": line,
        "body": body,
        "author": "reviewer",
        "url": f"https://github.com/org/repo/pull/1#discussion_r{comment_id}",
    }


def _corpus_record(number, comments):
    return {"repo": "org/repo", "number": number, "human_comments": comments}


def _setup_corpus(tmp_path, comments):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, comments))
    return corpus


def _run_cli(monkeypatch, corpus, out=None, replies=None, default_category="bug",
             spotcheck_out=None, spotcheck_rate=None, seed=None, only_ids=None,
             offline_requests=None, offline_answers=None):
    client = FakeCategorizeClient(replies=replies, default_category=default_category)
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)
    args = ["--corpus", str(corpus), "--model", "test/categorizer"]
    if out is not None:
        args += ["--out", str(out)]
    if spotcheck_out is not None:
        args += ["--spotcheck-out", str(spotcheck_out)]
    if spotcheck_rate is not None:
        args += ["--spotcheck-rate", str(spotcheck_rate)]
    if seed is not None:
        args += ["--seed", str(seed)]
    if only_ids is not None:
        args += ["--only-ids", str(only_ids)]
    if offline_requests is not None:
        args += ["--offline-requests", str(offline_requests)]
    if offline_answers is not None:
        args += ["--offline-answers", str(offline_answers)]
    cli.main(args)
    return client


# --- happy path ---


def test_every_comment_gets_a_category(tmp_path, monkeypatch):
    comments = [
        _mined_comment(1, 10, "this can NPE"),
        _mined_comment(2, 20, "please rename this variable"),
    ]
    corpus = _setup_corpus(tmp_path, comments)

    client = _run_cli(monkeypatch, corpus, default_category="bug")

    assert client.calls == 2
    out_path = corpus / CATEGORIES_FILENAME
    output = json.loads(out_path.read_text(encoding="utf-8"))

    assert output["model"] == "test/categorizer"
    assert output["prompt"]["name"] == "categorize_v1"
    assert output["prompt"]["version"] == 1
    assert len(output["prompt"]["sha256"]) == 64
    assert output["categories"]["1"] == {"category": "bug", "confidence": "high", "reason": "test verdict"}
    assert output["categories"]["2"] == {"category": "bug", "confidence": "high", "reason": "test verdict"}
    assert output["failures"] == []
    assert "categorized_at" in output


def test_out_flag_overrides_the_default_path(tmp_path, monkeypatch):
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])
    out = tmp_path / "elsewhere" / "cats.json"

    _run_cli(monkeypatch, corpus, out=out)

    assert out.is_file()
    assert not (corpus / CATEGORIES_FILENAME).exists()


# --- failure handling ---


def test_unparseable_reply_is_recorded_as_a_failure_not_a_category(tmp_path, monkeypatch):
    comments = [_mined_comment(1, 10, "garbled comment")]
    corpus = _setup_corpus(tmp_path, comments)

    _run_cli(monkeypatch, corpus, replies={"garbled comment": "not json at all"})

    output = json.loads((corpus / CATEGORIES_FILENAME).read_text(encoding="utf-8"))
    assert output["categories"] == {}
    assert len(output["failures"]) == 1
    assert output["failures"][0]["id"] == 1
    assert output["failures"][0]["repo"] == "org/repo"
    assert output["failures"][0]["number"] == 1
    assert "error" in output["failures"][0]


def test_category_outside_the_four_is_a_failure_not_silently_accepted(tmp_path, monkeypatch):
    comments = [_mined_comment(1, 10, "weird comment")]
    corpus = _setup_corpus(tmp_path, comments)
    bad_reply = json.dumps({"category": "nitpick", "confidence": "high", "reason": "x"})

    _run_cli(monkeypatch, corpus, replies={"weird comment": bad_reply})

    output = json.loads((corpus / CATEGORIES_FILENAME).read_text(encoding="utf-8"))
    assert output["categories"] == {}
    assert len(output["failures"]) == 1
    assert "nitpick" in output["failures"][0]["error"]


def test_duplicate_comment_id_across_the_corpus_is_fatal(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, [_mined_comment(1, 10, "a")]))
    _write(corpus / "org__repo__2.json", _corpus_record(2, [_mined_comment(1, 20, "b")]))
    client = FakeCategorizeClient()
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)

    with pytest.raises(SystemExit, match="Duplicate human comment id"):
        cli.main(["--corpus", str(corpus), "--model", "test/categorizer"])


# --- categories flow into the eval pipeline ---


def test_categories_flow_through_normalize_and_metrics(tmp_path, monkeypatch):
    comments = [
        _mined_comment(1, 10, "this can NPE"),
        _mined_comment(2, 20, "please rename this variable"),
    ]
    corpus = _setup_corpus(tmp_path, comments)
    _run_cli(
        monkeypatch,
        corpus,
        replies={
            "this can NPE": json.dumps({"category": "bug", "confidence": "high", "reason": "r"}),
            "please rename this variable": json.dumps(
                {"category": "style", "confidence": "low", "reason": "r"}
            ),
        },
    )

    categories = load_categories(str(corpus))
    normalized = [normalize_human_comment(c, categories) for c in comments]
    assert normalized[0]["category"] == "bug"
    assert normalized[1]["category"] == "style"

    model_comments = [{"file": "src/Main.java", "line": 10, "comment": "possible NPE"}]

    def always_equivalent(_human, _model):
        return True, "same issue"

    from reviewlens.eval.corpus import EvalPR

    pr = EvalPR(repo="org/repo", number=1, human_comments=normalized, model_comments=model_comments)
    result = match_comments(pr.human_comments, pr.model_comments, always_equivalent)
    metrics = compute_metrics([(pr, result)])

    assert metrics.categories_available is True
    by_name = {c.category: c for c in metrics.by_category}
    assert by_name["bug"].total == 1
    assert by_name["bug"].matched == 1
    assert by_name["style"].total == 1
    assert by_name["style"].matched == 0


def test_load_eval_inputs_picks_up_categories_json(tmp_path, monkeypatch):
    comments = [_mined_comment(1, 10, "this can NPE")]
    corpus = _setup_corpus(tmp_path, comments)
    _run_cli(monkeypatch, corpus, default_category="bug")

    run = tmp_path / "run"
    _write(
        run / "run_meta.json",
        {
            "model": "test/model-x",
            "prompt": {"name": "review_v1", "version": 1, "sha256": "b" * 64, "params": {}},
            "corpus": str(corpus),
            "corpus_pr_count": 1,
            "started": "2026-08-19T00:00:00+00:00",
            "finished": "2026-08-19T00:10:00+00:00",
            "complete": True,
            "pr_summaries": [
                {"repo": "org/repo", "number": 1, "chunk_count": 1, "comment_count": 0,
                 "parse_error_count": 0, "providers": {}}
            ],
            "exclusions": [],
        },
    )

    inputs = load_eval_inputs(str(run))

    assert inputs.prs[0].human_comments[0]["category"] == "bug"


# --- regression guards ---


def test_corpus_without_categories_json_still_loads_as_unavailable(tmp_path):
    """No categorization run yet must keep working exactly as before T8."""
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "a comment")])

    categories = load_categories(str(corpus))
    assert categories == {}

    normalized = normalize_human_comment(_mined_comment(1, 10, "a comment"), categories)
    assert "category" not in normalized


def test_load_corpus_does_not_treat_categories_json_as_a_pr_record(tmp_path, monkeypatch):
    comments = [_mined_comment(1, 10, "this can NPE")]
    corpus = _setup_corpus(tmp_path, comments)
    _run_cli(monkeypatch, corpus, default_category="bug")

    records = load_corpus(str(corpus))

    assert list(records) == ["org__repo__1"]


# --- spot-check sample (T8's "spot check" half) ---


def _read_spotcheck(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_spotcheck_sample_is_not_written_unless_asked(tmp_path, monkeypatch):
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])
    _run_cli(monkeypatch, corpus)
    assert not (tmp_path / "sample.csv").exists()


def test_spotcheck_sample_covers_at_least_the_requested_rate(tmp_path, monkeypatch):
    """ceil, not round: 11 assignments at 0.20 must yield 3, never 2."""
    comments = [_mined_comment(i, i * 10, f"comment {i}") for i in range(1, 12)]
    corpus = _setup_corpus(tmp_path, comments)
    out = tmp_path / "sample.csv"

    _run_cli(monkeypatch, corpus, spotcheck_out=out)

    rows = _read_spotcheck(out)
    assert len(rows) == 3
    assert len(rows) / len(comments) >= 0.20


def test_spotcheck_sample_is_reproducible_from_the_seed(tmp_path, monkeypatch):
    """A spot check nobody can reproduce is not evidence."""
    comments = [_mined_comment(i, i * 10, f"comment {i}") for i in range(1, 21)]
    corpus = _setup_corpus(tmp_path, comments)
    first, second, other = tmp_path / "a.csv", tmp_path / "b.csv", tmp_path / "c.csv"

    _run_cli(monkeypatch, corpus, spotcheck_out=first, seed=7)
    _run_cli(monkeypatch, corpus, spotcheck_out=second, seed=7)
    _run_cli(monkeypatch, corpus, spotcheck_out=other, seed=8)

    assert first.read_bytes() == second.read_bytes()
    ids = lambda p: [r["comment_id"] for r in _read_spotcheck(p)]
    assert ids(first) != ids(other)


def test_spotcheck_columns_for_the_human_are_always_blank(tmp_path, monkeypatch):
    """Pre-filling these would put the tool's answer where a human judgment goes."""
    comments = [_mined_comment(i, i * 10, f"comment {i}") for i in range(1, 6)]
    corpus = _setup_corpus(tmp_path, comments)
    out = tmp_path / "sample.csv"

    _run_cli(monkeypatch, corpus, spotcheck_out=out)

    rows = _read_spotcheck(out)
    assert rows
    for row in rows:
        assert row["human_category"] == ""
        assert row["human_agrees"] == ""
        assert row["notes"] == ""
        assert row["assigned_category"] == "bug"


def test_spotcheck_row_links_back_to_the_real_comment(tmp_path, monkeypatch):
    """The checker has to be able to open the PR and read the original."""
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])
    out = tmp_path / "sample.csv"

    _run_cli(monkeypatch, corpus, spotcheck_out=out)

    row = _read_spotcheck(out)[0]
    assert row["repo"] == "org/repo"
    assert row["pr_url"] == "https://github.com/org/repo/pull/1"
    assert row["comment_url"].endswith("#discussion_r1")
    assert row["comment"] == "this can NPE"
    assert row["file"] == "src/Main.java"
    assert row["line"] == "10"


def test_spotcheck_sample_preserves_a_comment_body_with_a_newline_and_comma(tmp_path, monkeypatch):
    body = "first line, with a comma\nsecond line"
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, body)])
    out = tmp_path / "sample.csv"

    _run_cli(monkeypatch, corpus, spotcheck_out=out)

    assert _read_spotcheck(out)[0]["comment"] == body


# --- offline mode / --only-ids / via ---


def test_offline_answers_without_offline_requests_exits_with_error(tmp_path, monkeypatch):
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])
    answers = tmp_path / "answers.jsonl"
    answers.write_text("", encoding="utf-8")
    client = FakeCategorizeClient()
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)

    with pytest.raises(SystemExit, match="--offline-answers requires --offline-requests"):
        cli.main(
            [
                "--corpus", str(corpus),
                "--model", "test/categorizer",
                "--offline-answers", str(answers),
            ]
        )


def test_only_ids_restricts_which_comments_are_categorized(tmp_path, monkeypatch):
    comments = [
        _mined_comment(1, 10, "this can NPE"),
        _mined_comment(2, 20, "please rename this variable"),
    ]
    corpus = _setup_corpus(tmp_path, comments)
    only_ids = tmp_path / "only_ids.txt"
    only_ids.write_text("# comment to keep\n1\n\n", encoding="utf-8")

    client = _run_cli(monkeypatch, corpus, only_ids=only_ids)

    assert client.calls == 1
    output = json.loads((corpus / CATEGORIES_FILENAME).read_text(encoding="utf-8"))
    assert list(output["categories"]) == ["1"]
    assert output["failures"] == []


def test_via_is_openrouter_by_default(tmp_path, monkeypatch):
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])

    _run_cli(monkeypatch, corpus)

    output = json.loads((corpus / CATEGORIES_FILENAME).read_text(encoding="utf-8"))
    assert output["via"] == "openrouter"


def test_via_is_claude_code_subagent_in_offline_mode(tmp_path, monkeypatch):
    corpus = _setup_corpus(tmp_path, [_mined_comment(1, 10, "this can NPE")])
    requests_path = tmp_path / "requests.jsonl"

    # No FakeCategorizeClient/OpenRouterClient patch needed: --offline-requests
    # makes the CLI build a real (network-free) OfflineClient itself.
    cli.main(
        [
            "--corpus", str(corpus),
            "--model", "test/categorizer",
            "--offline-requests", str(requests_path),
        ]
    )

    output = json.loads((corpus / CATEGORIES_FILENAME).read_text(encoding="utf-8"))
    assert output["via"] == "claude-code-subagent"
    # Pass 1: no answers yet, so the request was recorded and the reply
    # (content: None) is an unparseable failure rather than a fabricated category.
    assert output["categories"] == {}
    assert len(output["failures"]) == 1
    assert requests_path.exists()
