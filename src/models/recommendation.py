from __future__ import annotations

from pydantic import BaseModel, Field

from .artist import ScoredArtist


class Recommendation(BaseModel):
    """A single artist recommendation with entry points."""

    artist_name: str
    headline: str = Field(description="One-line hook, e.g. 'If Clipping. produced a punk album'")
    why_youll_love_it: str = Field(description="Personalized paragraph connecting to user's taste")
    start_with_album: str = Field(default="")
    start_with_tracks: list[str] = Field(default_factory=list)
    scored_artist: ScoredArtist | None = Field(
        default=None,
        description="Full scoring data backing this rec",
    )


class RecommendationReport(BaseModel):
    """The final output of a discovery session."""

    recommendations: list[Recommendation] = Field(default_factory=list)
    search_sources_used: list[str] = Field(default_factory=list)
    candidates_considered: int = 0
    session_summary: str = Field(
        default="",
        description="Brief overview of the discovery process",
    )
