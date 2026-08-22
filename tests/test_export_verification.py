from __future__ import annotations

import csv
import json
import math

import pytest

import reviewlens.eval.export_verification as export_verification


def _match(file, human_line, human_comment, model_line, model_comment, reason="looks right", human_id=None):
    return {
        "human": {
            "file": file,
            "line": human_line,
            "comment": human_comment,
            "id": human_id if human_id is not None else human_line,
            "url": f"https://github.com/org/repo/pull/1#discussion_r{human_line}",
            "author": "reviewer",
        },
        "model": {"file": file, "line": model_line, "category": "bug", "severity": "high", "comment": model_comment},
        "reason": reason,
    }


def _unmatched_model(file, line, comment, category="style", severity="low"):
    return {"file": file, "line": line, "category": category, "severity": severity, "comment": comment}


def _pr_record(repo="org/repo", number=1, matches=None, unmatched_model=None):
    return {
        "repo": repo,
        "number": number,
        "matches": matches or [],
        "unmatched_human": [],
        "unmatched_model": unmatched_model or [],
        "judge_log": [],
    }


def _write(run_dir, records):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / export_verification.MATCHES_FILENAME).write_text(json.dumps(records), encoding="utf-8")


def _read_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_populations_are_sampled_independently_not_pooled(tmp_path):
    """96 matches vs. 4 unmatched_model: a single pooled 20% sample (~20 rows
    out of 100) could easily land 0 of the 4 unmatched_model comments by
    chance. Independent sampling must not let that happen."""
    matches = [
        _match("src/A.java", 10 + i, f"human comment {i}", 10 + i, f"model comment {i}")
        for i in range(96)
    ]
    unmatched = [_unmatched_model("src/A.java", 200 + i, f"unmatched {i}") for i in range(4)]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches, unmatched_model=unmatched)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv)])

    rows = _read_rows(out_csv)
    match_rows = [r for r in rows if r["kind"] == "match"]
    unmatched_rows = [r for r in rows if r["kind"] == "unmatched_model"]

    assert len(match_rows) == math.ceil(96 * 0.20)
    assert len(unmatched_rows) == math.ceil(4 * 0.20)
    assert len(unmatched_rows) >= 1
    assert len(unmatched_rows) / 4 >= 0.20


def test_sample_size_uses_ceil_not_round(tmp_path):
    """11 at 0.20 must yield 3 (ceil), not 2 (round)."""
    matches = [
        _match("src/A.java", 10 + i, f"human {i}", 10 + i, f"model {i}") for i in range(11)
    ]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv), "--sample-rate", "0.20"])

    rows = _read_rows(out_csv)
    assert len(rows) == 3


def test_sample_ids_is_deterministic_for_a_fixed_seed():
    ids = sorted(f"id-{i}" for i in range(50))

    first = export_verification.sample_ids(ids, 0.20, seed=20260823)
    second = export_verification.sample_ids(ids, 0.20, seed=20260823)

    assert first == second


def test_sample_ids_differs_across_seeds():
    ids = sorted(f"id-{i}" for i in range(50))

    a = export_verification.sample_ids(ids, 0.20, seed=1)
    b = export_verification.sample_ids(ids, 0.20, seed=2)

    assert set(a) != set(b)


def test_cli_output_is_identical_across_runs_with_the_same_seed(tmp_path):
    matches = [
        _match("src/A.java", 10 + i, f"human {i}", 10 + i, f"model {i}") for i in range(20)
    ]
    unmatched = [_unmatched_model("src/A.java", 300 + i, f"unmatched {i}") for i in range(10)]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches, unmatched_model=unmatched)])

    out_a = tmp_path / "a.csv"
    out_b = tmp_path / "b.csv"
    export_verification.main(["--run", str(run_dir), "--out", str(out_a), "--seed", "42"])
    export_verification.main(["--run", str(run_dir), "--out", str(out_b), "--seed", "42"])

    assert out_a.read_text(encoding="utf-8") == out_b.read_text(encoding="utf-8")

    out_c = tmp_path / "c.csv"
    export_verification.main(["--run", str(run_dir), "--out", str(out_c), "--seed", "43"])
    assert out_c.read_text(encoding="utf-8") != out_a.read_text(encoding="utf-8")


def test_human_verdict_and_notes_columns_are_always_present_and_empty(tmp_path):
    matches = [_match("src/A.java", 10, "human comment", 10, "model comment")]
    unmatched = [_unmatched_model("src/A.java", 50, "unmatched comment")]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches, unmatched_model=unmatched)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv), "--sample-rate", "1.0"])

    rows = _read_rows(out_csv)
    assert len(rows) == 2
    for row in rows:
        assert "human_verdict" in row
        assert "human_notes" in row
        assert row["human_verdict"] == ""
        assert row["human_notes"] == ""


def test_comment_with_newline_and_comma_round_trips(tmp_path):
    tricky = "line one, with a comma\nline two, also a comma"
    matches = [_match("src/A.java", 10, tricky, 10, "model comment, also tricky\nsecond line")]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv), "--sample-rate", "1.0"])

    rows = _read_rows(out_csv)
    assert rows[0]["human_comment"] == tricky
    assert rows[0]["model_comment"] == "model comment, also tricky\nsecond line"


def test_unmatched_model_rows_have_empty_human_fields_and_unmatched_verdict(tmp_path):
    unmatched = [_unmatched_model("src/A.java", 50, "hallucinated issue")]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(unmatched_model=unmatched)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv), "--sample-rate", "1.0"])

    rows = _read_rows(out_csv)
    assert len(rows) == 1
    row = rows[0]
    assert row["kind"] == "unmatched_model"
    assert row["pipeline_verdict"] == "unmatched"
    assert row["human_line"] == ""
    assert row["human_comment"] == ""
    assert row["human_url"] == ""
    assert row["model_comment"] == "hallucinated issue"


def test_match_rows_have_matched_verdict_and_judge_reason(tmp_path):
    matches = [_match("src/A.java", 10, "human comment", 11, "model comment", reason="same NPE risk")]
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record(matches=matches)])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv), "--sample-rate", "1.0"])

    rows = _read_rows(out_csv)
    assert rows[0]["pipeline_verdict"] == "matched"
    assert rows[0]["judge_reason"] == "same NPE risk"
    assert rows[0]["human_comment"] == "human comment"
    assert rows[0]["human_url"] == "https://github.com/org/repo/pull/1#discussion_r10"


def test_missing_eval_matches_json_exits_with_an_actionable_message(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    with pytest.raises(SystemExit) as excinfo:
        export_verification.main(["--run", str(run_dir), "--out", str(tmp_path / "verify.csv")])

    assert "eval_matches.json" in str(excinfo.value)


def test_empty_population_samples_zero(tmp_path):
    run_dir = tmp_path / "run"
    _write(run_dir, [_pr_record()])
    out_csv = tmp_path / "verify.csv"

    export_verification.main(["--run", str(run_dir), "--out", str(out_csv)])

    rows = _read_rows(out_csv)
    assert rows == []
