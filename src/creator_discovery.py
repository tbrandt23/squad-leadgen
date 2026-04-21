"""Creator-first discovery: handle -> list of brand names.

Asks Perplexity for the DTC brands a given creator has posted sponsored or
affiliate content for, then returns a clean de-duplicated list of brand
names ready to feed through the existing lead agent pipeline.
"""

from __future__ import annotations

import re

from openai import OpenAI

from src import config

DISCOVERY_PROMPT = """List DTC brand partnerships for the content creator {handle}.

Focus on the last 12 months. Include paid partnerships, gifted placements,
and affiliate / discount-code deals across TikTok, Instagram Reels, and
YouTube Shorts.

Return ONLY a simple list of brand names, one per line, no numbering,
no extra commentary, no platform tags. Example format:

Alo Yoga
Ghost Energy
Graza

Stop after the list."""


def _client() -> OpenAI:
    config.require_keys()
    return OpenAI(
        api_key=config.PERPLEXITY_API_KEY,
        base_url=config.PERPLEXITY_BASE_URL,
        timeout=config.PERPLEXITY_TIMEOUT_SECONDS,
    )


def _parse_brands(text: str) -> list[str]:
    brands: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().lstrip("-*0123456789. ").strip()
        if not line or len(line) > 80:
            continue
        if any(stop in line.lower() for stop in ("here are", "partnership", "brand:", "based on")):
            continue
        line = re.sub(r"\s*\([^)]*\)\s*$", "", line).strip()
        key = line.lower()
        if key and key not in seen:
            seen.add(key)
            brands.append(line)
    return brands


def find_brands_for_creator(handle: str, limit: int = 5) -> list[str]:
    """Return up to `limit` brand names associated with the creator handle."""
    prompt = DISCOVERY_PROMPT.format(handle=handle)
    client = _client()
    response = client.chat.completions.create(
        model=config.PERPLEXITY_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content or ""
    return _parse_brands(raw)[:limit]


if __name__ == "__main__":
    sample = """Here are the brands:
    Alo Yoga
    1. Ghost Energy
    - Graza
    (not a brand line)
    Alo Yoga
    Based on publicly available posts"""
    print("parse test:", _parse_brands(sample))
    print("(Live API call skipped.)")
