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


async def _update_taste_profile_impl(
    args: dict[str, Any],
    storage: FileStorage | None = None,
) -> dict[str, Any]:
    """Core logic for updating a taste profile. Separated for testability."""
    store = storage or _storage
    user_id = args.get("user_id", "default")
    profile = await store.load_profile(user_id)

    if profile is None:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"No existing profile found for user '{user_id}'. "
                        "Use extract_taste_profile to create one first."
                    ),
                }
            ]
        }

    changes: list[str] = []

    # --- Add artists (deduplicated) ---
    add_artists = args.get("add_artists") or []
    if add_artists:
        existing_names = profile.known_artist_names
        added = []
        for a in add_artists:
            ap = ArtistProfile(**a) if isinstance(a, dict) else a
            if ap.name.lower() not in existing_names:
                profile.known_artists.append(ap)
                existing_names.add(ap.name.lower())
                added.append(ap.name)
        if added:
            changes.append(f"Added artists: {', '.join(added)}")

    # --- Remove artists ---
    remove_artists = args.get("remove_artists") or []
    if remove_artists:
        remove_lower = {name.lower() for name in remove_artists}
        before = len(profile.known_artists)
        profile.known_artists = [
            a for a in profile.known_artists if a.name.lower() not in remove_lower
        ]
        removed_count = before - len(profile.known_artists)
        if removed_count:
            changes.append(f"Removed {removed_count} artist(s)")

    # --- Adjust dimensions (upsert) ---
    adjust_dims = args.get("adjust_dimensions") or []
    if adjust_dims:
        dims_by_name = {d.name: d for d in profile.dimensions}
        for d in adjust_dims:
            td = TasteDimension(**d) if isinstance(d, dict) else d
            if td.name in dims_by_name:
                dims_by_name[td.name].score = td.score
                if td.description:
                    dims_by_name[td.name].description = td.description
                changes.append(f"Updated dimension '{td.name}' to {td.score}")
            else:
                profile.dimensions.append(td)
                changes.append(f"Added dimension '{td.name}' ({td.score})")

    # --- Anti-preferences ---
    add_anti = args.get("add_anti_preferences") or []
    if add_anti:
        existing_anti = set(profile.anti_preferences)
        new_anti = [p for p in add_anti if p not in existing_anti]
        profile.anti_preferences.extend(new_anti)
        if new_anti:
            changes.append(f"Added anti-preferences: {', '.join(new_anti)}")

    remove_anti = args.get("remove_anti_preferences") or []
    if remove_anti:
        remove_set = set(remove_anti)
        before = len(profile.anti_preferences)
        profile.anti_preferences = [
            p for p in profile.anti_preferences if p not in remove_set
        ]
        removed_count = before - len(profile.anti_preferences)
        if removed_count:
            changes.append(f"Removed {removed_count} anti-preference(s)")

    # --- Summary ---
    summary_update = args.get("summary_update")
    if summary_update:
        profile.summary = summary_update
        changes.append("Updated summary")

    if not changes:
        return {
            "content": [
                {"type": "text", "text": "No changes applied — all fields were empty or unchanged."}
            ]
        }

    await store.save_profile(profile)

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Profile updated for user '{user_id}'. "
                    f"Changes: {'; '.join(changes)}. "
                    f"Profile now has {len(profile.known_artists)} artists, "
                    f"{len(profile.dimensions)} dimensions, "
                    f"{len(profile.anti_preferences)} anti-preferences."
                ),
            }
        ]
    }


@tool(
    "update_taste_profile",
    "Incrementally update an existing taste profile. Loads the profile, merges "
    "changes, and saves. Use this instead of extract_taste_profile when the user "
    "wants to add/remove artists, adjust dimensions, or tweak anti-preferences "
    "without rebuilding the entire profile.",
    {
        "user_id": str,
        "add_artists": list,  # list of dicts with name, genres, reasons_liked
        "remove_artists": list,  # list of artist name strings to remove
        "adjust_dimensions": list,  # list of dicts with name, score, description
        "add_anti_preferences": list,  # list of strings
        "remove_anti_preferences": list,  # list of strings
        "summary_update": str,  # replacement summary string
    },
)
async def update_taste_profile(args: dict[str, Any]) -> dict[str, Any]:
    return await _update_taste_profile_impl(args)
