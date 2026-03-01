# Music Discovery Agent

A multi-agent music discovery system powered by [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk). It learns your taste through conversation, searches the web for new artists, scores them against your preferences, and writes personalized recommendations.

No API key needed — runs on your Claude Pro or Max subscription via the `claude` CLI.

## How It Works

The system uses an orchestrator that delegates to three specialized subagents:

```
                    ┌──────────────────────┐
                    │     Orchestrator     │
                    │  (Taste Profiling +  │
                    │   Session Manager)   │
                    └──────┬───────────────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
              ▼            ▼                ▼
  ┌───────────────┐ ┌──────────────┐ ┌──────────────────┐
  │ Web Discovery │ │   Artist     │ │  Recommendation  │
  │   Agent       │ │   Analyst    │ │   Synthesizer    │
  │  (Sonnet)     │ │  (Sonnet)    │ │    (Opus)        │
  └───────────────┘ └──────────────┘ └──────────────────┘
```

### Three-Phase Workflow

**Phase 1 — Taste Profiling:** The orchestrator has a natural conversation with you (3-5 exchanges) to understand what you like and why. It asks about specific artists, what draws you to certain sounds, production styles, lyrical approaches, and what you actively dislike. Once it has enough, it calls the `extract_taste_profile` MCP tool to formalize your preferences into scored taste dimensions.

**Phase 2 — Discovery:** The orchestrator delegates to its subagents:
1. **Web Discovery Agent** searches Pitchfork, Bandcamp, Reddit, RYM, YouTube, and music blogs for 10-15 candidates matching your profile
2. **Artist Analyst** researches each candidate and scores them against your taste dimensions (details below)
3. **Recommendation Synthesizer** writes personalized write-ups for the top matches

**Phase 3 — Presentation:** Results are presented with specific entry points ("Start with this album, specifically this track"). You can give feedback — "I already know that one," "more like X," "tell me more about Y" — and the system refines.

## The Scoring Algorithm

The scoring system is central to how recommendations are ranked. Here's how it works end-to-end.

### Taste Dimensions

During profiling, your preferences are encoded into **6 scored dimensions** (0-10 scale). Each dimension captures a different axis of taste:

| Dimension | Description | Example Score |
|-----------|-------------|---------------|
| `experimental_production` | Preference for unconventional, noisy, glitchy production techniques | 9.5 |
| `lyrical_density` | Values complex, layered, literary lyricism | 8.5 |
| `intensity` | Drawn to aggressive, high-energy, confrontational music | 9.0 |
| `genre_blending` | Appreciates artists who cross genre boundaries freely | 8.0 |
| `underground_ethos` | Prefers independent, DIY, anti-mainstream approaches | 8.5 |
| `conceptual_ambition` | Values albums with thematic or conceptual frameworks | 7.5 |

Dimensions are dynamic — they're generated from the conversation, not hardcoded. A jazz listener might get dimensions like `harmonic_complexity` and `improvisational_freedom` instead.

### Scoring Rubric

Each candidate artist is scored on every dimension using this scale:

| Score | Meaning |
|-------|---------|
| 0-2 | **Poor match** — doesn't align with this dimension at all |
| 3-4 | **Weak match** — some tangential connection |
| 5-6 | **Moderate match** — shares some qualities |
| 7-8 | **Strong match** — clearly aligns with this taste dimension |
| 9-10 | **Exceptional match** — this is exactly what the dimension describes |

### How Overall Scores Are Calculated

The Artist Analyst agent:
1. Searches the web for reviews, descriptions, and comparisons for each candidate
2. Scores them on each of the user's taste dimensions with reasoning
3. Calculates an **overall score** as a weighted average (weighted by dimension importance — i.e., the dimension's own score from the taste profile)
4. Writes a match summary connecting the artist to the user's stated preferences

The formula:

```
overall_score = Σ(dimension_score × dimension_weight) / Σ(dimension_weight)
```

Where `dimension_weight` is how important that dimension is to the user (the score from their taste profile) and `dimension_score` is how well the candidate matches that dimension.

### Anti-Preferences

The taste profile also captures **anti-preferences** — things the user explicitly dislikes. Examples:

- "overly polished pop production"
- "generic trap beats"
- "surface-level party lyrics"

If a candidate artist exhibits traits matching an anti-preference, the analyst notes it and it factors into the scoring. Artists below 5.0 overall are filtered out entirely.

### Example: Scoring a Candidate

Say a user's profile has the dimensions above, and the Web Discovery Agent finds **Machine Girl** (electronic/noise/breakcore).

The Artist Analyst might score them:

| Dimension | Weight | Score | Reasoning |
|-----------|--------|-------|-----------|
| `experimental_production` | 9.5 | 9.0 | "Abrasive digital maximalism, distorted breakbeats" |
| `lyrical_density` | 8.5 | 3.0 | "Primarily instrumental, minimal lyrics" |
| `intensity` | 9.0 | 9.5 | "Relentless BPM, harsh noise elements" |
| `genre_blending` | 8.0 | 8.5 | "Fuses breakcore, noise, vaporwave, punk" |
| `underground_ethos` | 8.5 | 9.0 | "DIY releases, underground scene staple" |
| `conceptual_ambition` | 7.5 | 6.0 | "Some thematic albums, not primarily concept-driven" |

```
overall = (9.5×9.0 + 8.5×3.0 + 9.0×9.5 + 8.0×8.5 + 8.5×9.0 + 7.5×6.0)
        / (9.5 + 8.5 + 9.0 + 8.0 + 8.5 + 7.5)
        = 393.75 / 51.0
        = 7.72
```

Result: 7.72/10 — strong match overall, held back by the lyrical density dimension since Machine Girl is largely instrumental.

### Deduplication

Before scoring, candidates are run through a fuzzy deduplication tool (using `thefuzz`) that:
- Removes artists the user already listed as known favorites
- Catches near-duplicates like "Clipping." vs "Clipping" or "Billy Woods" vs "Woods, Billy"
- Uses both exact matching and token-sort ratio with a 90% threshold

## Quick Start

### Prerequisites

- **Python 3.10+**
- **Claude Pro or Max subscription** — the agent runs via the `claude` CLI, which uses your subscription (no API key needed)
- **Claude Code CLI** installed and authenticated (`claude` command available in your terminal)

### Install

```bash
git clone https://github.com/0xapriori/music-discovery-agent.git
cd music-discovery-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure

```bash
cp .env.example .env
# Edit .env if you want to change the budget cap (default: $2.00 per session)
```

### Run

```bash
python -m src
```

This starts an interactive CLI session. The agent will greet you and ask about your music taste.

### Example Session

```
=== Music Discovery Agent ===
I'll help you find new artists you'll love.
Let's start by talking about your music taste.
==============================

Agent: Hello! I'm your music discovery agent. I'd love to learn about your
taste in music so I can find new artists for you. What are some artists
you've been really into lately, and what draws you to them?

You: I've been deep into Clipping. and JPEGMAFIA lately. I love the noisy,
abrasive production — the way they use distortion and glitchy textures as
instruments rather than effects. Also really into Billy Woods for the dense,
literary lyricism.

Agent: Great taste — that's a really specific intersection of experimental
production and lyrical depth. A few follow-ups...
[conversation continues for 3-5 exchanges]

Agent: I've built your taste profile. Let me search for some artists you
might not know yet...
[web discovery, scoring, and recommendation phases run]

Agent: Here are your recommendations:

1. **Machine Girl** — "If Death Grips built a DDR cabinet"
   Why: Shares the abrasive digital maximalism you love in JPEGMAFIA...
   Start with: *...Because I'm Young Arrogant and Hate Everything*, specifically "Krystle (URL CYBER PALACE)"
   Score: 7.7/10
   ...
```

## Project Structure

```
music-discovery-agent/
├── src/
│   ├── __init__.py
│   ├── __main__.py            # `python -m src` entry point
│   ├── app.py                 # CLI session loop
│   ├── config.py              # Paths, env vars, budget config
│   ├── agents/
│   │   ├── definitions.py     # AgentDefinition objects for 3 subagents
│   │   ├── orchestrator.py    # DiscoverySession wrapping ClaudeSDKClient
│   │   └── prompts.py         # System prompts for all agents
│   ├── models/
│   │   ├── artist.py          # CandidateArtist, DimensionScore, ScoredArtist
│   │   ├── recommendation.py  # Recommendation, RecommendationReport
│   │   └── taste_profile.py   # TasteProfile, TasteDimension, ArtistProfile
│   ├── storage/
│   │   ├── base.py            # StorageBackend abstract interface
│   │   └── file_storage.py    # JSON file-based profile persistence
│   └── tools/
│       ├── deduplication.py   # Fuzzy artist name deduplication
│       ├── server.py          # MCP server bundling all tools
│       └── taste_profile.py   # Extract/save/load profile MCP tools
├── tests/
│   ├── fixtures/
│   │   └── sample_profile.json
│   ├── test_deduplication.py  # 12 tests for fuzzy matching
│   └── test_taste_profile.py  # 10 tests for models + storage
├── data/
│   └── profiles/              # Saved user profiles (gitignored)
├── pyproject.toml
├── .env.example
└── CLAUDE.md
```

## MCP Tools

The agent exposes 4 custom tools via a local MCP server:

| Tool | Purpose |
|------|---------|
| `extract_taste_profile` | Structure conversation into a formal TasteProfile with scored dimensions |
| `save_user_profile` | Persist an updated profile to disk |
| `load_user_profile` | Load a previously saved profile by user ID |
| `deduplicate_artists` | Fuzzy-match candidate names against known artists and remove duplicates |

## Running Tests

```bash
python -m pytest tests/ -v
```

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the test suite (`python -m pytest tests/ -v`)
5. Submit a pull request

Areas where contributions are welcome:
- Additional storage backends (SQLite, Redis)
- New MCP tools (playlist export, listening history integration)
- Web UI for the discovery session
- Better scoring algorithms (collaborative filtering, embedding-based similarity)

## License

MIT — see [LICENSE](LICENSE).
