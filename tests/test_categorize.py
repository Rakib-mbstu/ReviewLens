from __future__ import annotations

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


def _run_cli(monkeypatch, corpus, out=None, replies=None, default_category="bug"):
    client = FakeCategorizeClient(replies=replies, default_category=default_category)
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)
    args = ["--corpus", str(corpus), "--model", "test/categorizer"]
    if out is not None:
        args += ["--out", str(out)]
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
