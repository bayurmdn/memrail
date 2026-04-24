"""Token counting. Approximation: 1 token ≈ 4 chars for English text."""
from __future__ import annotations

CHARS_PER_TOKEN = 4


def approx_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def message_tokens(message: dict) -> int:
    content = message.get("content", "")
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, dict):
                total += approx_tokens(str(block.get("text", block)))
            else:
                total += approx_tokens(str(block))
        return total + 4
    return approx_tokens(str(content)) + 4
