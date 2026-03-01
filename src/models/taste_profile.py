from __future__ import annotations

from pydantic import BaseModel, Field


class ArtistProfile(BaseModel):
    """An artist the user knows and likes, with reasons why."""

    name: str
    genres: list[str] = Field(default_factory=list)
    reasons_liked: list[str] = Field(
        default_factory=list,
        description="Why the user likes this artist (e.g. 'dense lyricism', 'glitchy production')",
    )


class TasteDimension(BaseModel):
    """A scored axis of the user's taste profile."""

    name: str = Field(description="e.g. 'experimental_production', 'lyrical_density'")
    score: float = Field(ge=0, le=10, description="How important this dimension is (0-10)")
    description: str = Field(
        default="",
        description="What this dimension means for this user",
    )


class TasteProfile(BaseModel):
    """Structured representation of a user's music taste."""

    user_id: str = Field(default="default")
    known_artists: list[ArtistProfile] = Field(default_factory=list)
    dimensions: list[TasteDimension] = Field(default_factory=list)
    summary: str = Field(
        default="",
        description="Natural-language summary of the user's taste",
    )
    anti_preferences: list[str] = Field(
        default_factory=list,
        description="Things the user explicitly dislikes",
    )

    @property
    def known_artist_names(self) -> set[str]:
        return {a.name.lower() for a in self.known_artists}

    def dimensions_dict(self) -> dict[str, float]:
        return {d.name: d.score for d in self.dimensions}
