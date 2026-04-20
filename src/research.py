"""Perplexity research module.

Exposes `research_brand(brand_name)` which returns a structured text dump
covering the six research areas defined in PRD section 9.1.
"""

from __future__ import annotations

from openai import OpenAI

from src import config

RESEARCH_PROMPT_TEMPLATE = """Research {brand_name}, a DTC brand that works with UGC content creators.

Find and report on these six areas. Be specific. Cite sources.
Skip filler and intros.

1. UGC platforms: which of TikTok, Instagram Reels, YouTube Shorts they
   actively post creator-made content on.

2. Creator volume estimate: roughly how many creators have partnered
   with them in the last 90 days. Give a range (1-5, 6-20, 20+) with
   reasoning.

3. Attribution signals: do they appear to use unique discount codes per
   creator, generic site-wide codes, or no codes at all? Are multiple
   creators running simultaneous campaigns?

4. Contract and IP signals: do they repost creator content to their own
   feed? Does creator UGC appear in their paid ads or on their product
   pages? Any evidence of content rights complexity?

5. Buyer fit signals: estimated company size (employees, revenue tier,
   funding stage if known).

6. Urgency signals: any active job listings for creator ops, influencer
   management, or partnerships roles. Recent funding rounds. Public
   complaints from founders or marketers about creator operations.

Return structured sections with clear headers."""


def _client() -> OpenAI:
    config.require_keys()
    return OpenAI(
        api_key=config.PERPLEXITY_API_KEY,
        base_url=config.PERPLEXITY_BASE_URL,
        timeout=config.PERPLEXITY_TIMEOUT_SECONDS,
    )


def _call_perplexity(prompt: str) -> str:
    client = _client()
    response = client.chat.completions.create(
        model=config.PERPLEXITY_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def research_brand(brand_name: str) -> str:
    """Return a structured research dump for `brand_name`.

    Uses Perplexity's sonar-pro model. Retries once on timeout or transient
    network errors before giving up and re-raising.
    """
    prompt = RESEARCH_PROMPT_TEMPLATE.format(brand_name=brand_name)
    try:
        return _call_perplexity(prompt)
    except Exception as first_error:
        try:
            return _call_perplexity(prompt)
        except Exception as second_error:
            raise RuntimeError(
                f"Perplexity research failed twice for {brand_name!r}: "
                f"{first_error} / {second_error}"
            ) from second_error


if __name__ == "__main__":
    sample_brand = "Alo Yoga"
    print(f"Sample prompt for {sample_brand}:")
    print("-" * 60)
    print(RESEARCH_PROMPT_TEMPLATE.format(brand_name=sample_brand))
    print("-" * 60)
    print("(Live API call skipped. Run with keys set to invoke research_brand.)")
