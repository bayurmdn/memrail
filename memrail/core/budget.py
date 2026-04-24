"""Token estimation + threshold logic. Pure, no I/O."""
from __future__ import annotations

from memrail.utils.tokenizer import message_tokens

DEFAULT_MAX_TOKENS = 80_000


def count_tokens(messages: list[dict]) -> int:
    return sum(message_tokens(m) for m in messages)


def is_over_budget(messages: list[dict], max_tokens: int = DEFAULT_MAX_TOKENS) -> bool:
    return count_tokens(messages) > max_tokens


def remaining_budget(messages: list[dict], max_tokens: int = DEFAULT_MAX_TOKENS) -> int:
    return max_tokens - count_tokens(messages)
