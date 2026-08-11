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
