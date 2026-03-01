"""Tests for taste profile models and storage."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.models.taste_profile import ArtistProfile, TasteDimension, TasteProfile
from src.storage.file_storage import FileStorage

FIXTURES = Path(__file__).parent / "fixtures"


class TestTasteProfileModel:
    def test_create_minimal(self):
        profile = TasteProfile(user_id="test")
        assert profile.user_id == "test"
        assert profile.known_artists == []
        assert profile.dimensions == []

    def test_create_full(self):
        profile = TasteProfile(
            user_id="full_test",
            known_artists=[
                ArtistProfile(
                    name="Clipping.",
                    genres=["noise rap"],
                    reasons_liked=["noise production"],
                )
            ],
            dimensions=[
                TasteDimension(
                    name="experimental_production",
                    score=9.5,
                    description="Likes noisy production",
                )
            ],
            summary="Experimental listener",
            anti_preferences=["generic trap"],
        )
        assert len(profile.known_artists) == 1
        assert profile.known_artists[0].name == "Clipping."
        assert profile.dimensions[0].score == 9.5

    def test_known_artist_names_lowercase(self):
        profile = TasteProfile(
            known_artists=[
                ArtistProfile(name="JPEGMAFIA"),
                ArtistProfile(name="Death Grips"),
            ]
        )
        assert profile.known_artist_names == {"jpegmafia", "death grips"}

    def test_dimensions_dict(self):
        profile = TasteProfile(
            dimensions=[
                TasteDimension(name="intensity", score=9.0),
                TasteDimension(name="lyrical_density", score=8.5),
            ]
        )
        d = profile.dimensions_dict()
        assert d == {"intensity": 9.0, "lyrical_density": 8.5}

    def test_dimension_score_bounds(self):
        with pytest.raises(Exception):
            TasteDimension(name="bad", score=11.0)
        with pytest.raises(Exception):
            TasteDimension(name="bad", score=-1.0)

    def test_load_fixture(self):
        data = json.loads((FIXTURES / "sample_profile.json").read_text())
        profile = TasteProfile.model_validate(data)
        assert profile.user_id == "test_user"
        assert len(profile.known_artists) == 8
        assert len(profile.dimensions) == 6
        assert "Clipping." in {a.name for a in profile.known_artists}

    def test_roundtrip_json(self):
        profile = TasteProfile(
            user_id="roundtrip",
            known_artists=[ArtistProfile(name="Sonic Youth", genres=["noise rock"])],
            dimensions=[TasteDimension(name="experimental_production", score=9.0)],
        )
        json_str = profile.model_dump_json()
        restored = TasteProfile.model_validate_json(json_str)
        assert restored.user_id == profile.user_id
        assert restored.known_artists[0].name == "Sonic Youth"


class TestFileStorage:
    @pytest.mark.asyncio
    async def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(directory=Path(tmpdir))
            profile = TasteProfile(
                user_id="storage_test",
                known_artists=[ArtistProfile(name="Billy Woods")],
                summary="Test profile",
            )
            await storage.save_profile(profile)
            loaded = await storage.load_profile("storage_test")

            assert loaded is not None
            assert loaded.user_id == "storage_test"
            assert loaded.known_artists[0].name == "Billy Woods"

    @pytest.mark.asyncio
    async def test_load_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(directory=Path(tmpdir))
            result = await storage.load_profile("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_list_profiles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileStorage(directory=Path(tmpdir))
            await storage.save_profile(TasteProfile(user_id="user_a"))
            await storage.save_profile(TasteProfile(user_id="user_b"))
            profiles = await storage.list_profiles()
            assert set(profiles) == {"user_a", "user_b"}
