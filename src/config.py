"""Configuration loader for the Squad Lead Gen Agent.

Loads API keys and constants from a `.env` file at the project root.
All modules should import keys from here rather than reading env vars directly.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
PERPLEXITY_API_KEY: str | None = os.getenv("PERPLEXITY_API_KEY")

ANTHROPIC_MODEL = "claude-sonnet-4-6"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

PERPLEXITY_TIMEOUT_SECONDS = 45
LEADS_CSV_PATH = PROJECT_ROOT / "data" / "leads.csv"
SEED_BRANDS_CSV_PATH = PROJECT_ROOT / "data" / "seed_brands.csv"


def require_keys() -> None:
    """Raise if either API key is missing. Call before live API usage."""
    missing = [
        name
        for name, value in (
            ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
            ("PERPLEXITY_API_KEY", PERPLEXITY_API_KEY),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your keys."
        )


if __name__ == "__main__":
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"ANTHROPIC_API_KEY present: {bool(ANTHROPIC_API_KEY)}")
    print(f"PERPLEXITY_API_KEY present: {bool(PERPLEXITY_API_KEY)}")
    print(f"ANTHROPIC_MODEL: {ANTHROPIC_MODEL}")
    print(f"PERPLEXITY_MODEL: {PERPLEXITY_MODEL}")
