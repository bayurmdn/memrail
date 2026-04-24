from memrail.core.store import MemrailStore


def test_save_and_get_in_memory():
    s = MemrailStore()
    s.save("abc", {"hello": "world"})
    assert s.get("abc") == {"hello": "world"}


def test_missing_returns_none():
    s = MemrailStore()
    assert s.get("nope") is None


def test_list_and_clear():
    s = MemrailStore()
    s.save("a", 1)
    s.save("b", 2)
    assert set(s.list_pointers()) == {"a", "b"}
    s.clear()
    assert s.list_pointers() == []


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "store.json"
    s1 = MemrailStore(path)
    s1.save("x", "value")
    s2 = MemrailStore(path)
    assert s2.get("x") == "value"
