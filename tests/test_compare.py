from __future__ import annotations

import json

import pytest

import reviewlens.eval.compare as cli
from reviewlens.eval.compare import fisher_exact_two_sided, render_comparison, wilson_interval


def _row(model, matched, human, comments, via="openrouter", chunks=100, parse_errors=0, prs=("a", "b")):
    return {
        "model": model, "via": via, "complete": True, "prs": list(prs),
        "human_comments": human, "model_comments": comments, "matched": matched,
        "reachable": matched * 3, "chunks": chunks, "parse_errors": parse_errors,
    }


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
