"""Thin OpenRouter chat-completions client with a file-based response cache.

The cache exists so that a full evaluation re-run with a warm cache costs $0
and produces byte-identical model responses (reproducibility). Cache keys
cover everything that influences a response: model ID, messages, and request
parameters. The model ID is always a caller-supplied parameter — nothing here
is tied to a specific provider tier or model.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

import httpx

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
API_KEY_ENV_VAR = "OPENROUTER_API_KEY"


class OpenRouterError(Exception):
    """Base class for OpenRouter client failures."""


class AuthError(OpenRouterError):
    """Authentication failed — not retried."""


class RateLimitError(OpenRouterError):
    """Rate limited and retries exhausted."""


class TransientError(OpenRouterError):
    """Server or network error and retries exhausted."""


def response_provider(response: dict) -> str | None:
    """The upstream provider that served a response, if OpenRouter reported one.

    Recorded in run metadata because the model ID alone does not determine
    who actually answered, and providers differ in ways the study can see
    (see `content_is_missing`).
    """
    provider = response.get("provider")
    return provider if isinstance(provider, str) else None


def content_is_missing(response: dict) -> bool:
    """True when a response carries no assistant text despite being billed.

    Observed from more than one upstream (Novita serving qwen3-coder-30b,
    Phala serving gpt-oss-120b): `finish_reason` is "stop", completion
    tokens are billed, and `message.content` is null. Caching that would
    bake a provider-side serialization bug into every later run as a parse
    failure, and RQ3 would read it as a difference between *models* when it
    is a difference between providers.

    A completion stopped by its token budget (`finish_reason` "length") is a
    real model outcome rather than this bug, so it is deliberately excluded
    here and left for the engine to record as an ordinary parse error.
    """
    try:
        choice = response["choices"][0]
    except (KeyError, IndexError, TypeError):
        return False
    if not isinstance(choice, dict) or choice.get("finish_reason") == "length":
        return False
    message = choice.get("message")
    if not isinstance(message, dict):
        return False
    return not message.get("content")


def cache_key(model: str, messages: list[dict], params: dict) -> str:
    """Deterministic cache key for one completion request.

    Canonical JSON (sorted keys, fixed separators) so that dict ordering
    never changes the key. Any change to this scheme invalidates the whole
    cache, so it is pinned by a golden-value unit test.
    """
    canonical = json.dumps(
        {"model": model, "messages": messages, "params": params},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OpenRouterClient:
    """Chat-completions client. One instance per run; safe to reuse across calls.

    transport is injectable so tests never touch the network.
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: str = "cache",
        use_cache: bool = True,
        base_url: str = OPENROUTER_BASE_URL,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._api_key = api_key or os.environ.get(API_KEY_ENV_VAR)
        # A missing key is fatal at the first call that needs the network, not
        # at construction: the cache is documented to make a warm re-run free,
        # and demanding a key to spend nothing would make a published run
        # unreproducible by anyone without an account. Deferring rather than
        # dropping the check keeps a forgotten key a loud error for anyone whose
        # run actually has to reach OpenRouter.
        self._cache_dir = cache_dir
        self._use_cache = use_cache
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._http = httpx.Client(
            base_url=base_url,
            headers=({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
            timeout=timeout,
            transport=transport,
        )

    def complete(self, model: str, messages: list[dict], **params) -> dict:
        """Request a chat completion, returning the raw response JSON.

        Cache hits return the stored response without any HTTP request.

        A billed-but-empty response (see `content_is_missing`) is retried
        rather than accepted, because OpenRouter may route the retry to a
        different upstream. If every attempt comes back empty the response is
        returned anyway — the engine records it as a parse error, exactly as
        before — but it is never written to the cache, so the failure is not
        replayed for free forever as if it were a real model answer.
        """
        key = cache_key(model, messages, params)
        cache_path = os.path.join(self._cache_dir, f"{key}.json")

        if self._use_cache and os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)

        if not self._api_key:
            raise AuthError(
                f"No API key: pass api_key or set the {API_KEY_ENV_VAR} environment "
                f"variable. (This call missed the cache at {self._cache_dir}/, so it "
                "needs the network; a fully warm cache replays without a key.)"
            )

        payload = {"model": model, "messages": messages, **params}
        for _ in range(max(1, self._max_retries)):
            response = self._post_with_retries("/chat/completions", payload)
            if not content_is_missing(response):
                break
        else:
            return response

        os.makedirs(self._cache_dir, exist_ok=True)
        tmp_path = f"{cache_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=True)
        os.replace(tmp_path, cache_path)
        return response

    def _post_with_retries(self, path: str, payload: dict) -> dict:
        last_error = "no request attempted"
        for attempt in range(self._max_retries):
            if attempt > 0:
                time.sleep(self._backoff_base * 2 ** (attempt - 1))
            try:
                resp = self._http.post(path, json=payload)
            except httpx.HTTPError as exc:
                last_error = f"network error: {exc}"
                continue

            if resp.status_code in (401, 403):
                raise AuthError(
                    f"OpenRouter rejected the API key (HTTP {resp.status_code}). "
                    f"Check that {API_KEY_ENV_VAR} is set to a valid key."
                )
            if resp.status_code == 429:
                last_error = "rate limited (HTTP 429)"
                continue
            if resp.status_code >= 500:
                last_error = f"server error (HTTP {resp.status_code})"
                continue
            if resp.status_code != 200:
                raise OpenRouterError(
                    f"Unexpected OpenRouter response (HTTP {resp.status_code}): {resp.text[:500]}"
                )
            return resp.json()

        if "429" in last_error:
            raise RateLimitError(
                f"Rate limited by OpenRouter after {self._max_retries} attempts. "
                "Wait and re-run (the cache makes completed calls free) or reduce request rate."
            )
        raise TransientError(
            f"OpenRouter request failed after {self._max_retries} attempts ({last_error}). "
            "Check network connectivity and https://status.openrouter.ai, then re-run."
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "OpenRouterClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
