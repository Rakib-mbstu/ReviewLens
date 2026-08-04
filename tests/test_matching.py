import os
import random

import httpx

from reviewlens.eval.matching import (
    LINE_TOLERANCE,
    LlmJudge,
    MatchResult,
    is_candidate,
    match_comments,
    render_match_user,
)
from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.prompt import Prompt, load_prompt

MATCH_V1_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "match_v1.md")

# Small inline prompt for the LLM-call tests, mirroring how test_engine.py avoids
# depending on the real (larger) prompt file's exact wording for its HTTP-call tests.
MATCH_PROMPT = Prompt(
    name="match_v1",
    version=1,
    params={"temperature": 0.0},
    system="Judge equivalence.",
    user_template=(
        "Human: [[HUMAN_FILE]]:[[HUMAN_LINE]] [[HUMAN_COMMENT]]\n"
        "Model: [[MODEL_FILE]]:[[MODEL_LINE]] [[MODEL_COMMENT]]"
    ),
    sha256="0" * 64,
)


def comment(file: str, line: int, text: str) -> dict:
    return {"file": file, "line": line, "comment": text}


def stub_judge(equivalent_pairs):
    """Judge stub: (human['comment'], model['comment']) pairs in `equivalent_pairs`
    are equivalent; everything else is not. Never touches the network."""

    def judge(human, model):
        key = (human["comment"], model["comment"])
        if key in equivalent_pairs:
            return True, "stub: same issue"
        return False, "stub: different issue"

    return judge


# --- is_candidate (pure geometric filter) ---


def test_is_candidate_plus_three_is_boundary_candidate():
    model = comment("Foo.java", 10, "M")
    human = comment("Foo.java", 13, "H")  # +3
    assert is_candidate(model, human)


def test_is_candidate_minus_three_is_boundary_candidate():
    model = comment("Foo.java", 10, "M")
    human = comment("Foo.java", 7, "H")  # -3
    assert is_candidate(model, human)


def test_is_candidate_four_lines_apart_is_not_a_candidate():
    model = comment("Foo.java", 10, "M")
    assert not is_candidate(model, comment("Foo.java", 14, "H"))  # +4
    assert not is_candidate(model, comment("Foo.java", 6, "H"))  # -4


def test_is_candidate_same_line_different_file_is_not_a_candidate():
    model = comment("Foo.java", 10, "M")
    human = comment("Bar.java", 10, "H")
    assert not is_candidate(model, human)


def test_is_candidate_is_symmetric():
    # match_comments calls it (human, model) while a caller reasoning about a
    # model comment would call it (model, human); the +-3 window must not
    # depend on which side is passed first.
    model = comment("Foo.java", 10, "M")
    human = comment("Foo.java", 13, "H")
    assert is_candidate(model, human) == is_candidate(human, model)


def test_line_tolerance_constant_is_three():
    assert LINE_TOLERANCE == 3


# --- match_comments: deterministic ordering ---


def test_multiple_candidates_within_tolerance_picks_nearest_deterministically():
    human = comment("F.java", 10, "H")
    # Deltas: far=2 (idx0), near=1 (idx1), farthest=3 (idx2).
    m_far = comment("F.java", 8, "far")
    m_near = comment("F.java", 9, "near")
    m_farthest = comment("F.java", 13, "farthest")
    model_comments = [m_far, m_near, m_farthest]
    judge = stub_judge({("H", "far"), ("H", "near"), ("H", "farthest")})

    result = match_comments([human], model_comments, judge)

    assert len(result.matches) == 1
    matched_human, matched_model, _reason = result.matches[0]
    assert matched_human == human
    assert matched_model == m_near
    assert result.unmatched_human == []
    assert {c["comment"] for c in result.unmatched_model} == {"far", "farthest"}


def test_nearest_candidate_pick_is_stable_across_repeats_and_shuffles():
    human = comment("F.java", 10, "H")
    m_far = comment("F.java", 8, "far")
    m_near = comment("F.java", 9, "near")
    m_farthest = comment("F.java", 13, "farthest")
    judge = stub_judge({("H", "far"), ("H", "near"), ("H", "farthest")})

    orderings = [
        [m_far, m_near, m_farthest],
        [m_near, m_farthest, m_far],
        [m_farthest, m_far, m_near],
    ]
    rng = random.Random(42)
    shuffled = [m_far, m_near, m_farthest]
    rng.shuffle(shuffled)
    orderings.append(shuffled)

    for model_comments in orderings:
        result = match_comments([human], list(model_comments), judge)
        assert len(result.matches) == 1
        assert result.matches[0][1] == m_near

    # Repeated runs on the same ordering are identical too.
    first = match_comments([human], [m_far, m_near, m_farthest], judge)
    second = match_comments([human], [m_far, m_near, m_farthest], judge)
    assert first.matches == second.matches


def test_judge_rejects_nearest_but_accepts_a_farther_candidate():
    human = comment("F.java", 10, "H")
    m_near = comment("F.java", 9, "near")  # delta 1 — tried first
    m_far = comment("F.java", 12, "far")  # delta 2 — tried second
    # Only the farther one is equivalent.
    judge = stub_judge({("H", "far")})

    result = match_comments([human], [m_near, m_far], judge)

    assert len(result.matches) == 1
    assert result.matches[0][1] == m_far
    assert result.unmatched_model == [m_near]


# --- match_comments: judge says not equivalent ---


def test_judge_says_not_equivalent_within_tolerance_yields_no_match_and_hallucination_candidate():
    human = comment("F.java", 10, "null check missing")
    model = comment("F.java", 11, "consider renaming this variable")
    judge = stub_judge(set())  # nothing is equivalent

    result = match_comments([human], [model], judge)

    assert result.matches == []
    assert result.unmatched_human == [human]
    assert result.unmatched_model == [model]  # hallucination candidate for RQ2


# --- match_comments: one-to-one ---


def test_one_model_comment_cannot_satisfy_two_human_comments():
    human1 = comment("F.java", 10, "H1")
    human2 = comment("F.java", 11, "H2")
    model = comment("F.java", 10, "M")
    # The judge would call both equivalent if asked, but only the first
    # human comment processed should get to claim the model comment.
    judge = stub_judge({("H1", "M"), ("H2", "M")})

    result = match_comments([human1, human2], [model], judge)

    assert len(result.matches) == 1
    assert result.matches[0][0] == human1
    assert result.unmatched_human == [human2]
    assert result.unmatched_model == []


# --- match_comments: unmatched reporting is complete and separate ---


def test_unmatched_human_and_model_are_reported_completely_and_separately():
    matched_human = comment("F.java", 10, "matched-h")
    matched_model = comment("F.java", 10, "matched-m")
    orphan_human = comment("F.java", 50, "orphan-h")  # no candidate model comment nearby
    orphan_model = comment("Other.java", 5, "orphan-m")  # different file entirely

    judge = stub_judge({("matched-h", "matched-m")})

    result = match_comments(
        [matched_human, orphan_human], [matched_model, orphan_model], judge
    )

    assert result.matches == [(matched_human, matched_model, "stub: same issue")]
    assert result.unmatched_human == [orphan_human]
    assert result.unmatched_model == [orphan_model]


def test_judge_log_records_every_invocation_including_rejections():
    human = comment("F.java", 10, "H")
    m_near = comment("F.java", 9, "near")
    m_far = comment("F.java", 12, "far")
    judge = stub_judge({("H", "far")})

    result = match_comments([human], [m_near, m_far], judge)

    assert isinstance(result, MatchResult)
    assert len(result.judge_log) == 2
    assert result.judge_log[0] == (human, m_near, False, "stub: different issue")
    assert result.judge_log[1] == (human, m_far, True, "stub: same issue")


# --- LlmJudge: response parsing, driven through a mocked OpenRouterClient ---


def make_llm_client(tmp_path, transport):
    return OpenRouterClient(
        api_key="test-key",
        cache_dir=str(tmp_path / "cache"),
        transport=transport,
        use_cache=False,
        backoff_base=0.0,
    )


def llm_transport(content: str) -> httpx.MockTransport:
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    return httpx.MockTransport(handler)


def test_llm_judge_parses_well_formed_reply(tmp_path):
    client = make_llm_client(tmp_path, llm_transport('{"equivalent": true, "reason": "same defect"}'))
    judge = LlmJudge(client, "test/model-x", MATCH_PROMPT)

    equivalent, reason = judge(comment("F.java", 10, "H"), comment("F.java", 11, "M"))

    assert equivalent is True
    assert reason == "same defect"


def test_llm_judge_strips_json_code_fence(tmp_path):
    fenced = '```json\n{"equivalent": false, "reason": "different concern"}\n```'
    client = make_llm_client(tmp_path, llm_transport(fenced))
    judge = LlmJudge(client, "test/model-x", MATCH_PROMPT)

    equivalent, reason = judge(comment("F.java", 10, "H"), comment("F.java", 11, "M"))

    assert equivalent is False
    assert reason == "different concern"


def test_llm_judge_non_json_reply_is_not_equivalent_and_does_not_raise(tmp_path):
    client = make_llm_client(tmp_path, llm_transport("I am not going to answer in JSON."))
    judge = LlmJudge(client, "test/model-x", MATCH_PROMPT)

    equivalent, reason = judge(comment("F.java", 10, "H"), comment("F.java", 11, "M"))

    assert equivalent is False
    assert reason  # a reason was recorded, not dropped


def test_llm_judge_reply_missing_equivalent_key_is_not_equivalent_and_does_not_raise(tmp_path):
    client = make_llm_client(tmp_path, llm_transport('{"reason": "forgot the key"}'))
    judge = LlmJudge(client, "test/model-x", MATCH_PROMPT)

    equivalent, reason = judge(comment("F.java", 10, "H"), comment("F.java", 11, "M"))

    assert equivalent is False
    assert "equivalent" in reason


# --- prompts/match_v1.md loads cleanly and all six tokens substitute ---


def test_match_v1_prompt_loads_and_all_placeholders_substitute():
    prompt = load_prompt(MATCH_V1_PATH)

    assert prompt.name == "match_v1"
    assert prompt.version == 1
    assert prompt.params == {"temperature": 0.0}

    rendered = render_match_user(
        prompt.user_template,
        "Human.java",
        10,
        "human comment text",
        "Model.java",
        12,
        "model comment text",
    )

    assert "[[" not in rendered
    assert "Human.java" in rendered
    assert "10" in rendered
    assert "human comment text" in rendered
    assert "Model.java" in rendered
    assert "12" in rendered
    assert "model comment text" in rendered
