"""CLI entry point for the music discovery agent."""

from __future__ import annotations

import asyncio
import sys

from src.agents.orchestrator import DiscoverySession
from src.storage.file_storage import FileStorage

WELCOME = """\
=== Music Discovery Agent ===
I'll help you find new artists you'll love.
Let's start by talking about your music taste.

Type /help for available commands, or 'quit' to exit.
==============================
"""

HELP_TEXT = """\
Available commands:
  /help              Show this help message
  /new               Start a fresh discovery round (keeps your profile)
  /profile           Display your current taste profile
  /add <artists>     Add artists to your profile (comma-separated)
  /save              Save your profile for next session
  /quit              Exit the session
"""


async def _check_saved_profiles() -> str | None:
    """Check for saved profiles and prompt user to resume one."""
    storage = FileStorage()
    profiles = await storage.list_profiles()

    if not profiles:
        return None

    print(f"\nSaved profiles found: {', '.join(profiles)}")
    try:
        choice = input("Enter a name to resume, or press Enter to start fresh: ").strip()
    except EOFError:
        return None

    if choice and choice in profiles:
        return choice

    return None


def _handle_slash_command(command: str) -> str | None:
    """Handle slash commands. Returns a system message to send to the agent,
    or empty string for commands handled purely in the CLI, or None if not a command."""
    if not command.startswith("/"):
        return None

    parts = command.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/help":
        print(HELP_TEXT)
        return ""

    if cmd in ("/quit", "/exit"):
        return "/quit"

    if cmd == "/new":
        return "[SYSTEM] The user wants a fresh discovery round. Load their profile " \
               "with load_user_profile to preserve known_artists, then start Phase 1 " \
               "to explore a new direction."

    if cmd == "/profile":
        return "[SYSTEM] Load the user's profile with load_user_profile and display " \
               "a readable summary of their taste dimensions, known artists, and " \
               "anti-preferences."

    if cmd == "/add":
        if not arg:
            print("Usage: /add Artist1, Artist2, ...")
            return ""
        return (
            f"[SYSTEM] The user wants to add these artists to their profile: {arg}. "
            "Call update_taste_profile with add_artists for each artist name. "
            "Confirm what was added."
        )

    if cmd == "/save":
        return "[SYSTEM] Save the user's current profile using save_user_profile. " \
               "Confirm that it has been saved."

    print(f"Unknown command: {cmd}. Type /help for available commands.")
    return ""


async def run_session() -> None:
    session = DiscoverySession()
    await session.start()

    print(WELCOME)

    # Check for saved profiles to resume
    resumed_user = await _check_saved_profiles()

    if resumed_user:
        session.user_id = resumed_user
        print(f"\nResuming profile: {resumed_user}\n")
        print("Agent: ", end="", flush=True)
        system_msg = (
            f"[SYSTEM] Resuming session for user '{resumed_user}'. "
            "Load their profile with load_user_profile and greet them. "
            "Summarize their taste profile briefly and ask what they'd like to do: "
            "get new recommendations, refine their profile, or explore a new direction."
        )
        async for chunk in session.send_message(system_msg):
            print(chunk, end="", flush=True)
        print("\n")
    else:
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

            # Handle slash commands
            result = _handle_slash_command(user_input)
            if result is not None:
                if result == "":
                    # Command handled locally (e.g. /help), no agent call needed
                    continue
                if result == "/quit":
                    print("\nThanks for discovering music with me!")
                    break
                # /new needs a session reset before sending the system message
                if user_input.split()[0].lower() == "/new":
                    await session.reset()
                # Send system message to agent
                print("\nAgent: ", end="", flush=True)
                async for chunk in session.send_message(result):
                    print(chunk, end="", flush=True)
                print("\n")
                continue

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
