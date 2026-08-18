from __future__ import annotations

import json
import os

import pytest

from reviewlens.eval.corpus import EvalPR
from reviewlens.eval.matching import match_comments
from reviewlens.eval.metrics import compute_metrics
from reviewlens.eval.report import render_report
from reviewlens.review.prompt import Prompt, load_prompt

JUDGE_PROMPT = Prompt(
    name="match_v1",
    version=1,
    params={"temperature": 0.0},
    system="You judge equivalence.",
    user_template="[[HUMAN_COMMENT]] vs [[MODEL_COMMENT]]",
    sha256="a" * 64,
)


def _run_meta(complete=True, pr_summaries=None):
    return {
        "model": "test/model-x",
        "prompt": {"name": "review_v1", "version": 1, "sha256": "b" * 64, "params": {}},
        "corpus": "data/corpus",
        "corpus_pr_count": 3,
        "started": "2026-08-19T00:00:00+00:00",
        "finished": "2026-08-19T00:10:00+00:00" if complete else None,
        "complete": complete,
        "pr_summaries": pr_summaries if pr_summaries is not None else [],
        "exclusions": [],
    }


def _metrics(humans, models, judge=lambda h, m: (True, "same"), **kwargs):
    pr = EvalPR(repo="org/repo", number=1, human_comments=humans, model_comments=models, **kwargs)
    return compute_metrics([(pr, match_comments(humans, models, judge))])


def _human(line, comment, category=None):
    record = {"file": "src/Main.java", "line": line, "comment": comment}
    if category is not None:
        record["category"] = category
    return record


def _model(line, comment):
    return {"file": "src/Main.java", "line": line, "comment": comment}


# --- honesty rules the report must not break ---


def test_hallucination_rate_is_reported_as_not_measured():
    """Unmatched model comments are an upper bound, not the hallucination
    rate — naming them that would overstate what the pipeline measured."""
    metrics = _metrics([_human(10, "a")], [_model(80, "b")])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "| **Hallucination rate** | **not measured** |" in report
    assert "upper bound" in report


def test_absent_categories_are_stated_not_zeroed():
    metrics = _metrics([_human(10, "a")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "Not available" in report
    assert "| bug |" not in report


def test_category_table_appears_once_comments_are_categorized():
    metrics = _metrics([_human(10, "a", category="bug")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "| bug | 1 | 1 | 100.0% |" in report


def test_incomplete_run_is_flagged_at_the_top():
    metrics = _metrics([_human(10, "a")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(complete=False), "test/judge", JUDGE_PROMPT)

    assert "**Incomplete run.**" in report
    assert "partial pass" in report


def test_complete_run_carries_no_incomplete_banner():
    metrics = _metrics([_human(10, "a")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "Incomplete run" not in report


def test_undefined_recall_is_not_rendered_as_zero():
    metrics = _metrics([], [])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "| **Recall** | **not measured** |" in report


# --- provenance: a report must name what produced it ---


def test_report_records_models_prompts_and_corpus():
    metrics = _metrics([_human(10, "a")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "`test/model-x`" in report
    assert "`test/judge`" in report
    assert "`review_v1` v1" in report
    assert "`match_v1` v1" in report
    assert "`data/corpus`" in report


def test_report_tallies_the_upstream_providers_that_served_the_run():
    """The model ID does not pin down who answered, and providers differ in
    ways the numbers can see."""
    summaries = [
        {"repo": "org/repo", "number": 1, "chunk_count": 3, "comment_count": 1,
         "parse_error_count": 0, "providers": {"AlphaProvider": 2, "BetaProvider": 1}},
    ]
    metrics = _metrics([_human(10, "a")], [_model(10, "a")])

    report = render_report(metrics, _run_meta(pr_summaries=summaries), "test/judge", JUDGE_PROMPT)

    assert "AlphaProvider (2), BetaProvider (1)" in report


def test_parse_failure_rate_is_reported_beside_recall():
    metrics = _metrics([_human(10, "a")], [_model(10, "a")], chunk_count=10, parse_error_count=2)

    report = render_report(metrics, _run_meta(), "test/judge", JUDGE_PROMPT)

    assert "| Parse failures | 2/10 |" in report
    assert "| Parse-failure rate | 20.0% |" in report


# --- the shipped rubric file must actually load ---


def test_match_v1_rubric_loads_and_exposes_its_placeholders():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt = load_prompt(os.path.join(repo_root, "prompts", "match_v1.md"))

    assert prompt.name == "match_v1"
    assert prompt.version == 1
    for token in ("[[HUMAN_COMMENT]]", "[[MODEL_COMMENT]]", "[[HUMAN_LINE]]", "[[MODEL_LINE]]"):
        assert token in prompt.user_template
