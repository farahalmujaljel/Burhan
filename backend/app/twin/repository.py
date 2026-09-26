"""Append-only log of TwinUpdates (the twin's change history)."""

import threading
from pathlib import Path

from app.schemas.twin import TwinUpdate


class TwinUpdateLog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._updates: list[TwinUpdate] = []
        if path and path.exists():
            self._updates = [
                TwinUpdate.model_validate_json(line)
                for line in path.read_text("utf-8").splitlines()
                if line.strip()
            ]

    def append(self, update: TwinUpdate) -> None:
        with self._lock:
            self._updates.append(update)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(update.model_dump_json() + "\n")

    def list(self, limit: int | None = None) -> list[TwinUpdate]:
        """Newest first."""
        with self._lock:
            items = list(reversed(self._updates))
        return items[:limit] if limit else items

    def last(self) -> TwinUpdate | None:
        with self._lock:
            return self._updates[-1] if self._updates else None
