"""Artifact store. In-memory default; optional JSON file persistence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemrailStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self._data: dict[str, Any] = {}
        self._path = Path(path).expanduser() if path else None
        if self._path and self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except json.JSONDecodeError:
                self._data = {}

    def save(self, pointer_id: str, content: Any) -> None:
        self._data[pointer_id] = content
        self._flush()

    def get(self, pointer_id: str) -> Any | None:
        return self._data.get(pointer_id)

    def list_pointers(self) -> list[str]:
        return list(self._data.keys())

    def clear(self) -> None:
        self._data.clear()
        self._flush()

    def _flush(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, default=str, indent=2))
