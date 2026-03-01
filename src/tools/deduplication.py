"""MCP tool for fuzzy artist deduplication."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool
from thefuzz import fuzz


def _is_duplicate(name_a: str, name_b: str, threshold: int = 90) -> bool:
    """Check if two artist names are likely the same artist."""
    a = name_a.lower().strip()
    b = name_b.lower().strip()
    if a == b:
        return True
    if fuzz.ratio(a, b) >= threshold:
        return True
    # token_sort catches reordered words (e.g. "Woods, Billy" vs "Billy Woods")
    if fuzz.token_sort_ratio(a, b) >= threshold:
        return True
    return False


def deduplicate_artist_list(
    candidates: list[str],
    known_artists: list[str],
    threshold: int = 90,
) -> list[str]:
    """Remove duplicates and already-known artists from a candidate list.

    Returns the deduplicated list of genuinely new artist names.
    """
    known_lower = [k.lower().strip() for k in known_artists]
    seen: list[str] = []
    result: list[str] = []

    for candidate in candidates:
        c_lower = candidate.lower().strip()

        # Skip if matches a known artist
        if any(_is_duplicate(c_lower, k, threshold) for k in known_lower):
            continue

        # Skip if already seen in results
        if any(_is_duplicate(c_lower, s, threshold) for s in seen):
            continue

        seen.append(c_lower)
        result.append(candidate)

    return result


@tool(
    "deduplicate_artists",
    "Remove duplicate artist names and filter out artists the user already knows. "
    "Returns only genuinely new, unique artist names.",
    {
        "candidate_names": list,  # list of str
        "known_artist_names": list,  # list of str
    },
)
async def deduplicate_artists(args: dict[str, Any]) -> dict[str, Any]:
    candidates = args.get("candidate_names", [])
    known = args.get("known_artist_names", [])

    unique = deduplicate_artist_list(candidates, known)

    removed_count = len(candidates) - len(unique)
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Deduplicated {len(candidates)} candidates → {len(unique)} unique new artists "
                    f"({removed_count} removed as duplicates or already known).\n\n"
                    f"Unique artists: {', '.join(unique)}"
                ),
            }
        ]
    }
