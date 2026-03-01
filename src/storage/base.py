from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.taste_profile import TasteProfile


class StorageBackend(ABC):
    """Abstract interface for persisting taste profiles."""

    @abstractmethod
    async def save_profile(self, profile: TasteProfile) -> None: ...

    @abstractmethod
    async def load_profile(self, user_id: str) -> TasteProfile | None: ...

    @abstractmethod
    async def list_profiles(self) -> list[str]: ...
