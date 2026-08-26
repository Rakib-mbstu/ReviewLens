import json

import pytest

from reviewlens.eval.corpus import (
    load_categorization_meta,
    load_corpus,
    load_error_stats,
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


# --- categorization metadata (T8): provenance + coverage for the report ---


def _categories_json(corpus_dir, categorized, low_confidence, failures):
    """Write a categories.json fixture with distinctive, deliberately chosen
    counts so tests can tell "computed from data" apart from "hardcoded"."""
    categories = {}
    for i in range(categorized - low_confidence):
        categories[str(1000 + i)] = {"category": "bug", "confidence": "high", "reason": "r"}
    for i in range(low_confidence):
        categories[str(2000 + i)] = {"category": "design", "confidence": "low", "reason": "r"}
    payload = {
        "categorized_at": "2026-08-22T19:19:28+00:00",
        "model": "test/categorizer",
        "prompt": {"name": "categorize_v1", "version": 1, "sha256": "c" * 64},
        "categories": categories,
        "failures": [{"id": 3000 + i, "error": "parse"} for i in range(failures)],
    }
    _write(corpus_dir / "categories.json", payload)


def test_load_categorization_meta_is_none_without_categories_json(tmp_path):
    """No categorization run yet must keep reporting as unavailable, not
    raise and not fabricate a stub."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()

    assert load_categorization_meta(str(corpus)) is None


def test_load_categorization_meta_computes_counts_from_the_file(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    _categories_json(corpus, categorized=13, low_confidence=5, failures=2)

    meta = load_categorization_meta(str(corpus))

    assert meta.model == "test/categorizer"
    assert meta.prompt_name == "categorize_v1"
    assert meta.prompt_version == 1
    assert meta.prompt_sha256 == "c" * 64
    assert meta.categorized_count == 13
    assert meta.low_confidence_count == 5
    assert meta.failure_count == 2


def test_load_eval_inputs_carries_categorization_metadata(tmp_path):
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    _categories_json(corpus, categorized=4, low_confidence=1, failures=0)
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1)], corpus))

    inputs = load_eval_inputs(str(run))

    assert inputs.categorization is not None
    assert inputs.categorization.categorized_count == 4
    assert inputs.categorization.low_confidence_count == 1


# --- parse-error stats: chunk loss vs. malformed items, provider vs. model ---


def _error(error, chunk_index, raw_content="{}"):
    """One errors.json record, in the shape reviewlens.review.engine writes."""
    return {"error": error, "raw_content": raw_content, "chunk_index": chunk_index}


def _model_comment(chunk_index, line=10, comment="ok"):
    return {"file": "src/Main.java", "line": line, "comment": comment, "chunk_index": chunk_index}


def test_missing_errors_json_is_zero_stats(tmp_path):
    run = tmp_path / "run"
    (run / "org__repo__1").mkdir(parents=True)

    stats = load_error_stats(str(run), "org__repo__1", model_comments=[])

    assert stats.parse_error_items == 0
    assert stats.error_chunk_count == 0
    assert stats.lost_chunk_count == 0
    assert stats.provider_error_items == 0
    assert stats.model_error_items == 0


def test_two_malformed_items_from_one_chunk_count_as_one_error_chunk(tmp_path):
    """parse_review_response can reject several elements from one chunk's
    reply; error_chunk_count must count the chunk once, not once per item."""
    run = tmp_path / "run"
    _write(
        run / "org__repo__1" / "errors.json",
        [
            _error("invalid JSON (Expecting value)", chunk_index=5),
            _error("invalid 'category' (...): 'test'", chunk_index=5),
        ],
    )

    stats = load_error_stats(str(run), "org__repo__1", model_comments=[])

    assert stats.parse_error_items == 2
    assert stats.error_chunk_count == 1
    assert stats.lost_chunk_count == 1


def test_a_chunk_with_an_error_and_a_valid_comment_is_not_lost(tmp_path):
    """engine.py's parse_review_response returns valid comments and errors
    for the same chunk together, so an errored chunk that still produced a
    comment was not lost — only chunks with zero surviving output are."""
    run = tmp_path / "run"
    _write(run / "org__repo__1" / "errors.json", [_error("invalid JSON (Expecting value)", chunk_index=5)])
    model_comments = [_model_comment(chunk_index=5)]

    stats = load_error_stats(str(run), "org__repo__1", model_comments)

    assert stats.error_chunk_count == 1
    assert stats.lost_chunk_count == 0


def test_content_missing_message_classifies_as_provider_caused(tmp_path):
    """The exact message engine.py:134 writes when the provider returns a
    null content field despite the model having been billed and having
    generated tokens."""
    run = tmp_path / "run"
    _write(
        run / "org__repo__1" / "errors.json",
        [_error("response content was NoneType, not a string", chunk_index=0)],
    )

    stats = load_error_stats(str(run), "org__repo__1", model_comments=[])

    assert stats.provider_error_items == 1
    assert stats.model_error_items == 0


def test_invalid_json_and_invalid_category_classify_as_model_caused(tmp_path):
    run = tmp_path / "run"
    _write(
        run / "org__repo__1" / "errors.json",
        [
            _error("invalid JSON (Expecting value)", chunk_index=0),
            _error("invalid 'category' (must be one of ['bug']): 'test'", chunk_index=1),
        ],
    )

    stats = load_error_stats(str(run), "org__repo__1", model_comments=[])

    assert stats.provider_error_items == 0
    assert stats.model_error_items == 2


def test_load_eval_inputs_carries_error_stats_through_to_evalpr(tmp_path):
    """End-to-end: load_eval_inputs must actually call load_error_stats and
    attach its results to each EvalPR, not just parse_error_count/chunk_count."""
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1, chunk_count=3, parse_error_count=1)], corpus))
    _write(
        run / "org__repo__1" / "errors.json",
        [_error("response content was NoneType, not a string", chunk_index=2)],
    )
    _write(run / "org__repo__1" / "comments.json", [])

    pr = load_eval_inputs(str(run)).prs[0]

    assert pr.parse_error_items == 1
    assert pr.error_chunk_count == 1
    assert pr.lost_chunk_count == 1
    assert pr.provider_error_items == 1
    assert pr.model_error_items == 0


def test_load_eval_inputs_categorization_is_none_without_categories_json(tmp_path):
    """Regression guard: a corpus with no categories.json must keep loading
    and reporting categorization as unavailable, exactly as before T8."""
    corpus = tmp_path / "corpus"
    _write(corpus / "org__repo__1.json", _corpus_record(1, []))
    run = tmp_path / "run"
    _write(run / "run_meta.json", _run_meta([_summary(1)], corpus))

    inputs = load_eval_inputs(str(run))

    assert inputs.categorization is None
