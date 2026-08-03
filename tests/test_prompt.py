import os

from reviewlens.review.prompt import load_prompt, render_user

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROMPT_PATH = os.path.join(_REPO_ROOT, "prompts", "review_v1.md")


def test_load_prompt_parses_the_real_review_v1_file():
    prompt = load_prompt(_PROMPT_PATH)

    assert prompt.name == "review_v1"
    assert prompt.version == 1
    assert prompt.params == {"temperature": 0.0}
    assert len(prompt.sha256) == 64
    int(prompt.sha256, 16)  # must be a valid hex digest

    assert prompt.system.strip() != ""
    assert prompt.user_template.strip() != ""
    for token in ("[[FILE]]", "[[START_LINE]]", "[[END_LINE]]", "[[CHUNK]]"):
        assert token in prompt.user_template


def test_sha256_is_stable_across_loads():
    first = load_prompt(_PROMPT_PATH)
    second = load_prompt(_PROMPT_PATH)
    assert first.sha256 == second.sha256


def test_render_user_substitutes_all_tokens_and_preserves_json_braces():
    template = (
        "File: [[FILE]]\n"
        "Lines [[START_LINE]]-[[END_LINE]]\n"
        'Schema: {"file": "<path>", "line": <int>}\n'
        "Chunk:\n[[CHUNK]]"
    )

    rendered = render_user(template, "Foo.java", 12, 20, "+ 12: some code")

    assert "[[FILE]]" not in rendered
    assert "[[START_LINE]]" not in rendered
    assert "[[END_LINE]]" not in rendered
    assert "[[CHUNK]]" not in rendered
    assert "File: Foo.java" in rendered
    assert "Lines 12-20" in rendered
    assert "+ 12: some code" in rendered
    # JSON braces from the prompt body must survive untouched (str.replace,
    # not str.format, which would choke on these).
    assert '{"file": "<path>", "line": <int>}' in rendered
