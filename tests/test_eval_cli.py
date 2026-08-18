from __future__ import annotations

import json

import pytest

import reviewlens.eval.__main__ as cli


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class FakeJudgeClient:
    """Stands in for OpenRouterClient so the CLI never touches the network.

    Returns the rubric's own reply shape, so the CLI is exercised through the
    real parse path rather than a shortcut.
    """

    def __init__(self, equivalent=True, **kwargs):
        self.equivalent = equivalent
        self.calls = 0

    def complete(self, model, messages, **params):
        self.calls += 1
        body = json.dumps({"equivalent": self.equivalent, "reason": "test verdict"})
        return {
            "provider": "TestProvider",
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": body}}],
        }

    def close(self):
        pass


def _setup(tmp_path, human_line=10, model_line=11):
    corpus = tmp_path / "corpus"
    _write(
        corpus / "org__repo__1.json",
        {
            "repo": "org/repo",
            "number": 1,
            "human_comments": [
                {
                    "id": 1,
                    "path": "src/Main.java",
                    "line": human_line,
                    "body": "this can be null",
                    "author": "reviewer",
                    "url": "https://github.com/org/repo/pull/1#discussion_r1",
                }
            ],
        },
    )
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
                {"repo": "org/repo", "number": 1, "chunk_count": 4, "comment_count": 1,
                 "parse_error_count": 0, "providers": {"TestProvider": 4}}
            ],
            "exclusions": [],
        },
    )
    _write(
        run / "org__repo__1" / "comments.json",
        [{"file": "src/Main.java", "line": model_line, "category": "bug", "severity": "high",
          "comment": "possible NPE"}],
    )
    return corpus, run


def _run_cli(monkeypatch, run, report, equivalent=True):
    client = FakeJudgeClient(equivalent=equivalent)
    monkeypatch.setattr(cli, "OpenRouterClient", lambda **kwargs: client)
    cli.main(["--run", str(run), "--report", str(report), "--judge-model", "test/judge"])
    return client


def test_eval_cli_writes_a_report_with_real_numbers(tmp_path, monkeypatch):
    _corpus, run = _setup(tmp_path)
    report = tmp_path / "reports" / "model-x.md"

    client = _run_cli(monkeypatch, run, report)

    assert client.calls == 1
    text = report.read_text(encoding="utf-8")
    assert "| **Recall** | **100.0%** |" in text
    assert "| Human comments (denominator) | 1 |" in text


def test_eval_cli_persists_an_auditable_match_record(tmp_path, monkeypatch):
    """A report that cannot be re-derived comment by comment is not evidence."""
    _corpus, run = _setup(tmp_path)

    _run_cli(monkeypatch, run, tmp_path / "report.md")

    record = json.loads((run / "eval_matches.json").read_text(encoding="utf-8"))
    assert record[0]["repo"] == "org/repo"
    assert record[0]["matches"][0]["human"]["comment"] == "this can be null"
    assert record[0]["matches"][0]["model"]["comment"] == "possible NPE"
    assert record[0]["judge_log"][0]["equivalent"] is True


def test_rejected_verdicts_are_kept_in_the_judge_log(tmp_path, monkeypatch):
    """A near-miss that the judge rejected must stay inspectable, not vanish."""
    _corpus, run = _setup(tmp_path)

    _run_cli(monkeypatch, run, tmp_path / "report.md", equivalent=False)

    record = json.loads((run / "eval_matches.json").read_text(encoding="utf-8"))
    assert record[0]["matches"] == []
    assert record[0]["judge_log"][0]["equivalent"] is False
    assert len(record[0]["unmatched_human"]) == 1
    assert len(record[0]["unmatched_model"]) == 1


def test_out_of_window_pair_is_never_sent_to_the_judge(tmp_path, monkeypatch):
    """The +/-3 line pre-filter keeps paid judge calls off pairs that could
    never match."""
    _corpus, run = _setup(tmp_path, human_line=10, model_line=20)

    client = _run_cli(monkeypatch, run, tmp_path / "report.md")

    assert client.calls == 0


def test_run_missing_run_meta_exits_with_an_actionable_message(tmp_path, monkeypatch, capsys):
    run = tmp_path / "run"
    run.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--run", str(run), "--report", str(tmp_path / "r.md"), "--judge-model", "m"])

    assert "run_meta.json" in str(excinfo.value)


def test_run_reviewing_a_pr_outside_the_corpus_refuses_to_report(tmp_path, monkeypatch):
    """Otherwise recall would be computed against the wrong denominator."""
    corpus, run = _setup(tmp_path)
    meta = json.loads((run / "run_meta.json").read_text(encoding="utf-8"))
    meta["pr_summaries"].append(
        {"repo": "org/repo", "number": 99, "chunk_count": 1, "comment_count": 0,
         "parse_error_count": 0, "providers": {}}
    )
    _write(run / "run_meta.json", meta)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--run", str(run), "--report", str(tmp_path / "r.md"), "--judge-model", "m"])

    assert "wrong denominator" in str(excinfo.value)
