from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROFILES_DIR = DATA_DIR / "profiles"

# Ensure dirs exist
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# API — no ANTHROPIC_API_KEY here; the Claude Agent SDK spawns a `claude` CLI
# subprocess that will use your existing Claude subscription auth.

# Budget
MAX_BUDGET_USD = float(os.getenv("MAX_BUDGET_USD", "2.0"))
