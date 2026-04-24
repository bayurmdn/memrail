"""Compress classified messages: keep CRITICAL/USEFUL, pointerize RESTORABLE, summarize DISPOSABLE."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from memrail.core.budget import DEFAULT_MAX_TOKENS, count_tokens
from memrail.core.classifier import Tier, _content_text, classify_all, tier_counts
from memrail.core.pointer import create_pointer
from memrail.core.store import MemrailStore

TRUNCATE_PREVIEW = 200


class LLMClient(Protocol):
    def summarize(self, text: str, max_tokens: int = 200) -> str: ...


@dataclass
class CompressedContext:
    messages: list[dict]
    summary: str
    tokens_before: int
    tokens_after: int
    tier_counts: dict[Tier, int] = field(default_factory=dict)
    pointer_ids: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        if self.tokens_before == 0:
            return 0.0
        return 1 - (self.tokens_after / self.tokens_before)


def _pointerize(message: dict, store: MemrailStore) -> tuple[dict, str]:
    text = _content_text(message)
    role = message.get("role", "user")
    label = "tool-result" if role == "tool" else "artifact"
    pointer = create_pointer(label)
    pid = pointer.strip("[]").split(":")[-1]
    store.save(pid, {"role": role, "content": text})
    preview = text[:TRUNCATE_PREVIEW].replace("\n", " ")
    new_content = f"{pointer} [{len(text)} chars; preview: {preview}...]"
    return {"role": role, "content": new_content}, pid


def _summarize_group(
    messages: list[dict],
    llm: LLMClient | None,
) -> dict:
    joined = "\n".join(f"{m.get('role','?')}: {_content_text(m)}" for m in messages)
    if llm is not None:
        summary_text = llm.summarize(joined, max_tokens=200)
    else:
        summary_text = f"[memrail:summary] Dropped {len(messages)} stale messages (~{len(joined)} chars)."
    return {"role": "system", "content": summary_text}


def compress(
    messages: list[dict],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    llm_client: LLMClient | None = None,
    store: MemrailStore | None = None,
) -> CompressedContext:
    store = store or MemrailStore()
    tokens_before = count_tokens(messages)
    classified = classify_all(messages)
    counts = tier_counts(classified)

    kept: list[dict] = []
    disposables: list[dict] = []
    pointer_ids: list[str] = []

    for msg, tier in classified:
        if tier == Tier.CRITICAL:
            kept.append(msg)
        elif tier == Tier.USEFUL:
            kept.append(msg)
        elif tier == Tier.RESTORABLE:
            new_msg, pid = _pointerize(msg, store)
            kept.append(new_msg)
            pointer_ids.append(pid)
        else:
            disposables.append(msg)

    if disposables:
        kept.insert(0, _summarize_group(disposables, llm_client))

    if count_tokens(kept) > max_tokens:
        kept = _drop_oldest_useful(kept, max_tokens)

    tokens_after = count_tokens(kept)
    summary = (
        f"kept={counts[Tier.CRITICAL]+counts[Tier.USEFUL]} "
        f"pointerized={counts[Tier.RESTORABLE]} "
        f"summarized={counts[Tier.DISPOSABLE]} "
        f"{tokens_before}→{tokens_after} tokens"
    )

    return CompressedContext(
        messages=kept,
        summary=summary,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        tier_counts=counts,
        pointer_ids=pointer_ids,
    )


def _drop_oldest_useful(messages: list[dict], max_tokens: int) -> list[dict]:
    out = list(messages)
    i = 0
    while count_tokens(out) > max_tokens and i < len(out):
        role = out[i].get("role", "")
        if role == "system":
            i += 1
            continue
        out.pop(i)
    return out
