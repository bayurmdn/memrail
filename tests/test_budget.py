from memrail.core.budget import DEFAULT_MAX_TOKENS, count_tokens, is_over_budget, remaining_budget


def test_count_tokens_empty():
    assert count_tokens([]) == 0


def test_count_tokens_scales_with_size():
    small = [{"role": "user", "content": "hi"}]
    big = [{"role": "user", "content": "x" * 4000}]
    assert count_tokens(big) > count_tokens(small)


def test_is_over_budget():
    messages = [{"role": "user", "content": "x" * 8000}]
    assert is_over_budget(messages, max_tokens=100)
    assert not is_over_budget(messages, max_tokens=10_000)


def test_remaining_budget():
    messages = [{"role": "user", "content": "x" * 40}]
    rem = remaining_budget(messages, max_tokens=1000)
    assert rem < 1000
    assert rem > 900


def test_default_max_tokens_reasonable():
    assert DEFAULT_MAX_TOKENS >= 10_000
