import httpx
import pytest

from reviewlens.openrouter import (
    AuthError,
    OpenRouterClient,
    RateLimitError,
    TransientError,
)

MESSAGES = [{"role": "user", "content": "review this hunk"}]
FAKE_RESPONSE = {"choices": [{"message": {"role": "assistant", "content": "LGTM"}}]}


class CountingTransport(httpx.MockTransport):
    """MockTransport that counts requests, so tests can assert zero-HTTP cache hits."""

    def __init__(self, handler):
        super().__init__(handler)
        self.requests = 0

    def handle_request(self, request):
        self.requests += 1
        return super().handle_request(request)


def ok_transport():
    return CountingTransport(lambda request: httpx.Response(200, json=FAKE_RESPONSE))


def make_client(tmp_path, transport, **kwargs):
    kwargs.setdefault("backoff_base", 0.0)
    return OpenRouterClient(
        api_key="test-key",
        cache_dir=str(tmp_path / "cache"),
        transport=transport,
        **kwargs,
    )


def test_second_identical_call_makes_zero_http_requests(tmp_path):
    transport = ok_transport()
    client = make_client(tmp_path, transport)

    first = client.complete("some/model", MESSAGES, temperature=0.0)
    assert transport.requests == 1

    second = client.complete("some/model", MESSAGES, temperature=0.0)
    assert transport.requests == 1
    assert second == first == FAKE_RESPONSE


def test_cache_survives_client_restart(tmp_path):
    transport = ok_transport()
    make_client(tmp_path, transport).complete("some/model", MESSAGES)

    transport2 = ok_transport()
    result = make_client(tmp_path, transport2).complete("some/model", MESSAGES)
    assert transport2.requests == 0
    assert result == FAKE_RESPONSE


def test_different_request_misses_cache(tmp_path):
    transport = ok_transport()
    client = make_client(tmp_path, transport)
    client.complete("some/model", MESSAGES)
    client.complete("other/model", MESSAGES)
    assert transport.requests == 2


def test_no_cache_always_calls_api(tmp_path):
    transport = ok_transport()
    client = make_client(tmp_path, transport, use_cache=False)
    client.complete("some/model", MESSAGES)
    client.complete("some/model", MESSAGES)
    assert transport.requests == 2


def test_auth_error_is_not_retried(tmp_path):
    transport = CountingTransport(lambda request: httpx.Response(401, json={"error": "bad key"}))
    client = make_client(tmp_path, transport)
    with pytest.raises(AuthError, match="OPENROUTER_API_KEY"):
        client.complete("some/model", MESSAGES)
    assert transport.requests == 1


def test_rate_limit_retried_then_raises(tmp_path):
    transport = CountingTransport(lambda request: httpx.Response(429, json={"error": "slow down"}))
    client = make_client(tmp_path, transport, max_retries=3)
    with pytest.raises(RateLimitError, match="Rate limited"):
        client.complete("some/model", MESSAGES)
    assert transport.requests == 3


def test_transient_server_error_recovers_on_retry(tmp_path):
    calls = []

    def flaky(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, json={"error": "overloaded"})
        return httpx.Response(200, json=FAKE_RESPONSE)

    client = make_client(tmp_path, CountingTransport(flaky))
    assert client.complete("some/model", MESSAGES) == FAKE_RESPONSE
    assert len(calls) == 2


def test_network_errors_exhaust_into_transient_error(tmp_path):
    def broken(request):
        raise httpx.ConnectError("connection refused")

    client = make_client(tmp_path, CountingTransport(broken), max_retries=2)
    with pytest.raises(TransientError, match="after 2 attempts"):
        client.complete("some/model", MESSAGES)


def test_missing_api_key_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(AuthError, match="OPENROUTER_API_KEY"):
        OpenRouterClient(cache_dir=str(tmp_path / "cache"))


# --- billed-but-empty responses (provider-side serialization bug) ---

EMPTY_RESPONSE = {
    "provider": "BrokenProvider",
    "choices": [
        {"finish_reason": "stop", "message": {"role": "assistant", "content": None}}
    ],
}
LENGTH_CAPPED_RESPONSE = {
    "provider": "SomeProvider",
    "choices": [
        {"finish_reason": "length", "message": {"role": "assistant", "content": None}}
    ],
}


def test_empty_content_is_retried_and_recovers(tmp_path):
    """A null-content reply is retried; a later attempt may land on a working
    upstream, and only that good response is what the caller sees."""
    responses = [EMPTY_RESPONSE, FAKE_RESPONSE]
    transport = CountingTransport(
        lambda request: httpx.Response(200, json=responses[min(transport.requests - 1, 1)])
    )
    client = make_client(tmp_path, transport)

    result = client.complete("some/model", MESSAGES)

    assert transport.requests == 2
    assert result == FAKE_RESPONSE


def test_persistently_empty_content_is_returned_but_never_cached(tmp_path):
    """After retries are exhausted the empty reply is still returned — the
    engine records it as a parse error — but caching it would replay a
    provider bug forever as if it were a real model answer."""
    transport = CountingTransport(lambda request: httpx.Response(200, json=EMPTY_RESPONSE))
    client = make_client(tmp_path, transport, max_retries=3)

    result = client.complete("some/model", MESSAGES)
    assert result == EMPTY_RESPONSE
    assert transport.requests == 3

    # A re-run must go back to the network rather than serve the bad reply.
    client.complete("some/model", MESSAGES)
    assert transport.requests == 6


def test_length_capped_empty_content_is_not_retried(tmp_path):
    """A completion cut short by its token budget is a real model outcome,
    not the provider bug, so it is cached and reported like any other reply."""
    transport = CountingTransport(
        lambda request: httpx.Response(200, json=LENGTH_CAPPED_RESPONSE)
    )
    client = make_client(tmp_path, transport)

    assert client.complete("some/model", MESSAGES) == LENGTH_CAPPED_RESPONSE
    assert transport.requests == 1

    client.complete("some/model", MESSAGES)
    assert transport.requests == 1
