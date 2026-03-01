from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateArtist(BaseModel):
    """An artist discovered by the web discovery agent."""

    name: str
    genres: list[str] = Field(default_factory=list)
    source: str = Field(
        default="",
        description="Where this artist was found (e.g. 'Pitchfork', 'Reddit r/indieheads')",
    )
    source_url: str = Field(default="")
    description: str = Field(
        default="",
        description="Brief description of the artist's sound",
    )
    key_albums: list[str] = Field(default_factory=list)
    key_tracks: list[str] = Field(default_factory=list)
    active_years: str = Field(default="")


class DimensionScore(BaseModel):
    """Score for a single taste dimension."""

    dimension: str
    score: float = Field(ge=0, le=10)
    reasoning: str = Field(default="")


class ScoredArtist(BaseModel):
    """A candidate artist scored against the user's taste profile."""

    artist: CandidateArtist
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    overall_score: float = Field(ge=0, le=10)
    match_summary: str = Field(
        default="",
        description="Why this artist matches (or doesn't) the user's taste",
    )

    @property
    def average_score(self) -> float:
        if not self.dimension_scores:
            return 0.0
        return sum(d.score for d in self.dimension_scores) / len(self.dimension_scores)
