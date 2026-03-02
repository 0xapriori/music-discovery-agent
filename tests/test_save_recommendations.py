"""Tests for the save_recommendations_md logic."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.tools.recommendations import _save_recommendations_md_impl


@pytest.fixture()
def tmp_dir():
    """Create a temporary directory for recommendation files."""
    tmpdir = tempfile.mkdtemp()
    return Path(tmpdir)


def _sample_recommendations() -> list[dict]:
    return [
        {
            "artist_name": "Floating Points",
            "headline": "If Boards of Canada went to a jazz club",
            "why_youll_love_it": "Lush electronic textures with live instrumentation.",
            "start_with_album": "Crush",
            "start_with_tracks": ["LesAlpx", "Falaise"],
            "score": 8.5,
        },
        {
            "artist_name": "Tirzah",
            "headline": "Minimalist R&B that breathes",
            "why_youll_love_it": "Sparse, intimate production with raw vocals.",
            "start_with_album": "Devotion",
            "start_with_tracks": ["Gladly", "Do You Know"],
            "score": 7.8,
        },
    ]


class TestSaveRecommendationsMd:
    def test_saves_single_round(self, tmp_dir):
        result = _save_recommendations_md_impl(
            user_id="test_user",
            recommendations=_sample_recommendations(),
            session_summary="Explored ambient-electronic crossover.",
            output_dir=tmp_dir,
        )
        text = result["content"][0]["text"]
        assert "2 recommendation(s)" in text

        filepath = tmp_dir / "test_user.md"
        assert filepath.exists()

        content = filepath.read_text()
        assert "# Music Discoveries — test_user" in content
        assert "## Session:" in content
        assert "> Explored ambient-electronic crossover." in content
        assert "### 1. Floating Points" in content
        assert '*"If Boards of Canada went to a jazz club"*' in content
        assert "Score: 8.5/10" in content
        assert "**Start with:** Crush" in content
        assert "- LesAlpx" in content
        assert "### 2. Tirzah" in content

    def test_appends_second_round(self, tmp_dir):
        _save_recommendations_md_impl(
            user_id="test_user",
            recommendations=_sample_recommendations()[:1],
            session_summary="Round 1",
            output_dir=tmp_dir,
        )
        _save_recommendations_md_impl(
            user_id="test_user",
            recommendations=_sample_recommendations()[1:],
            session_summary="Round 2",
            output_dir=tmp_dir,
        )

        content = (tmp_dir / "test_user.md").read_text()
        # Header should appear only once
        assert content.count("# Music Discoveries — test_user") == 1
        # Both sessions present
        assert "Round 1" in content
        assert "Round 2" in content
        # Separator between sessions
        assert "---" in content
        # Both artists present
        assert "Floating Points" in content
        assert "Tirzah" in content

    def test_handles_missing_fields(self, tmp_dir):
        result = _save_recommendations_md_impl(
            user_id="sparse",
            recommendations=[
                {"artist_name": "Mystery Artist"},
                {},
            ],
            output_dir=tmp_dir,
        )
        text = result["content"][0]["text"]
        assert "2 recommendation(s)" in text

        content = (tmp_dir / "sparse.md").read_text()
        assert "### 1. Mystery Artist" in content
        assert "### 2. Unknown Artist" in content

    def test_includes_session_summary_when_provided(self, tmp_dir):
        _save_recommendations_md_impl(
            user_id="summary_test",
            recommendations=_sample_recommendations()[:1],
            session_summary="A focused session on ambient textures.",
            output_dir=tmp_dir,
        )
        content = (tmp_dir / "summary_test.md").read_text()
        assert "> A focused session on ambient textures." in content

    def test_omits_summary_when_none(self, tmp_dir):
        _save_recommendations_md_impl(
            user_id="no_summary",
            recommendations=_sample_recommendations()[:1],
            output_dir=tmp_dir,
        )
        content = (tmp_dir / "no_summary.md").read_text()
        # No blockquote line when summary is absent
        assert "> " not in content
