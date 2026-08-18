import json

import pytest

from reviewlens.eval.corpus import (
    load_corpus,
    load_eval_inputs,
    load_run_meta,
    normalize_human_comment,
    pr_key,
)


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _corpus_record(number: int, comments):
    return {
        "repo": "org/repo",
        "number": number,
        "human_comments": comments,
    }


def _mined_comment(line: int, body: str, comment_id: int = 1):
    """A human comment in the shape reviewlens.mine actually writes."""
    return {
        "id": comment_id,
        "path": "src/Main.java",
        "line": line,
        "raw_line": line,
        "original_line": line,
        "body": body,
        "author": "reviewer",
        "url": f"https://github.com/org/repo/pull/1#discussion_r{comment_id}",
    }


def _run_meta(summaries, corpus_dir, complete=True):
    return {
        "model": "test/model-x",
        "prompt": {"name": "review_v1", "version": 1, "sha256": "0" * 64, "params": {}},
        "corpus": str(corpus_dir),
        "corpus_pr_count": len(summaries),
        "started": "2026-08-19T00:00:00+00:00",
        "finished": "2026-08-19T00:10:00+00:00" if complete else None,
        "complete": complete,
        "pr_summaries": summaries,
        "exclusions": [],
    }


def _summary(number, chunk_count=2, parse_error_count=0):
    return {
        "repo": "org/repo",
        "number": number,
        "chunk_count": chunk_count,
        "comment_count": 1,
        "parse_error_count": parse_error_count,
        "providers": {"TestProvider": chunk_count},
    }


# --- the mine -> eval key seam: {path, line, body} -> {file, line, comment} ---


def test_normalize_renames_the_keys_matching_actually_reads():
    """The corpus and the matcher use different names for the same three
    fields; if this rename is ever dropped, every candidate lookup fails and
    recall reads as a flat 0% that looks like a result rather than a bug."""
    normalized = normalize_human_comment(_mined_comment(42, "please rename this"))

    assert normalized["file"] == "src/Main.java"
    assert normalized["line"] == 42
    assert normalized["comment"] == "please rename this"


def test_normalize_keeps_identity_fields_for_manual_verification():
    normalized = normalize_human_comment(_mined_comment(42, "body", comment_id=99))

    assert normalized["id"] == 99
    assert normalized["author"] == "reviewer"
    assert normalized["url"].endswith("discussion_r99")


def test_normalized_comments_are_matchable(tmp_path):
    """End-to-end on the real rule: a normalized human comment and a model
    comment two lines apart are candidates."""
    from reviewlens.eval.matching import is_candidate

    human = normalize_human_comment(_mined_comment(100, "null check missing"))
    model = {"file": "src/Main.java", "line": 102, "comment": "possible NPE"}

    assert is_candidate(human, model) is True


# --- loading ---


def test_load_corpus_skips_the_mining_manifest(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    _write(corpus / "manifest.json", {"projects": ["junit5"]})

    records = load_corpus(str(corpus))

    assert list(records) == ["org__repo__1"]


def test_load_corpus_rejects_a_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError, match="Corpus directory not found"):
        load_corpus(str(tmp_path / "nope"))


def test_load_corpus_rejects_an_empty_corpus(tmp_path):
    """An empty denominator would surface as a fabricated 0% recall."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()

    with pytest.raises(FileNotFoundError, match="holds no PR files"):
        load_corpus(str(corpus))


def test_run_without_run_meta_cannot_be_evaluated(tmp_path):
    """The aborted first corpus run left outputs but no metadata; a report
    must be reproducible from the run directory alone, so that is fatal."""
    run = tmp_path / "run"
    run.mkdir()

    with pytest.raises(FileNotFoundError, match="reproducible from the run directory"):
        load_run_meta(str(run))


def test_load_eval_inputs_pairs_human_and_model_comments(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, [_mined_comment(10, "human note")]))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1, chunk_count=3, parse_error_count=1)], corpus))
    _write(
        run / "org__repo__1" / "comments.json",
        [{"file": "src/Main.java", "line": 11, "category": "bug", "severity": "high", "comment": "model note"}],
    )

    inputs = load_eval_inputs(str(run))

    assert len(inputs.prs) == 1
    pr = inputs.prs[0]
    assert pr.human_comments[0]["comment"] == "human note"
    assert pr.model_comments[0]["comment"] == "model note"
    assert pr.chunk_count == 3
    assert pr.parse_error_count == 1


def test_load_eval_inputs_reads_the_corpus_recorded_by_the_run(tmp_path):
    """The report is tied to the corpus the run used, not to whatever is on
    disk when the report is generated."""
    corpus = tmp_path / "recorded-corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1)], corpus))

    assert load_eval_inputs(str(run)).corpus_dir == str(corpus)


def test_load_eval_inputs_requires_a_corpus_from_somewhere(tmp_path):
    run = tmp_path / "run"
    meta = _run_meta([_summary(1)], tmp_path / "corpus")
    del meta["corpus"]
    _write(run / "run_meta.json", meta)

    with pytest.raises(FileNotFoundError, match="does not record which corpus"):
        load_eval_inputs(str(run))


def test_missing_comments_json_reads_as_no_model_comments(tmp_path):
    """A PR the run never finished contributes no model comments rather than
    crashing the report."""
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, [_mined_comment(10, "human note")]))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1)], corpus))

    assert load_eval_inputs(str(run)).prs[0].model_comments == []


def test_pr_reviewed_but_absent_from_the_corpus_is_reported(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1), _summary(2)], corpus))

    inputs = load_eval_inputs(str(run))

    assert inputs.missing_from_corpus == ["org__repo__2"]


def test_corpus_pr_the_run_skipped_is_reported(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    _write(corpus / "org__repo__2.json", _corpus_record(2, []))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1)], corpus))

    inputs = load_eval_inputs(str(run))

    assert inputs.missing_from_run == ["org__repo__2"]
    assert len(inputs.prs) == 1


def test_pr_key_matches_the_run_directory_naming():
    assert pr_key("junit-team/junit5", 4629) == "junit-team__junit5__4629"
