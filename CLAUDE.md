# Music Discovery Agent

Multi-agent music discovery system built on the Claude Agent SDK. The SDK spawns a `claude` CLI subprocess — no API key needed, uses the user's Claude Pro/Max subscription.

## Architecture

An **orchestrator** (Claude) manages a 3-phase workflow and delegates to 3 subagents:

1. **Web Discovery Agent** (Sonnet) — searches the web for candidate artists
2. **Artist Analyst** (Sonnet) — scores candidates against the user's taste dimensions
3. **Recommendation Synthesizer** (Opus) — writes personalized recommendation write-ups

The orchestrator has access to 4 MCP tools via a local server (`src/tools/server.py`):
- `extract_taste_profile` — structures conversation into a formal TasteProfile
- `save_user_profile` / `load_user_profile` — persist/load profiles as JSON
- `deduplicate_artists` — fuzzy-matches candidate names against known artists

## Running

```bash
python -m src
```

Or via the installed script: `music-discover`

## Testing

```bash
python -m pytest tests/ -v
```

22 tests covering models, storage, and deduplication logic.

## Key Directories

- `src/agents/` — orchestrator, subagent definitions, system prompts
- `src/tools/` — MCP tool implementations and server setup
- `src/models/` — Pydantic models (TasteProfile, ScoredArtist, Recommendation)
- `src/storage/` — abstract StorageBackend + FileStorage implementation
- `tests/fixtures/` — sample taste profile JSON for tests

## 3-Phase Workflow

1. **Taste Profiling** — conversational exchange (3-5 turns), then `extract_taste_profile` tool call
2. **Discovery** — web-discovery-agent → artist-analyst-agent → recommendation-synthesizer (sequential delegation)
3. **Presentation** — orchestrator presents results, handles feedback loops

## Rules

- Never fabricate artist names, album titles, or track names. All data must come from real web searches.
- Anti-preferences (things the user dislikes) must be respected — artists matching anti-preferences should score lower.
- Artists scoring below 5.0 overall are filtered out of final recommendations.
- Budget is capped via `MAX_BUDGET_USD` in `.env` (default: $2.00).
