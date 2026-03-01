"""AgentDefinition objects for the 3 subagents."""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition

from .prompts import (
    ARTIST_ANALYST_PROMPT,
    RECOMMENDATION_SYNTHESIZER_PROMPT,
    WEB_DISCOVERY_PROMPT,
)

web_discovery_agent = AgentDefinition(
    description=(
        "Web discovery researcher. Use this agent to search the internet for candidate "
        "artists matching the user's taste profile. Pass the full taste profile JSON as context."
    ),
    prompt=WEB_DISCOVERY_PROMPT,
    tools=["WebSearch", "WebFetch"],
    model="sonnet",
)

artist_analyst_agent = AgentDefinition(
    description=(
        "Artist taste analyst. Use this agent to score candidate artists against the "
        "user's taste profile dimensions. Pass both the taste profile and the candidate list."
    ),
    prompt=ARTIST_ANALYST_PROMPT,
    tools=["WebSearch", "WebFetch"],
    model="sonnet",
)

recommendation_synthesizer_agent = AgentDefinition(
    description=(
        "Recommendation writer. Use this agent to write personalized, compelling "
        "recommendations from scored artist data. Pass the scored artists and taste profile."
    ),
    prompt=RECOMMENDATION_SYNTHESIZER_PROMPT,
    tools=["WebSearch", "WebFetch"],
    model="opus",
)

SUBAGENTS = {
    "web-discovery-agent": web_discovery_agent,
    "artist-analyst-agent": artist_analyst_agent,
    "recommendation-synthesizer": recommendation_synthesizer_agent,
}
