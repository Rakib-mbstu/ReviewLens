"""Compute RQ1/RQ2 metrics from matched comments.

Two naming decisions here are load-bearing for the study's honesty rules:

* **Recall (RQ1)** is recall *against human comments* — agreement with the
  reviewers who actually looked at the PR, not absolute defect detection.
  Human comments are not ground truth for every issue in the diff.

* **Unmatched model comments are not the hallucination rate (RQ2).** A model
  comment that matches no human comment may be a hallucination, or a real
  issue the humans did not bother to mention. Only the manual verification
  pass can tell those apart, so this module reports an *unmatched rate* and
  refuses to name it anything stronger. No hallucination rate is emitted
  until a human has judged the sample.

Per-category recall is likewise computed only when human comments actually
carry categories. Human-comment categorization is a separate stage; until it
runs, the per-category breakdown is absent rather than zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryMetrics:
    """Recall within one human-comment category."""

    category: str
    total: int
    matched: int

    @property
    def recall(self) -> float | None:
        return None if self.total == 0 else self.matched / self.total


@dataclass
class Metrics:
    """Everything the report renders. Rates are None when undefined."""

    pr_count: int
    human_comment_count: int
    model_comment_count: int
    matched_count: int
    unmatched_model_count: int
    chunk_count: int
    parse_error_count: int
    by_category: list[CategoryMetrics] = field(default_factory=list)
    categories_available: bool = False

    @property
    def recall(self) -> float | None:
        """RQ1: fraction of human comments the model also raised."""
        if self.human_comment_count == 0:
            return None
        return self.matched_count / self.human_comment_count

    @property
    def unmatched_model_rate(self) -> float | None:
        """Fraction of model comments matching no human comment.

        An upper bound on the hallucination rate, not the rate itself.
        """
        if self.model_comment_count == 0:
            return None
        return self.unmatched_model_count / self.model_comment_count

    @property
    def parse_failure_rate(self) -> float | None:
        """Fraction of chunks whose reply could not be parsed.

        Reported because a lost chunk depresses recall for reasons unrelated
        to review ability, so it has to be visible next to the recall number.
        """
        if self.chunk_count == 0:
            return None
        return self.parse_error_count / self.chunk_count


def compute_metrics(per_pr_results: list[tuple[object, object]]) -> Metrics:
    """Aggregate per-PR (EvalPR, MatchResult) pairs into one Metrics.

    Takes already-matched results rather than doing matching itself: matching
    costs LLM calls, and keeping this function pure makes every metric
    testable on fixed fixtures with no network access.
    """
    pr_count = len(per_pr_results)
    human_total = 0
    model_total = 0
    matched_total = 0
    unmatched_model_total = 0
    chunk_total = 0
    parse_error_total = 0

    category_totals: dict[str, int] = {}
    category_matched: dict[str, int] = {}
    categorized_human = 0

    for pr, result in per_pr_results:
        human_total += len(pr.human_comments)
        model_total += len(pr.model_comments)
        matched_total += len(result.matches)
        unmatched_model_total += len(result.unmatched_model)
        chunk_total += pr.chunk_count
        parse_error_total += pr.parse_error_count

        # `match_comments` returns the very dicts it was given, so object
        # identity is what distinguishes two human comments that happen to
        # carry identical text on nearby lines.
        matched_human_ids = {id(human) for human, _model, _reason in result.matches}
        for human in pr.human_comments:
            category = human.get("category")
            if not category:
                continue
            categorized_human += 1
            category_totals[category] = category_totals.get(category, 0) + 1
            if id(human) in matched_human_ids:
                category_matched[category] = category_matched.get(category, 0) + 1

    by_category = [
        CategoryMetrics(
            category=category,
            total=category_totals[category],
            matched=category_matched.get(category, 0),
        )
        for category in sorted(category_totals)
    ]

    return Metrics(
        pr_count=pr_count,
        human_comment_count=human_total,
        model_comment_count=model_total,
        matched_count=matched_total,
        unmatched_model_count=unmatched_model_total,
        chunk_count=chunk_total,
        parse_error_count=parse_error_total,
        by_category=by_category,
        # A partially categorized corpus would silently report recall over a
        # subset of the denominator, so the breakdown counts as available
        # only when every human comment carries a category.
        categories_available=categorized_human == human_total and human_total > 0,
    )
