"""CLI entry point for the music discovery agent."""

from __future__ import annotations

import asyncio
import sys

from src.agents.orchestrator import DiscoverySession

WELCOME = """\
=== Music Discovery Agent ===
I'll help you find new artists you'll love.
Let's start by talking about your music taste.

Type 'quit' or 'exit' to end the session.
==============================
"""


async def run_session() -> None:
    session = DiscoverySession()
    await session.start()

    print(WELCOME)

    # Kick off with an opening prompt
    opening = (
        "Hello! I'm your music discovery agent. I'd love to learn about your taste "
        "in music so I can find new artists for you. What are some artists you've been "
        "really into lately, and what draws you to them?"
    )
    print(f"Agent: {opening}\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("\nThanks for discovering music with me!")
                break

            print("\nAgent: ", end="", flush=True)
            async for chunk in session.send_message(user_input):
                print(chunk, end="", flush=True)
            print("\n")

    except KeyboardInterrupt:
        print("\n\nSession interrupted.")
    finally:
        await session.close()


def main() -> None:
    asyncio.run(run_session())


if __name__ == "__main__":
    main()
