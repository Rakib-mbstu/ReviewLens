from reviewlens.openrouter import cache_key

MODEL = "openai/gpt-4o-mini"
MESSAGES = [{"role": "user", "content": "hello"}]
PARAMS = {"temperature": 0.0}


def test_same_inputs_same_key():
    assert cache_key(MODEL, MESSAGES, PARAMS) == cache_key(MODEL, MESSAGES, PARAMS)


def test_param_order_does_not_change_key():
    a = cache_key(MODEL, MESSAGES, {"temperature": 0.0, "max_tokens": 100})
    b = cache_key(MODEL, MESSAGES, {"max_tokens": 100, "temperature": 0.0})
    assert a == b


def test_model_changes_key():
    assert cache_key(MODEL, MESSAGES, PARAMS) != cache_key("anthropic/claude-sonnet-5", MESSAGES, PARAMS)


def test_messages_change_key():
    other = [{"role": "user", "content": "goodbye"}]
    assert cache_key(MODEL, MESSAGES, PARAMS) != cache_key(MODEL, other, PARAMS)


def test_params_change_key():
    assert cache_key(MODEL, MESSAGES, PARAMS) != cache_key(MODEL, MESSAGES, {"temperature": 1.0})


def test_golden_value():
    # Pins the key scheme itself: if this fails, the cache format changed and
    # every existing cache entry (and $0 warm re-runs) is invalidated.
    assert (
        cache_key(MODEL, MESSAGES, PARAMS)
        == "2c370d93e0fa01d7f8cbff65f4b12f52dac4db8ca99f126cb846b03523ed2a92"
    )
