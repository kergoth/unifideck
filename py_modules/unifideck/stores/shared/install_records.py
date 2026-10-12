"""Per-store archive install records, independent of connection state."""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class InstallRecords:
    def __init__(self, store: str) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", store):
            raise ValueError("Invalid store namespace")
        self._store = store

    def _directory(self) -> Path:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        return Path(base) / "unifideck" / f"{self._store}_installed"

    def _path(self, game_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", game_id):
            raise ValueError("Invalid install record ID")
        return self._directory() / f"{game_id}.json"

    def save(
        self,
        game_id: str,
        *,
        title: str,
        install_path: str,
        exe_path: str,
        archive_path: str = "",
    ) -> None:
        path = self._path(game_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "game_id": game_id,
            "title": title,
            "install_path": install_path,
            "exe_path": exe_path,
            "archive_path": archive_path,
        }
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=".record-")
        temp = Path(name)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(data, stream, indent=2)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)

    def load(self, game_id: str) -> dict[str, Any] | None:
        path = self._path(game_id)
        try:
            data = json.loads(path.read_text())
            return data if isinstance(data, dict) else None
        except (OSError, ValueError):
            return None

    def remove(self, game_id: str) -> None:
        self._path(game_id).unlink(missing_ok=True)

    def load_all(self) -> dict[str, dict[str, Any]]:
        result = {}
        for path in self._directory().glob("*.json"):
            try:
                data = self.load(path.stem)
            except ValueError:
                data = None
            if data is not None:
                result[path.stem] = data
            else:
                logger.warning("[%s installs] skipping unreadable record %s", self._store, path.name)
        return result
