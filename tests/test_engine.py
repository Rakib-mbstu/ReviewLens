import base64
import json
import os
import re

import httpx
import pytest

from reviewlens.openrouter import OpenRouterClient
from reviewlens.review.engine import parse_review_response, review_pr
from reviewlens.review.ingest import GitHubClient, PRFile, PRSnapshot
from reviewlens.review.prompt import Prompt

PROMPT = Prompt(
    name="review_v1",
    version=1,
    params={"temperature": 0.0},
    system="You are a reviewer.",
    user_template="File: [[FILE]] ([[START_LINE]]-[[END_LINE]])\n[[CHUNK]]",
    sha256="0" * 64,
)

# 30-line synthetic pre-review file, matching the fixture style in test_chunking.py.
MODIFIED_FILE_LINES = [f"L{i}" for i in range(1, 31)]

# Two far-apart hunks (lines 2 and 20) so with context_lines=1 they stay two
# separate chunks rather than merging into one.
MODIFIED_PATCH = (
    "@@ -2,1 +2,1 @@\n-L2\n+L2-changed\n"
    "@@ -20,1 +20,1 @@\n-L20\n+L20-changed\n"
)
ADDED_PATCH = "@@ -0,0 +1,2 @@\n+new1\n+new2\n"
REMOVED_PATCH = "@@ -1,1 +0,0 @@\n-gone\n"


class CountingTransport(httpx.MockTransport):
    """MockTransport that counts requests, so tests can assert call counts."""

    def __init__(self, handler):
        super().__init__(handler)
        self.requests = 0

    def handle_request(self, request):
        self.requests += 1
        return super().handle_request(request)


def make_github_client(transport, **kwargs):
    kwargs.setdefault("backoff_base", 0.0)
    return GitHubClient(token="test-token", transport=transport, **kwargs)


def make_llm_client(tmp_path, transport, **kwargs):
    kwargs.setdefault("backoff_base", 0.0)
    return OpenRouterClient(
        api_key="test-key",
        cache_dir=str(tmp_path / "cache"),
        transport=transport,
        use_cache=False,
        **kwargs,
    )


def github_route(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/contents/Modified.java"):
        content = "\n".join(MODIFIED_FILE_LINES)
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        return httpx.Response(200, json={"content": encoded, "encoding": "base64"})
    raise AssertionError(f"unexpected GitHub request: {request.method} {path}")


def llm_route(request: httpx.Request) -> httpx.Response:
    """Echo a single valid comment tagged with the file named in the prompt,
    so assertions can tell which chunk/file produced which comment."""
    payload = json.loads(request.content)
    user_content = payload["messages"][1]["content"]
    file_match = re.search(r"File: (\S+)", user_content)
    file = file_match.group(1) if file_match else "unknown"
    body = [{"file": file, "line": 1, "category": "style", "severity": "low", "comment": f"nit in {file}"}]
    return httpx.Response(
        200,
        json={
            "provider": "TestProvider",
            "choices": [{"message": {"role": "assistant", "content": json.dumps(body)}}],
        },
    )


def make_snapshot(files):
    return PRSnapshot(
        repo="org/repo",
        number=7,
        base_sha="base-sha",
        pre_review_sha="pre-sha",
        files=files,
    )


# --- (a) full review_pr run: run dir layout, comments.json, raw/, model param ---


def test_review_pr_writes_full_run_directory(tmp_path):
    snapshot = make_snapshot(
        [
            PRFile(path="Modified.java", status="modified", patch=MODIFIED_PATCH),
            PRFile(path="Added.java", status="added", patch=ADDED_PATCH),
        ]
    )
    gh_transport = CountingTransport(github_route)
    llm_transport = CountingTransport(llm_route)
    github_client = make_github_client(gh_transport)
    llm_client = make_llm_client(tmp_path, llm_transport)
    out_dir = str(tmp_path / "run")

    summary = review_pr(
        snapshot, github_client, llm_client, "test/model-x", PROMPT, out_dir, context_lines=1
    )

    # Modified.java's two far-apart hunks stay separate chunks (context=1);
    # Added.java's single hunk is one more chunk.
    assert summary == {
        "repo": "org/repo",
        "number": 7,
        "chunk_count": 3,
        "comment_count": 3,
        "parse_error_count": 0,
        # Which upstream answered is recorded per run: the same model ID can
        # be served by providers that differ in ways the results can see.
        "providers": {"TestProvider": 3},
    }
    assert llm_transport.requests == 3
    # Content is fetched for the modified file exactly once per chunk that
    # needs it — here, both modified chunks come from the same file fetch
    # inside review_pr's per-file loop, so contents is requested once.
    assert gh_transport.requests == 1

    pr_dir = os.path.join(out_dir, "org__repo__7")
    assert os.path.isdir(pr_dir)
    assert os.path.isfile(os.path.join(pr_dir, "comments.json"))
    assert not os.path.exists(os.path.join(pr_dir, "errors.json"))

    with open(os.path.join(pr_dir, "comments.json"), encoding="utf-8") as f:
        comments = json.load(f)
    assert len(comments) == 3
    assert {c["chunk_index"] for c in comments} == {0, 1, 2}
    files_seen = {c["file"] for c in comments}
    assert files_seen == {"Modified.java", "Added.java"}

    for i in range(3):
        raw_path = os.path.join(pr_dir, "raw", f"chunk_{i}.json")
        assert os.path.isfile(raw_path)
        with open(raw_path, encoding="utf-8") as f:
            raw = json.load(f)
        assert raw["request"]["model"] == "test/model-x"
        assert raw["request"]["params"] == {"temperature": 0.0}
        assert raw["request"]["messages"][0]["role"] == "system"
        assert raw["request"]["messages"][1]["role"] == "user"
        assert "choices" in raw["response"]


def test_removed_file_is_skipped_with_no_llm_call(tmp_path):
    snapshot = make_snapshot([PRFile(path="Gone.java", status="removed", patch=REMOVED_PATCH)])
    gh_transport = CountingTransport(github_route)
    llm_transport = CountingTransport(llm_route)
    github_client = make_github_client(gh_transport)
    llm_client = make_llm_client(tmp_path, llm_transport)
    out_dir = str(tmp_path / "run")

    summary = review_pr(snapshot, github_client, llm_client, "test/model-x", PROMPT, out_dir)

    assert llm_transport.requests == 0
    assert gh_transport.requests == 0
    assert summary["chunk_count"] == 0
    assert summary["comment_count"] == 0

    with open(os.path.join(out_dir, "org__repo__7", "comments.json"), encoding="utf-8") as f:
        assert json.load(f) == []


def test_file_with_empty_patch_is_skipped(tmp_path):
    snapshot = make_snapshot([PRFile(path="Unchanged.java", status="modified", patch="")])
    llm_transport = CountingTransport(llm_route)
    github_client = make_github_client(CountingTransport(github_route))
    llm_client = make_llm_client(tmp_path, llm_transport)

    summary = review_pr(
        snapshot, github_client, llm_client, "test/model-x", PROMPT, str(tmp_path / "run")
    )

    assert llm_transport.requests == 0
    assert summary["chunk_count"] == 0


# --- (b) parse_review_response ---


def _response(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def test_parse_review_response_valid_array():
    body = [{"file": "Foo.java", "line": 5, "category": "bug", "severity": "high", "comment": "leak"}]
    comments, errors = parse_review_response(_response(json.dumps(body)))
    assert comments == body
    assert errors == []


def test_parse_review_response_strips_markdown_json_fence():
    body = [{"file": "Foo.java", "line": 1, "category": "style", "severity": "low", "comment": "nit"}]
    content = "```json\n" + json.dumps(body) + "\n```"
    comments, errors = parse_review_response(_response(content))
    assert comments == body
    assert errors == []


def test_parse_review_response_strips_diff_markers_bled_into_the_reply():
    """Reproduces a real google/gemini-2.5-flash-lite reply from the first smoke
    run: the model copied the chunk's `- ` line markers onto its own output,
    fence included, which cost that chunk's comments before this was handled."""
    body = [
        {
            "file": "Foo.java",
            "line": 1124,
            "category": "style",
            "severity": "low",
            "comment": "This pattern is used multiple times, consider making it a constant.",
        }
    ]
    fenced = "```json\n" + json.dumps(body, indent=2) + "\n```"
    content = "\n".join("- " + line for line in fenced.splitlines())
    comments, errors = parse_review_response(_response(content))
    assert comments == body
    assert errors == []


def test_parse_review_response_strips_added_line_markers_too():
    body = [{"file": "Foo.java", "line": 3, "category": "bug", "severity": "high", "comment": "npe"}]
    content = "\n".join("+ " + line for line in json.dumps(body, indent=2).splitlines())
    comments, errors = parse_review_response(_response(content))
    assert comments == body
    assert errors == []


def test_parse_review_response_does_not_mistake_a_bullet_list_for_marked_json():
    """Every line starts with `- `, but stripping the markers still yields
    prose — the fallback must not manufacture a parse out of a non-JSON reply."""
    comments, errors = parse_review_response(
        _response("- the constructor may leak\n- the field should be final")
    )
    assert comments == []
    assert len(errors) == 1


def test_parse_review_response_leaves_mixed_marker_lines_alone():
    """Markers are only format bleed when uniform; a reply whose lines start
    with different characters is just malformed and must be reported as such."""
    comments, errors = parse_review_response(_response("- [\n+ {}\n]"))
    assert comments == []
    assert len(errors) == 1


def test_parse_review_response_non_json_reply_records_error_and_does_not_raise():
    comments, errors = parse_review_response(_response("I refuse to output JSON today."))
    assert comments == []
    assert len(errors) == 1
    assert "raw_content" in errors[0]
    assert "error" in errors[0]


def test_parse_review_response_rejects_invalid_elements_but_keeps_valid_siblings():
    body = [
        {"file": "Foo.java", "line": 5, "category": "bug", "severity": "high", "comment": "ok"},
        # line must be an int, not a numeric string
        {"file": "Foo.java", "line": "5", "category": "bug", "severity": "high", "comment": "bad line"},
        # category not in the allowed set
        {"file": "Foo.java", "line": 6, "category": "nitpick", "severity": "high", "comment": "bad cat"},
    ]
    comments, errors = parse_review_response(_response(json.dumps(body)))
    assert len(comments) == 1
    assert comments[0]["comment"] == "ok"
    assert len(errors) == 2


def test_parse_review_response_empty_array_is_ok():
    comments, errors = parse_review_response(_response("[]"))
    assert comments == []
    assert errors == []


def test_parse_review_response_non_array_json_records_error():
    comments, errors = parse_review_response(_response('{"file": "Foo.java"}'))
    assert comments == []
    assert len(errors) == 1


def test_parse_review_response_null_content_records_error_and_does_not_raise():
    """Reasoning models return content=None when the reasoning budget eats the
    whole completion. One such chunk must cost one parse error, not abort the run."""
    comments, errors = parse_review_response(_response(None))
    assert comments == []
    assert len(errors) == 1
    assert "NoneType" in errors[0]["error"]
