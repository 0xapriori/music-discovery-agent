"""Tests for fuzzy artist deduplication."""

from __future__ import annotations

from src.tools.deduplication import _is_duplicate, deduplicate_artist_list


class TestIsDuplicate:
    def test_exact_match(self):
        assert _is_duplicate("Death Grips", "Death Grips")

    def test_case_insensitive(self):
        assert _is_duplicate("JPEGMAFIA", "jpegmafia")

    def test_whitespace(self):
        assert _is_duplicate("  Sonic Youth ", "Sonic Youth")

    def test_close_spelling(self):
        assert _is_duplicate("Clipping.", "Clipping")

    def test_different_artists(self):
        assert not _is_duplicate("Death Grips", "Sonic Youth")

    def test_partial_match_different(self):
        assert not _is_duplicate("Billy Woods", "Billy Joel")


class TestDeduplicateArtistList:
    def test_removes_known_artists(self):
        candidates = ["Death Grips", "New Artist", "JPEGMAFIA"]
        known = ["Death Grips", "JPEGMAFIA"]
        result = deduplicate_artist_list(candidates, known)
        assert result == ["New Artist"]

    def test_removes_duplicates_within_candidates(self):
        candidates = ["Artist A", "artist a", "Artist B"]
        result = deduplicate_artist_list(candidates, [])
        assert len(result) == 2
        assert result[0] == "Artist A"
        assert result[1] == "Artist B"

    def test_fuzzy_dedup(self):
        candidates = ["Clipping.", "Clipping", "Billy Woods"]
        result = deduplicate_artist_list(candidates, [])
        assert len(result) == 2
        assert result[0] == "Clipping."
        assert result[1] == "Billy Woods"

    def test_empty_inputs(self):
        assert deduplicate_artist_list([], []) == []
        assert deduplicate_artist_list([], ["Death Grips"]) == []

    def test_no_overlap(self):
        candidates = ["Artist A", "Artist B"]
        known = ["Artist C", "Artist D"]
        result = deduplicate_artist_list(candidates, known)
        assert result == ["Artist A", "Artist B"]

    def test_all_known(self):
        candidates = ["Death Grips", "JPEGMAFIA"]
        known = ["Death Grips", "JPEGMAFIA"]
        result = deduplicate_artist_list(candidates, known)
        assert result == []
