from __future__ import annotations

import pytest

from reviewlens.eval.corpus import EvalPR
from reviewlens.eval.matching import match_comments
from reviewlens.eval.metrics import compute_metrics


def human(line: int, comment: str, category: str | None = None) -> dict:
    record = {"file": "src/Main.java", "line": line, "comment": comment}
    if category is not None:
        record["category"] = category
    return record


def model(line: int, comment: str) -> dict:
    return {"file": "src/Main.java", "line": line, "comment": comment}


def always_equivalent(_human, _model):
    return True, "same issue"


def never_equivalent(_human, _model):
    return False, "different issue"


def build(pr_number, humans, models, judge, chunk_count=4, parse_error_count=0):
    pr = EvalPR(
        repo="org/repo",
        number=pr_number,
        human_comments=humans,
        model_comments=models,
        chunk_count=chunk_count,
        parse_error_count=parse_error_count,
    )
    return pr, match_comments(pr.human_comments, pr.model_comments, judge)


# --- RQ1 recall ---


def test_recall_is_matched_over_human_comments():
    humans = [human(10, "a"), human(50, "b")]
    models = [model(11, "a-ish")]  # only the first is within +/-3 lines

    metrics = compute_metrics([build(1, humans, models, always_equivalent)])

    assert metrics.matched_count == 1
    assert metrics.human_comment_count == 2
    assert metrics.recall == 0.5


def test_recall_aggregates_across_prs():
    first = build(1, [human(10, "a")], [model(10, "a")], always_equivalent)
    second = build(2, [human(10, "b"), human(20, "c")], [model(99, "d")], always_equivalent)

    metrics = compute_metrics([first, second])

    assert metrics.pr_count == 2
    assert metrics.human_comment_count == 3
    assert metrics.matched_count == 1
    assert metrics.recall == 1 / 3


def test_recall_is_none_rather_than_zero_on_an_empty_denominator():
    """Zero human comments means recall is undefined; reporting 0% would be a
    fabricated number."""
    metrics = compute_metrics([build(1, [], [model(10, "a")], always_equivalent)])

    assert metrics.recall is None


def test_a_rejected_judge_verdict_is_not_a_match():
    metrics = compute_metrics([build(1, [human(10, "a")], [model(10, "a")], never_equivalent)])

    assert metrics.matched_count == 0
    assert metrics.recall == 0.0


# --- RQ2: unmatched, deliberately not called hallucination ---


def test_unmatched_model_rate_counts_model_comments_with_no_human_counterpart():
    humans = [human(10, "a")]
    models = [model(10, "a"), model(80, "b"), model(90, "c")]

    metrics = compute_metrics([build(1, humans, models, always_equivalent)])

    assert metrics.unmatched_model_count == 2
    assert metrics.unmatched_model_rate == 2 / 3


def test_unmatched_model_rate_is_none_when_the_model_said_nothing():
    metrics = compute_metrics([build(1, [human(10, "a")], [], always_equivalent)])

    assert metrics.unmatched_model_rate is None


# --- per-category recall depends on human categorization ---


def test_per_category_recall_is_absent_until_human_comments_are_categorized():
    metrics = compute_metrics([build(1, [human(10, "a")], [model(10, "a")], always_equivalent)])

    assert metrics.categories_available is False
    assert metrics.by_category == []


def test_per_category_recall_splits_by_human_category():
    humans = [
        human(10, "bug one", category="bug"),
        human(50, "bug two", category="bug"),
        human(90, "style one", category="style"),
    ]
    models = [model(10, "bug one"), model(90, "style one")]

    metrics = compute_metrics([build(1, humans, models, always_equivalent)])

    assert metrics.categories_available is True
    by_name = {c.category: c for c in metrics.by_category}
    assert by_name["bug"].total == 2
    assert by_name["bug"].matched == 1
    assert by_name["bug"].recall == 0.5
    assert by_name["style"].recall == 1.0


def test_partial_categorization_does_not_count_as_available():
    """Otherwise the breakdown would silently report recall over a subset of
    the denominator."""
    humans = [human(10, "a", category="bug"), human(50, "b")]

    metrics = compute_metrics([build(1, humans, [], always_equivalent)])

    assert metrics.categories_available is False


def test_identical_human_comments_are_counted_separately():
    """Two human comments with the same text on nearby lines are two findings,
    and only the one that actually matched counts toward its category."""
    humans = [human(10, "same text", category="bug"), human(11, "same text", category="bug")]
    models = [model(10, "same text")]

    metrics = compute_metrics([build(1, humans, models, always_equivalent)])

    assert metrics.matched_count == 1
    by_name = {c.category: c for c in metrics.by_category}
    assert by_name["bug"].total == 2
    assert by_name["bug"].matched == 1


# --- run health ---


def test_parse_failure_rate_is_chunks_lost_over_chunks_reviewed():
    first = build(1, [], [], always_equivalent, chunk_count=8, parse_error_count=1)
    second = build(2, [], [], always_equivalent, chunk_count=2, parse_error_count=1)

    metrics = compute_metrics([first, second])

    assert metrics.chunk_count == 10
    assert metrics.parse_error_count == 2
    assert metrics.parse_failure_rate == 0.2


def test_parse_failure_rate_is_none_without_chunks():
    metrics = compute_metrics([build(1, [], [], always_equivalent, chunk_count=0)])

    assert metrics.parse_failure_rate is None


def test_no_prs_yields_no_rates():
    metrics = compute_metrics([])

    assert metrics.pr_count == 0
    assert metrics.recall is None
    assert metrics.unmatched_model_rate is None
    assert metrics.parse_failure_rate is None
    assert metrics.chunk_loss_rate is None
    assert metrics.error_chunk_rate is None


# --- chunk loss vs. malformed-item rate: the bug this module fixes ---


def _pr_with_error_stats(number=1, chunk_count=10, **error_stats):
    """An EvalPR carrying the corpus-derived per-chunk error stats directly,
    bypassing load_error_stats so these tests exercise only aggregation."""
    return EvalPR(
        repo="org/repo",
        number=number,
        human_comments=[],
        model_comments=[],
        chunk_count=chunk_count,
        **error_stats,
    )


def test_chunk_loss_rate_is_none_without_chunks():
    pr = _pr_with_error_stats(chunk_count=0)
    metrics = compute_metrics([(pr, match_comments([], [], always_equivalent))])

    assert metrics.chunk_loss_rate is None
    assert metrics.error_chunk_rate is None


def test_a_chunk_with_two_malformed_items_counts_as_one_error_chunk():
    """parse_error_items counts items; error_chunk_count counts distinct
    chunks — one chunk rejecting two items must not be double-counted."""
    pr = _pr_with_error_stats(
        chunk_count=10, parse_error_items=2, error_chunk_count=1, lost_chunk_count=1
    )
    metrics = compute_metrics([(pr, match_comments([], [], always_equivalent))])

    assert metrics.parse_error_items == 2
    assert metrics.error_chunk_count == 1
    assert metrics.error_chunk_rate == 0.1


def test_a_chunk_with_an_error_and_a_valid_comment_is_not_lost():
    """error_chunk_count and lost_chunk_count diverge exactly when a chunk
    both errored and still contributed a comment — this is the overstatement
    the ambiguous single rate used to hide."""
    pr = _pr_with_error_stats(
        chunk_count=10, parse_error_items=1, error_chunk_count=1, lost_chunk_count=0
    )
    metrics = compute_metrics([(pr, match_comments([], [], always_equivalent))])

    assert metrics.error_chunk_rate == 0.1
    assert metrics.chunk_loss_rate == 0.0


def test_chunk_loss_rate_can_be_lower_than_parse_failure_rate():
    """Reproduces the qwen run's shape: 14 malformed items but only 6 lost
    chunks over the same chunk_count — the honest number is much smaller."""
    pr = _pr_with_error_stats(
        chunk_count=1173,
        parse_error_count=14,
        parse_error_items=14,
        error_chunk_count=11,
        lost_chunk_count=6,
    )
    metrics = compute_metrics([(pr, match_comments([], [], always_equivalent))])

    assert metrics.parse_failure_rate == pytest.approx(14 / 1173)
    assert metrics.chunk_loss_rate == pytest.approx(6 / 1173)
    assert metrics.chunk_loss_rate < metrics.parse_failure_rate


def test_provider_and_model_error_items_classify_and_aggregate():
    first = _pr_with_error_stats(
        number=1, chunk_count=5, provider_error_items=1, model_error_items=2
    )
    second = _pr_with_error_stats(
        number=2, chunk_count=5, provider_error_items=0, model_error_items=1
    )
    metrics = compute_metrics(
        [
            (first, match_comments([], [], always_equivalent)),
            (second, match_comments([], [], always_equivalent)),
        ]
    )

    assert metrics.provider_error_items == 1
    assert metrics.model_error_items == 3
