"""Claude qualification module.

Exposes `qualify(research_dump)` which scores a brand on the five-signal
rubric from PRD section 9.2 and returns a structured scorecard dict.
"""

from __future__ import annotations

import json
import re
from typing import Any

from anthropic import Anthropic

from src import config

QUALIFY_PROMPT_TEMPLATE = """You are a lead qualification analyst for Squad, a CRM built for DTC
brands managing UGC creator partnerships.

Squad solves two core pains:
  ATTRIBUTION: brands can't tell which creator actually drove sales
  CONTRACTS/IP: brands lose track of contracts, renewal dates, and
  content usage rights

Score the brand below on five signals, 0-3 each, using this rubric:

CREATOR VOLUME
  0: no visible creator partnerships
  1: 1-5 creators in last 90 days
  2: 6-20 creators
  3: 20+ creators

ATTRIBUTION PAIN
  0: no creator program, or clean per-creator codes
  1: generic codes, one creator at a time
  2: multiple creators with non-unique tracking
  3: heavy multi-creator campaigns with obvious attribution chaos

CONTRACT/IP PAIN
  0: no content reuse visible
  1: occasional creator repost
  2: consistent UGC repurposing in marketing
  3: creator UGC in paid ads and product pages, heavy rights complexity

BUYER FIT
  0: too small (<$1M) or too big (>$200M)
  1: edge of ideal range
  2: solid fit ($5M-$50M)
  3: bullseye ($10M-$30M, Series A/B)

INTENT/URGENCY
  0: no active signals
  1: steady creator program running
  2: recent hire or ops growth
  3: active creator job listing, recent funding, public pain signals

Hook selection: whichever of attribution or contracts scored higher wins.
Tie goes to attribution.

Research:
{research_dump}

Return JSON ONLY, no preamble:
{{
  "creator_volume": <0-3>,
  "attribution_pain": <0-3>,
  "contract_pain": <0-3>,
  "buyer_fit": <0-3>,
  "intent_urgency": <0-3>,
  "total_score": <int 1-10, normalized>,
  "hook_pain": "attribution" or "contracts",
  "hook_evidence": "specific fact from research supporting the hook",
  "summary": "one sentence on why they fit"
}}"""

SIGNAL_KEYS = (
    "creator_volume",
    "attribution_pain",
    "contract_pain",
    "buyer_fit",
    "intent_urgency",
)


def _extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {text[:200]}")
    return json.loads(match.group(0))


def _enforce_invariants(data: dict[str, Any]) -> dict[str, Any]:
    """Recompute total and resolve hook locally so the UI never shows bad math."""
    for key in SIGNAL_KEYS:
        data[key] = max(0, min(3, int(data.get(key, 0))))

    raw_total = sum(data[key] for key in SIGNAL_KEYS)
    data["total_score"] = max(1, round((raw_total / 15) * 10))

    attribution = data["attribution_pain"]
    contracts = data["contract_pain"]
    data["hook_pain"] = "contracts" if contracts > attribution else "attribution"
    return data


def qualify(research_dump: str) -> dict[str, Any]:
    """Return a scorecard dict for the given research dump."""
    config.require_keys()
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = QUALIFY_PROMPT_TEMPLATE.format(research_dump=research_dump)
    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = "".join(block.text for block in message.content if block.type == "text")
    return _enforce_invariants(_extract_json(raw_text))


if __name__ == "__main__":
    sample = {
        "creator_volume": 3,
        "attribution_pain": 2,
        "contract_pain": 3,
        "buyer_fit": 2,
        "intent_urgency": 1,
        "total_score": 99,
        "hook_pain": "attribution",
        "hook_evidence": "sample",
        "summary": "sample",
    }
    print("invariants check:", _enforce_invariants(dict(sample)))
    print("extract check:", _extract_json('garbage {"a": 1, "b": 2} trailing'))
    print("(Live API call skipped.)")
