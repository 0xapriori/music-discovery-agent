"""MCP server setup — bundles all custom tools into a single server."""

from __future__ import annotations

from claude_agent_sdk import create_sdk_mcp_server

from .deduplication import deduplicate_artists
from .taste_profile import (
    extract_taste_profile,
    load_user_profile,
    save_user_profile,
    update_taste_profile,
)

music_tools_server = create_sdk_mcp_server(
    name="music-discovery",
    version="0.1.0",
    tools=[
        extract_taste_profile,
        save_user_profile,
        load_user_profile,
        update_taste_profile,
        deduplicate_artists,
    ],
)
