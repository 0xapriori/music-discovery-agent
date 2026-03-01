"""Tests for the update_taste_profile logic."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.models.taste_profile import ArtistProfile, TasteDimension, TasteProfile
from src.storage.file_storage import FileStorage
from src.tools.taste_profile import _update_taste_profile_impl


@pytest.fixture()
def tmp_storage():
    """Create a temporary FileStorage instance."""
    tmpdir = tempfile.mkdtemp()
    return FileStorage(directory=Path(tmpdir))


async def _seed_profile(storage: FileStorage) -> TasteProfile:
    """Create and save a baseline profile for testing updates."""
    profile = TasteProfile(
        user_id="test_user",
        known_artists=[
            ArtistProfile(name="Clipping.", genres=["noise rap"], reasons_liked=["abrasive production"]),
            ArtistProfile(name="JPEGMAFIA", genres=["experimental hip hop"], reasons_liked=["glitchy beats"]),
        ],
        dimensions=[
            TasteDimension(name="experimental_production", score=9.5, description="Likes noisy production"),
            TasteDimension(name="lyrical_density", score=8.5, description="Values dense lyrics"),
        ],
        summary="Experimental listener who likes abrasive sounds.",
        anti_preferences=["generic trap", "overly polished pop"],
    )
    await storage.save_profile(profile)
    return profile


class TestUpdateTasteProfile:
    @pytest.mark.asyncio
    async def test_add_artists_deduped(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "add_artists": [
                {"name": "Death Grips", "genres": ["noise rap"], "reasons_liked": ["chaos"]},
                {"name": "Clipping.", "genres": ["noise rap"], "reasons_liked": ["already known"]},
            ],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Death Grips" in text
        # Clipping. should be deduped (already exists)
        profile = await tmp_storage.load_profile("test_user")
        artist_names = {a.name for a in profile.known_artists}
        assert "Death Grips" in artist_names
        assert len([a for a in profile.known_artists if a.name == "Clipping."]) == 1

    @pytest.mark.asyncio
    async def test_remove_artists(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "remove_artists": ["JPEGMAFIA"],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Removed 1 artist" in text
        profile = await tmp_storage.load_profile("test_user")
        assert "jpegmafia" not in profile.known_artist_names

    @pytest.mark.asyncio
    async def test_upsert_dimensions_update_existing(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "adjust_dimensions": [
                {"name": "experimental_production", "score": 7.0, "description": "Toned down"},
            ],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Updated dimension 'experimental_production' to 7.0" in text
        profile = await tmp_storage.load_profile("test_user")
        dims = profile.dimensions_dict()
        assert dims["experimental_production"] == 7.0

    @pytest.mark.asyncio
    async def test_upsert_dimensions_add_new(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "adjust_dimensions": [
                {"name": "melodic_warmth", "score": 6.0, "description": "New dimension"},
            ],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Added dimension 'melodic_warmth'" in text
        profile = await tmp_storage.load_profile("test_user")
        dims = profile.dimensions_dict()
        assert "melodic_warmth" in dims
        assert dims["melodic_warmth"] == 6.0

    @pytest.mark.asyncio
    async def test_add_anti_preferences(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "add_anti_preferences": ["auto-tune", "generic trap"],  # "generic trap" already exists
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "auto-tune" in text
        profile = await tmp_storage.load_profile("test_user")
        assert "auto-tune" in profile.anti_preferences
        # "generic trap" should not be duplicated
        assert profile.anti_preferences.count("generic trap") == 1

    @pytest.mark.asyncio
    async def test_remove_anti_preferences(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "remove_anti_preferences": ["generic trap"],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Removed 1 anti-preference" in text
        profile = await tmp_storage.load_profile("test_user")
        assert "generic trap" not in profile.anti_preferences

    @pytest.mark.asyncio
    async def test_error_when_no_profile_exists(self, tmp_storage):
        result = await _update_taste_profile_impl({
            "user_id": "nonexistent_user",
            "add_artists": [{"name": "Radiohead", "genres": ["alt rock"], "reasons_liked": ["complex"]}],
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "No existing profile found" in text
        assert "extract_taste_profile" in text

    @pytest.mark.asyncio
    async def test_empty_update_no_changes(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "No changes applied" in text

    @pytest.mark.asyncio
    async def test_summary_update(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "summary_update": "Now also into ambient and drone.",
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Updated summary" in text
        profile = await tmp_storage.load_profile("test_user")
        assert profile.summary == "Now also into ambient and drone."

    @pytest.mark.asyncio
    async def test_multiple_changes_at_once(self, tmp_storage):
        await _seed_profile(tmp_storage)
        result = await _update_taste_profile_impl({
            "user_id": "test_user",
            "add_artists": [{"name": "Sonic Youth", "genres": ["noise rock"], "reasons_liked": ["feedback"]}],
            "remove_artists": ["JPEGMAFIA"],
            "adjust_dimensions": [{"name": "intensity", "score": 9.0, "description": "High energy"}],
            "add_anti_preferences": ["mumble rap"],
            "summary_update": "Expanded taste profile.",
        }, storage=tmp_storage)
        text = result["content"][0]["text"]
        assert "Sonic Youth" in text
        assert "Removed 1 artist" in text
        assert "intensity" in text
        assert "mumble rap" in text
        assert "Updated summary" in text

        profile = await tmp_storage.load_profile("test_user")
        assert "sonic youth" in profile.known_artist_names
        assert "jpegmafia" not in profile.known_artist_names
        assert "intensity" in profile.dimensions_dict()
        assert "mumble rap" in profile.anti_preferences
        assert profile.summary == "Expanded taste profile."
