from __future__ import annotations

import json

import pytest

import reviewlens.eval.compare as cli
from reviewlens.eval.compare import (
    apply_verification,
    fisher_exact_two_sided,
    load_verified_matches,
    render_comparison,
    wilson_interval,
)


def _row(model, matched, human, comments, via="openrouter", chunks=100, parse_errors=0, prs=("a", "b")):
    return {
        "model": model, "via": via, "complete": True, "prs": list(prs),
        "human_comments": human, "model_comments": comments, "matched": matched,
        "match_ids": [f"{model}__j{i}" for i in range(matched)],
        "checked": None, "rejected": None, "matched_verified": None,
        "reachable": matched * 3, "chunks": chunks, "parse_errors": parse_errors,
    }


def _verification_csv(tmp_path, rows, name="verified.csv"):
    """Write the subset of the export_verification schema the flag reads."""
    path = tmp_path / name
    header = "judgment_id,run,kind,human_verdict\n"
    body = "".join(f"{jid},runs/r/,{kind},{verdict}\n" for jid, kind, verdict in rows)
    path.write_text(header + body, encoding="utf-8")
    return str(path)


def test_wilson_interval_is_none_on_an_empty_denominator():
    """A recall with no denominator must not render as a number."""
    assert wilson_interval(0, 0) is None


def test_wilson_interval_never_goes_below_zero():
    """The normal approximation does; that is why this uses Wilson."""
    low, high = wilson_interval(0, 30)
    assert low == 0.0 and 0 < high < 1


def test_fisher_exact_reports_a_clear_difference_as_significant():
    assert fisher_exact_two_sided(20, 5, 2, 23) < 0.05


def test_fisher_exact_reports_a_small_difference_as_not_significant():
    """6/102 vs 1/102 — the real observed gap — must not read as a finding."""
    assert fisher_exact_two_sided(6, 96, 1, 101) > 0.05


def test_comparison_marks_a_non_significant_gap(capsys):
    rows = [_row("cheap", 1, 102, 800), _row("frontier", 6, 102, 250)]

    out = render_comparison(rows, "test/judge")

    assert "(n.s.)" in out
    assert "not evidence of an ordering" in out


def test_comparison_reports_the_delivery_channel():
    """A subagent arm did not get the same treatment as an API arm."""
    rows = [_row("a", 1, 102, 800), _row("b", 6, 102, 250, via="claude-code-subagent")]

    out = render_comparison(rows, "test/judge")

    assert "claude-code-subagent" in out
    assert "cannot" in out and "capability alone" in out


def test_comparison_includes_matches_per_comment():
    """Volume is not capability; this is the column that separates them."""
    rows = [_row("loud", 1, 102, 800), _row("terse", 6, 102, 250)]

    out = render_comparison(rows, "test/judge")

    assert "Matches per comment" in out or "Matches per comment" in out
    assert "0.1%" in out  # 1/800
    assert "2.4%" in out  # 6/250


def test_runs_covering_different_prs_are_refused(tmp_path, monkeypatch):
    """Different denominators would make the recall column meaningless."""
    monkeypatch.setattr(
        cli, "summarize_run",
        lambda d: _row("m", 1, 10, 10, prs=("a",) if d.endswith("1") else ("b",)),
    )

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--runs", "r1", "r2", "--report", str(tmp_path / "c.md"), "--judge-model", "j"])

    assert "same PRs" in str(excinfo.value)


def test_run_without_eval_matches_is_refused(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "run_meta.json").write_text(json.dumps({"model": "m", "pr_summaries": []}), encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        cli.summarize_run(str(run))

    assert "eval_matches.json" in str(excinfo.value)


def test_a_rejected_match_stops_counting_toward_recall(tmp_path):
    """The point of the flag: a human veto has to move the published number."""
    rows = [_row("frontier", 6, 102, 250)]
    path = _verification_csv(tmp_path, [
        ("frontier__j0", "match", "not_equivalent"),
        ("frontier__j1", "match", "equivalent"),
    ])

    apply_verification(rows, load_verified_matches(path))

    assert rows[0]["matched"] == 6          # the judge's count is not overwritten
    assert rows[0]["matched_verified"] == 5
    assert (rows[0]["checked"], rows[0]["rejected"]) == (2, 1)
    assert "**4.9%**" in render_comparison(rows, "test/judge")


def test_unrated_and_non_match_rows_are_ignored(tmp_path):
    """Blank verdicts are unrated, and rejecting an unmatched comment cannot
    move recall — only match judgments belong in the numerator."""
    path = _verification_csv(tmp_path, [
        ("a__j0", "match", ""),
        ("a__j1", "unmatched_model", "not_equivalent"),
    ])

    assert load_verified_matches(path) == {}


def test_an_unrecognised_verdict_is_fatal(tmp_path):
    """Skipping a typo would silently restore the number the flag corrects."""
    path = _verification_csv(tmp_path, [("a__j0", "match", "eqivalent")])

    with pytest.raises(SystemExit) as excinfo:
        load_verified_matches(path)

    assert "eqivalent" in str(excinfo.value)


def test_a_csv_that_is_not_a_verification_export_is_refused(tmp_path):
    path = tmp_path / "other.csv"
    path.write_text("sheet_id,verdict\nM1,equivalent\n", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        load_verified_matches(str(path))

    assert "judgment_id" in str(excinfo.value)


def test_one_id_carrying_two_verdicts_is_refused(tmp_path):
    """Ids collide across two runs of the same model; that must not be silent."""
    path = _verification_csv(tmp_path, [
        ("a__j0", "match", "equivalent"),
        ("a__j0", "match", "not_equivalent"),
    ])

    with pytest.raises(SystemExit) as excinfo:
        load_verified_matches(str(path))

    assert "collide" in str(excinfo.value)


def test_an_unverified_table_says_so():
    """Silence would read as verified; the judge is not known to be correct."""
    out = render_comparison([_row("a", 1, 102, 800), _row("b", 6, 102, 250)], "test/judge")

    assert "No human verified these matches" in out
    assert "Human-checked" not in out


def test_a_verified_table_shows_the_coverage_of_each_arm(tmp_path):
    """An arm nobody checked must not read as an arm that passed."""
    rows = [_row("checked-arm", 2, 102, 800), _row("unchecked-arm", 3, 102, 250)]
    path = _verification_csv(tmp_path, [("checked-arm__j0", "match", "equivalent")])

    apply_verification(rows, load_verified_matches(path))
    out = render_comparison(rows, "test/judge")

    assert "1/2 checked, 0 rejected" in out
    assert "| none |" in out
    assert "human-corrected" in out


def test_a_verification_csv_that_joins_nothing_is_refused(tmp_path, monkeypatch):
    """Judgment ids lead with the run's model slug, so a CSV from another arm
    joins to zero rows — silently reporting the judge's numbers instead."""
    monkeypatch.setattr(cli, "summarize_run", lambda d: _row("m", 1, 10, 10))
    path = _verification_csv(tmp_path, [("other-arm__j0", "match", "equivalent")])

    with pytest.raises(SystemExit) as excinfo:
        cli.main([
            "--runs", "r1", "--report", str(tmp_path / "c.md"),
            "--judge-model", "j", "--verified", path,
        ])

    assert "no human verdict" in str(excinfo.value)


def test_a_single_run_is_not_titled_a_cross_model_comparison():
    """The tool is reused for one arm because it is the only entry point that
    folds human verdicts into recall. A report that still called itself a
    cross-model comparison would misdescribe itself to whoever opened it."""
    out = render_comparison([_row("solo", 5, 318, 2356)], "test/judge")

    assert out.startswith("# RQ1 — recall on one run, with human verdicts applied")
    assert "cross-model comparison" not in out.splitlines()[0]
    assert "All arms reviewed" not in out


def test_several_runs_keep_the_cross_model_heading():
    """The single-run wording must not leak into the RQ3 report it shares code
    with."""
    out = render_comparison([_row("a", 1, 102, 800), _row("b", 6, 102, 250)], "test/judge")

    assert out.startswith("# RQ3 — cross-model comparison")
    assert "All arms reviewed the **same 2 PRs**" in out
