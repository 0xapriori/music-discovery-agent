from __future__ import annotations

import json
from pathlib import Path

from src.config import PROFILES_DIR
from src.models.taste_profile import TasteProfile

from .base import StorageBackend


class FileStorage(StorageBackend):
    """JSON file-based storage for taste profiles."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or PROFILES_DIR
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, user_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_id)
        return self.directory / f"{safe_id}.json"

    async def save_profile(self, profile: TasteProfile) -> None:
        path = self._path_for(profile.user_id)
        path.write_text(profile.model_dump_json(indent=2))

    async def load_profile(self, user_id: str) -> TasteProfile | None:
        path = self._path_for(user_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return TasteProfile.model_validate(data)

    async def list_profiles(self) -> list[str]:
        return [p.stem for p in self.directory.glob("*.json")]
