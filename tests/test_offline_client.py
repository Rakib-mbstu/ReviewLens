import json

import pytest

from reviewlens.openrouter import cache_key, content_is_missing
from reviewlens.review.answers import load_answers
from reviewlens.review.engine import parse_review_response
from reviewlens.review.offline_client import OfflineClient

MESSAGES = [
    {"role": "system", "content": "You are a reviewer."},
    {"role": "user", "content": "File: Foo.java (1-5)\n+ some diff"},
]
PARAMS = {"temperature": 0.0}


def _requests_lines(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# --- pass 1: recording ---


def test_pass1_records_request_and_returns_content_missing_response(tmp_path):
    requests_path = tmp_path / "requests.jsonl"
    client = OfflineClient(str(requests_path))

    response = client.complete("test/model-x", MESSAGES, **PARAMS)

    assert content_is_missing(response)
    lines = _requests_lines(requests_path)
    assert len(lines) == 1
    assert lines[0]["model"] == "test/model-x"
    assert lines[0]["system"] == "You are a reviewer."
    assert lines[0]["user"] == "File: Foo.java (1-5)\n+ some diff"
    assert lines[0]["key"] == cache_key("test/model-x", MESSAGES, PARAMS)


def test_pass1_works_with_no_answers_file_yet(tmp_path):
    """A missing answers file must not be an error: pass 1 always runs before
    any answers exist."""
    requests_path = tmp_path / "requests.jsonl"
    missing_answers = tmp_path / "does_not_exist.jsonl"

    client = OfflineClient(str(requests_path), answers_path=str(missing_answers))
    response = client.complete("test/model-x", MESSAGES, **PARAMS)

    assert content_is_missing(response)
    assert client.answered == 0
    assert client.recorded == 1


# --- pass 2: answering ---


def test_pass2_returns_answer_text_parseable_by_the_engine(tmp_path):
    requests_path = tmp_path / "requests.jsonl"
    answers_path = tmp_path / "answers.jsonl"
    key = cache_key("test/model-x", MESSAGES, PARAMS)
    body = [{"file": "Foo.java", "line": 3, "category": "bug", "severity": "high", "comment": "npe"}]
    with open(answers_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "content": json.dumps(body)}) + "\n")

    client = OfflineClient(str(requests_path), answers_path=str(answers_path))
    response = client.complete("test/model-x", MESSAGES, **PARAMS)

    assert not content_is_missing(response)
    comments, errors = parse_review_response(response)
    assert errors == []
    assert comments == body
    assert client.answered == 1
    assert client.recorded == 0
    # Pass 2 must not write requests for keys it already answered.
    assert not requests_path.exists()


# --- key stability ---


def test_same_request_recorded_in_pass1_is_found_in_pass2(tmp_path):
    requests_path = tmp_path / "requests.jsonl"
    OfflineClient(str(requests_path)).complete("test/model-x", MESSAGES, **PARAMS)

    recorded_key = _requests_lines(requests_path)[0]["key"]

    answers_path = tmp_path / "answers.jsonl"
    with open(answers_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": recorded_key, "content": "[]"}) + "\n")

    pass2 = OfflineClient(tmp_path / "requests2.jsonl", answers_path=str(answers_path))
    response = pass2.complete("test/model-x", MESSAGES, **PARAMS)

    assert pass2.answered == 1
    assert not content_is_missing(response)


def test_different_params_produce_a_different_key_and_are_not_found(tmp_path):
    requests_path = tmp_path / "requests.jsonl"
    OfflineClient(str(requests_path)).complete("test/model-x", MESSAGES, temperature=0.0)

    recorded_key = _requests_lines(requests_path)[0]["key"]

    answers_path = tmp_path / "answers.jsonl"
    with open(answers_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": recorded_key, "content": "[]"}) + "\n")

    pass2 = OfflineClient(str(tmp_path / "requests2.jsonl"), answers_path=str(answers_path))
    # Different params -> different cache_key -> not in the answers dict.
    response = pass2.complete("test/model-x", MESSAGES, temperature=1.0)

    assert pass2.answered == 0
    assert pass2.recorded == 1
    assert content_is_missing(response)


# --- deduplication ---


def test_duplicate_chunk_in_one_run_is_recorded_once(tmp_path):
    requests_path = tmp_path / "requests.jsonl"
    client = OfflineClient(str(requests_path))

    client.complete("test/model-x", MESSAGES, **PARAMS)
    client.complete("test/model-x", MESSAGES, **PARAMS)
    client.complete("test/model-x", MESSAGES, **PARAMS)

    assert len(_requests_lines(requests_path)) == 1
    assert client.recorded == 1


# --- answered / recorded counts across a mixed run ---


def test_answered_and_recorded_counts_in_a_mixed_run(tmp_path):
    messages_a = MESSAGES
    messages_b = [
        {"role": "system", "content": "You are a reviewer."},
        {"role": "user", "content": "File: Bar.java (1-5)\n+ other diff"},
    ]
    answered_key = cache_key("test/model-x", messages_a, PARAMS)

    answers_path = tmp_path / "answers.jsonl"
    with open(answers_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": answered_key, "content": "[]"}) + "\n")

    requests_path = tmp_path / "requests.jsonl"
    client = OfflineClient(str(requests_path), answers_path=str(answers_path))

    client.complete("test/model-x", messages_a, **PARAMS)  # answered
    client.complete("test/model-x", messages_b, **PARAMS)  # unanswered, recorded
    client.complete("test/model-x", messages_b, **PARAMS)  # unanswered, duplicate
    client.complete("test/model-x", messages_a, **PARAMS)  # answered again

    assert client.answered == 2
    assert client.recorded == 1
    assert len(_requests_lines(requests_path)) == 1


# --- load_answers ---


def test_load_answers_raises_on_missing_key_naming_the_line_number(tmp_path):
    path = tmp_path / "answers.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": "abc", "content": "ok"}) + "\n")
        f.write(json.dumps({"content": "no key here"}) + "\n")

    with pytest.raises(ValueError) as excinfo:
        load_answers(str(path))

    assert "2" in str(excinfo.value)


def test_load_answers_raises_on_missing_content_naming_the_line_number(tmp_path):
    path = tmp_path / "answers.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": "abc"}) + "\n")

    with pytest.raises(ValueError) as excinfo:
        load_answers(str(path))

    assert "1" in str(excinfo.value)


def test_load_answers_returns_key_to_content_mapping(tmp_path):
    path = tmp_path / "answers.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"key": "k1", "content": "c1"}) + "\n")
        f.write(json.dumps({"key": "k2", "content": "c2"}) + "\n")

    assert load_answers(str(path)) == {"k1": "c1", "k2": "c2"}
