"""MCP tools for extracting, saving, and loading taste profiles."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

from src.models.taste_profile import ArtistProfile, TasteDimension, TasteProfile
from src.storage.file_storage import FileStorage

_storage = FileStorage()


@tool(
    "extract_taste_profile",
    "Structure a user's music taste from conversation into a formal TasteProfile. "
    "Call this after gathering enough information about the user's preferences.",
    {
        "user_id": str,
        "known_artists": list,  # list of dicts with name, genres, reasons_liked
        "dimensions": list,  # list of dicts with name, score, description
        "summary": str,
        "anti_preferences": list,  # list of strings
    },
)
async def extract_taste_profile(args: dict[str, Any]) -> dict[str, Any]:
    artists = [ArtistProfile(**a) for a in args.get("known_artists", [])]
    dims = [TasteDimension(**d) for d in args.get("dimensions", [])]

    profile = TasteProfile(
        user_id=args.get("user_id", "default"),
        known_artists=artists,
        dimensions=dims,
        summary=args.get("summary", ""),
        anti_preferences=args.get("anti_preferences", []),
    )

    await _storage.save_profile(profile)

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Taste profile extracted and saved for user '{profile.user_id}'. "
                    f"{len(artists)} artists, {len(dims)} dimensions, "
                    f"{len(profile.anti_preferences)} anti-preferences recorded."
                ),
            }
        ]
    }


@tool(
    "save_user_profile",
    "Save an updated taste profile to persistent storage.",
    {"profile_json": str},
)
async def save_user_profile(args: dict[str, Any]) -> dict[str, Any]:
    import json

    data = json.loads(args["profile_json"])
    profile = TasteProfile.model_validate(data)
    await _storage.save_profile(profile)
    return {
        "content": [
            {"type": "text", "text": f"Profile saved for user '{profile.user_id}'."}
        ]
    }


@tool(
    "load_user_profile",
    "Load a previously saved taste profile by user ID.",
    {"user_id": str},
)
async def load_user_profile(args: dict[str, Any]) -> dict[str, Any]:
    profile = await _storage.load_profile(args["user_id"])
    if profile is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No profile found for user '{args['user_id']}'.",
                }
            ]
        }
    return {
        "content": [{"type": "text", "text": profile.model_dump_json(indent=2)}]
    }
