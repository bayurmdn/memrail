"""Classify messages into priority tiers. Pure, no I/O."""
from __future__ import annotations

from enum import IntEnum

from memrail.utils.tokenizer import message_tokens

RECENT_WINDOW = 5
LARGE_CONTENT_CHARS = 2000

CRITICAL_SIGNALS = (
    "error",
    "exception",
    "traceback",
    "task:",
    "objective",
    "current goal",
    "must",
    "do not",
    "todo:",
)
RESTORABLE_SIGNALS = (
    "result",
    "output",
    "data",
    "response",
    "html",
    "dom",
    "snapshot",
    "<!doctype",
    "<html",
)


class Tier(IntEnum):
    CRITICAL = 1
    USEFUL = 2
    RESTORABLE = 3
    DISPOSABLE = 4


def _content_text(message: dict) -> str:
    content = message.get("content", "")
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text", "")))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(content)


def classify(message: dict, position: int, total: int) -> Tier:
    role = message.get("role", "")
    text = _content_text(message)
    lower = text.lower()

    if role == "system":
        return Tier.CRITICAL

    if any(sig in lower for sig in CRITICAL_SIGNALS):
        return Tier.CRITICAL

    is_recent = position >= total - RECENT_WINDOW
    is_large = len(text) > LARGE_CONTENT_CHARS

    if is_large and any(sig in lower for sig in RESTORABLE_SIGNALS):
        return Tier.RESTORABLE
    if is_large and role == "tool":
        return Tier.RESTORABLE
    if is_large:
        return Tier.RESTORABLE

    if is_recent:
        return Tier.USEFUL

    return Tier.DISPOSABLE


def classify_all(messages: list[dict]) -> list[tuple[dict, Tier]]:
    total = len(messages)
    return [(m, classify(m, i, total)) for i, m in enumerate(messages)]


def tier_counts(classified: list[tuple[dict, Tier]]) -> dict[Tier, int]:
    counts: dict[Tier, int] = {t: 0 for t in Tier}
    for _, tier in classified:
        counts[tier] += 1
    return counts


def tier_tokens(classified: list[tuple[dict, Tier]]) -> dict[Tier, int]:
    out: dict[Tier, int] = {t: 0 for t in Tier}
    for msg, tier in classified:
        out[tier] += message_tokens(msg)
    return out
