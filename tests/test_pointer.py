from memrail.core.pointer import create_pointer, get_pointer_id, get_pointer_label, is_pointer


def test_create_pointer_format():
    p = create_pointer("tool-result")
    assert p.startswith("[memrail:tool-result:")
    assert p.endswith("]")


def test_is_pointer():
    p = create_pointer("x")
    assert is_pointer(p)
    assert not is_pointer("just text")


def test_pointer_roundtrip():
    p = create_pointer("artifact")
    pid = get_pointer_id(p)
    assert pid and len(pid) >= 8
    assert get_pointer_label(p) == "artifact"


def test_unique_ids():
    assert create_pointer() != create_pointer()
