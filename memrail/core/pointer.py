"""Pointer tokens. Format: [memrail:<label>:<uuid>]"""
from __future__ import annotations

import re
import uuid

_POINTER_RE = re.compile(r"\[memrail:([a-zA-Z0-9_\-]+):([a-f0-9\-]{8,})\]")


def create_pointer(label: str = "artifact") -> str:
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", label) or "artifact"
    return f"[memrail:{safe}:{uuid.uuid4().hex}]"


def is_pointer(text: str) -> bool:
    return bool(_POINTER_RE.search(text or ""))


def get_pointer_id(text: str) -> str | None:
    m = _POINTER_RE.search(text or "")
    return m.group(2) if m else None


def get_pointer_label(text: str) -> str | None:
    m = _POINTER_RE.search(text or "")
    return m.group(1) if m else None
