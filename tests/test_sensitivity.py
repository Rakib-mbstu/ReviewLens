from __future__ import annotations

import json

import pytest

import reviewlens.eval.sensitivity as cli
from reviewlens.eval.corpus import EvalPR
from reviewlens.eval.matching import LINE_TOLERANCE
from reviewlens.eval.sensitivity import measure_window, render_markdown


def _human(line, comment="human says"):
    return {"file": "src/Main.java", "line": line, "comment": comment}


def _model(line, comment="model says"):
    return {"file": "src/Main.java", "line": line, "comment": comment}


def _pr(humans, models):
    return EvalPR(repo="org/repo", number=1, human_comments=humans, model_comments=models)


ALWAYS = lambda h, m: (True, "same")
NEVER = lambda h, m: (False, "different")


def test_reachability_grows_with_the_window():
    """The whole point of the sweep: a wider window sees more pairs."""
    prs = [_pr([_human(10), _human(30)], [_model(12), _model(50)])]

    near = measure_window(prs, ALWAYS, 3)
    far = measure_window(prs, ALWAYS, 25)

    assert near["reachable"] == 1
    assert far["reachable"] == 2
    assert far["judge_calls"] > near["judge_calls"]


def test_recall_can_stay_flat_while_reachability_rises():
    """The observed result: more pairs seen, no more matches. This is what
    separates "commented somewhere else" from "disagreed about the issue"."""
    prs = [_pr([_human(10), _human(30)], [_model(12), _model(50)])]

    near = measure_window(prs, NEVER, 3)
    far = measure_window(prs, NEVER, 25)

    assert far["reachable"] > near["reachable"]
    assert near["matched"] == far["matched"] == 0
    assert near["recall"] == far["recall"] == 0.0


def test_recall_and_reachable_rate_are_none_not_zero_on_an_empty_denominator():
    result = measure_window([_pr([], [])], ALWAYS, 3)

    assert result["recall"] is None
    assert result["reachable_rate"] is None


def test_markdown_marks_which_row_is_the_frozen_rule():
    """A reader must never mistake a diagnostic window for the study's rule."""
    rows = [measure_window([_pr([_human(10)], [_model(10)])], ALWAYS, w) for w in (3, 25)]

    out = render_markdown(rows, {"model": "test/model-x", "complete": False}, "test/judge")

    assert f"±{LINE_TOLERANCE} (frozen rule)" in out
    assert "±25 |" in out
    assert "diagnostic only" in out
    assert "PARTIAL" in out


def test_windows_must_include_the_frozen_rule(tmp_path):
    """Without the ±3 row the table has nothing to anchor reported recall to."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            ["--run", str(tmp_path), "--judge-model", "m",
             "--report", str(tmp_path / "s.md"), "--windows", "10,25"]
        )

    assert "frozen rule" in str(excinfo.value)


def test_non_integer_windows_are_rejected(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            ["--run", str(tmp_path), "--judge-model", "m",
             "--report", str(tmp_path / "s.md"), "--windows", "3,wide"]
        )

    assert "comma-separated integers" in str(excinfo.value)
