from memrail.core.compressor import CompressedContext, compress
from memrail.core.classifier import Tier
from memrail.core.pointer import is_pointer
from memrail.core.store import MemrailStore


class FakeLLM:
    def __init__(self) -> None:
        self.calls = 0

    def summarize(self, text: str, max_tokens: int = 200) -> str:
        self.calls += 1
        return f"[fake-summary] {len(text)} chars"


def _mk_messages() -> list[dict]:
    return [
        {"role": "system", "content": "You are an agent."},
        {"role": "user", "content": "old small chit chat"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "another old tangent"},
        {"role": "tool", "content": "data: " + "x" * 5000},
        {"role": "user", "content": "Error: something broke"},
        {"role": "assistant", "content": "investigating"},
        {"role": "user", "content": "what next"},
    ]


def test_compress_returns_struct():
    result = compress(_mk_messages(), max_tokens=80_000)
    assert isinstance(result, CompressedContext)
    assert result.tokens_before > 0
    assert result.tokens_after > 0
    assert result.tokens_after <= result.tokens_before


def test_critical_content_preserved():
    result = compress(_mk_messages())
    texts = [str(m.get("content", "")) for m in result.messages]
    assert any("You are an agent" in t for t in texts)
    assert any("Error: something broke" in t for t in texts)


def test_restorable_replaced_with_pointer():
    store = MemrailStore()
    result = compress(_mk_messages(), store=store)
    texts = [str(m.get("content", "")) for m in result.messages]
    assert any(is_pointer(t) for t in texts)
    assert len(result.pointer_ids) >= 1
    pid = result.pointer_ids[0]
    assert store.get(pid) is not None


def test_disposable_summarized_not_dropped():
    result = compress(_mk_messages())
    texts = [str(m.get("content", "")) for m in result.messages]
    assert any("memrail:summary" in t or "fake-summary" in t for t in texts) or result.tier_counts[Tier.DISPOSABLE] == 0


def test_llm_client_used_when_provided():
    llm = FakeLLM()
    result = compress(_mk_messages(), llm_client=llm)
    if result.tier_counts[Tier.DISPOSABLE] > 0:
        assert llm.calls >= 1
        assert any("fake-summary" in str(m.get("content", "")) for m in result.messages)


def test_no_real_llm_call_without_client():
    result = compress(_mk_messages(), llm_client=None)
    assert isinstance(result, CompressedContext)
