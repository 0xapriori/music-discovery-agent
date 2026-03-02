"""MCP tool for saving music recommendations to markdown files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

from src.config import RECOMMENDATIONS_DIR


def _format_recommendation(idx: int, rec: dict[str, Any]) -> str:
    """Format a single recommendation as a markdown section."""
    artist = rec.get("artist_name", "Unknown Artist")
    headline = rec.get("headline", "")
    score = rec.get("score")
    why = rec.get("why_youll_love_it", "")
    album = rec.get("start_with_album", "")
    tracks = rec.get("start_with_tracks") or []

    lines = [f"### {idx}. {artist}"]

    parts = []
    if headline:
        parts.append(f'*"{headline}"*')
    if score is not None:
        parts.append(f"Score: {score}/10")
    if parts:
        lines.append(" — ".join(parts))

    if why:
        lines.append("")
        lines.append(why)

    if album or tracks:
        lines.append("")
        lines.append(f"**Start with:** {album}" if album else "**Start with:**")
        for track in tracks:
            lines.append(f"- {track}")

    return "\n".join(lines)


def _save_recommendations_md_impl(
    user_id: str,
    recommendations: list[dict[str, Any]],
    session_summary: str | None = None,
    *,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Core logic for saving recommendations to markdown. Separated for testability."""
    directory = output_dir or RECOMMENDATIONS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    filepath = directory / f"{user_id}.md"

    today = date.today().isoformat()

    sections: list[str] = []

    # Header — only added if creating a new file
    if not filepath.exists():
        sections.append(f"# Music Discoveries — {user_id}\n")

    # Separator between sessions in an existing file
    if filepath.exists():
        sections.append("\n---\n")

    sections.append(f"## Session: {today}\n")

    if session_summary:
        sections.append(f"> {session_summary}\n")

    for idx, rec in enumerate(recommendations, start=1):
        sections.append(_format_recommendation(idx, rec))

    content = "\n".join(sections) + "\n"

    with open(filepath, "a") as f:
        f.write(content)

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Saved {len(recommendations)} recommendation(s) to {filepath}."
                ),
            }
        ]
    }


@tool(
    "save_recommendations_md",
    "Save the current round of music recommendations to a human-readable markdown file. "
    "Call this after presenting recommendations to the user. Multiple rounds accumulate "
    "in the same file, separated by horizontal rules.",
    {
        "user_id": str,
        "recommendations": list,  # list of dicts with artist_name, headline, etc.
        "session_summary": str,  # brief overview of the discovery round
    },
)
async def save_recommendations_md(args: dict[str, Any]) -> dict[str, Any]:
    return _save_recommendations_md_impl(
        user_id=args.get("user_id", "default"),
        recommendations=args.get("recommendations", []),
        session_summary=args.get("session_summary"),
    )
