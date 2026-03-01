"""Orchestrator — manages the multi-turn discovery session."""

from __future__ import annotations

from collections.abc import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

from src.config import MAX_BUDGET_USD

from .definitions import SUBAGENTS
from .prompts import ORCHESTRATOR_PROMPT


class DiscoverySession:
    """Interface-agnostic music discovery session.

    Wraps ClaudeSDKClient in a simple send/receive interface that works
    for both CLI (print to stdout) and web (send via WebSocket).
    """

    def __init__(self, user_id: str = "default") -> None:
        self.user_id = user_id
        self._client: ClaudeSDKClient | None = None

    async def start(self) -> None:
        """Initialize the SDK client and connect."""
        options = ClaudeAgentOptions(
            system_prompt=ORCHESTRATOR_PROMPT,
            permission_mode="acceptEdits",
            agents=SUBAGENTS,
            allowed_tools=[
                "WebSearch",
                "WebFetch",
                "Task",
                "mcp__music-discovery__extract_taste_profile",
                "mcp__music-discovery__save_user_profile",
                "mcp__music-discovery__load_user_profile",
                "mcp__music-discovery__deduplicate_artists",
            ],
            max_budget_usd=MAX_BUDGET_USD,
        )
        self._client = ClaudeSDKClient(options=options)
        await self._client.connect()

    async def send_message(self, user_input: str) -> AsyncIterator[str]:
        """Send a user message and yield text chunks from the response."""
        if self._client is None:
            raise RuntimeError("Session not started. Call start() first.")

        await self._client.query(user_input)

        async for message in self._client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text
            elif isinstance(message, ResultMessage):
                if message.subtype == "error_during_execution":
                    yield f"\n[Error: {getattr(message, 'error', 'unknown error')}]\n"

    async def close(self) -> None:
        """Disconnect the client."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None
