import json

import pytest

from reviewlens.mine.miner import MANIFEST_FILENAME
from reviewlens.review.__main__ import _load_corpus_entries


def _write(dir_path, name: str, payload) -> None:
    (dir_path / name).write_text(json.dumps(payload), encoding="utf-8")


def test_load_corpus_entries_skips_the_mining_manifest(tmp_path):
    """A real mined corpus always contains manifest.json alongside the PR
    files; treating it as a PR entry aborted the first full review run."""
    _write(tmp_path, "junit-team__junit5__4629.json", {"repo": "junit-team/junit5", "number": 4629})
    _write(tmp_path, MANIFEST_FILENAME, {"mined_at": "2026-08-06", "criteria": {}, "prs": []})

    entries = _load_corpus_entries(str(tmp_path))

    assert entries == [{"repo": "junit-team/junit5", "number": 4629}]


def test_load_corpus_entries_still_rejects_a_malformed_pr_file(tmp_path):
    """Skipping the manifest must not soften the loud failure for anything
    else — a corpus with a broken PR file must never quietly review fewer
    PRs than it claims to hold."""
    _write(tmp_path, "junit-team__junit5__4629.json", {"repo": "junit-team/junit5", "number": 4629})
    _write(tmp_path, "broken.json", {"repo": "junit-team/junit5"})

    with pytest.raises(SystemExit) as excinfo:
        _load_corpus_entries(str(tmp_path))

    assert "broken.json" in str(excinfo.value)


def test_load_corpus_entries_rejects_a_corpus_holding_only_a_manifest(tmp_path):
    """Mining that qualified no PRs still writes a manifest; the resulting
    corpus is empty and must fail with the 'run mine first' message rather
    than starting a zero-PR run that looks like a success."""
    _write(tmp_path, MANIFEST_FILENAME, {"mined_at": "2026-08-06", "criteria": {}, "prs": []})

    with pytest.raises(SystemExit) as excinfo:
        _load_corpus_entries(str(tmp_path))

    assert "no PR JSON files" in str(excinfo.value)


# --- run_meta.json is written incrementally, so an aborted run is not opaque ---


def _stub_run(monkeypatch, review_side_effect):
    """Neutralise the CLI's network dependencies, leaving only its run_meta
    bookkeeping under test. review_side_effect(entry_index) either returns a
    PR summary or raises."""
    import reviewlens.review.__main__ as cli

    class _NoopClient:
        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

    calls = {"n": 0}

    def fake_review_pr(*args, **kwargs):
        index = calls["n"]
        calls["n"] += 1
        return review_side_effect(index)

    monkeypatch.setattr(cli, "GitHubClient", _NoopClient)
    monkeypatch.setattr(cli, "OpenRouterClient", _NoopClient)
    monkeypatch.setattr(cli, "fetch_pr_snapshot", lambda *a, **k: object())
    monkeypatch.setattr(cli, "review_pr", fake_review_pr)
    return cli


def _summary(number: int) -> dict:
    return {
        "repo": "org/repo",
        "number": number,
        "chunk_count": 1,
        "comment_count": 1,
        "parse_error_count": 0,
        "providers": {"TestProvider": 1},
    }


def test_run_meta_records_a_run_that_dies_partway_through(tmp_path, monkeypatch):
    """The first corpus run aborted mid-loop and left outputs with no metadata
    at all. A partial run must still describe itself — and must not pass for a
    complete one that merely reviewed fewer PRs."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for number in (1, 2, 3):
        _write(corpus, f"pr_{number}.json", {"repo": "org/repo", "number": number})

    def side_effect(index):
        if index == 1:
            raise KeyboardInterrupt
        return _summary(index + 1)

    cli = _stub_run(monkeypatch, side_effect)
    out = tmp_path / "run"

    with pytest.raises(KeyboardInterrupt):
        cli.main(["--corpus", str(corpus), "--model", "test/model-x", "--out", str(out)])

    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["complete"] is False
    assert meta["finished"] is None
    assert meta["corpus_pr_count"] == 3
    assert [s["number"] for s in meta["pr_summaries"]] == [1]
    assert meta["model"] == "test/model-x"
    assert meta["prompt"]["name"] == "review_v1"


def test_run_meta_marks_a_finished_run_complete(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for number in (1, 2):
        _write(corpus, f"pr_{number}.json", {"repo": "org/repo", "number": number})

    cli = _stub_run(monkeypatch, lambda index: _summary(index + 1))
    out = tmp_path / "run"

    cli.main(["--corpus", str(corpus), "--model", "test/model-x", "--out", str(out)])

    meta = json.loads((out / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["complete"] is True
    assert meta["finished"] is not None
    assert [s["number"] for s in meta["pr_summaries"]] == [1, 2]
