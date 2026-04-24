from memrail.core.classifier import Tier, classify, classify_all


def test_system_message_critical():
    msg = {"role": "system", "content": "You are a helpful agent."}
    assert classify(msg, 0, 10) == Tier.CRITICAL


def test_error_content_critical():
    msg = {"role": "user", "content": "Got an Error: traceback here"}
    assert classify(msg, 0, 10) == Tier.CRITICAL


def test_large_tool_output_restorable():
    msg = {"role": "tool", "content": "data: " + "x" * 5000}
    assert classify(msg, 0, 10) == Tier.RESTORABLE


def test_recent_message_useful():
    msg = {"role": "user", "content": "pick next step"}
    assert classify(msg, 9, 10) == Tier.USEFUL


def test_old_noise_disposable():
    msg = {"role": "user", "content": "chit chat"}
    assert classify(msg, 0, 20) == Tier.DISPOSABLE


def test_classify_all_preserves_order():
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    out = classify_all(msgs)
    assert [m for m, _ in out] == msgs
