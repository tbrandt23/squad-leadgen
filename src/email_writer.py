"""Claude email writer module.

Exposes `write_email(brand_name, hook_pain, hook_evidence)` which returns
a dict with `subject` and `body` keys, obeying the hard rules from PRD 9.3.
"""

from __future__ import annotations

import re

from anthropic import Anthropic

from src import config

EMAIL_PROMPT_TEMPLATE = """Write a cold email from the founder of Squad to a marketing ops or
growth lead at {brand_name}.

Hard rules:
  Max 80 words in the body
  No em dashes, no semicolons
  No "I hope this finds you well," "quick question," "circling back"
  No fluff words: streamline, leverage, unlock, revolutionize, solution
  Sound like a real human founder who knows the creator ops space
  Reference the specific hook evidence naturally, not robotically
  One CTA: "Worth a 15-min look next week?"

Hook pain: {hook_pain}
Hook evidence: {hook_evidence}

Structure:
  Line 1: reference something real about their creator program
  Line 2: name what's probably hard about it (attribution OR contracts),
          without calling it a "pain point"
  Line 3: one concrete sentence on what Squad does for that
  Line 4: CTA

Subject line: 6 words max, specific, no clickbait.

Return exactly this format:
Subject: <subject line>
Body: <email body>"""

BANNED_CHARS = ("\u2014", ";")
BANNED_PHRASES = (
    "i hope this finds you well",
    "quick question",
    "circling back",
)
BANNED_WORDS = ("streamline", "leverage", "unlock", "revolutionize", "solution")


def _parse_output(text: str) -> dict[str, str]:
    subject_match = re.search(r"Subject:\s*(.+)", text)
    body_match = re.search(r"Body:\s*(.+)", text, re.DOTALL)
    if not subject_match or not body_match:
        raise ValueError(f"Could not parse Subject/Body from output: {text[:200]}")
    return {
        "subject": subject_match.group(1).strip(),
        "body": body_match.group(1).strip(),
    }


def _violations(email: dict[str, str]) -> list[str]:
    body = email["body"]
    body_lower = body.lower()
    problems: list[str] = []

    for ch in BANNED_CHARS:
        if ch in body:
            problems.append(f"contains banned character {ch!r}")
    for phrase in BANNED_PHRASES:
        if phrase in body_lower:
            problems.append(f"contains banned phrase {phrase!r}")
    for word in BANNED_WORDS:
        if re.search(rf"\b{word}\b", body_lower):
            problems.append(f"contains banned word {word!r}")
    if len(body.split()) > 80:
        problems.append(f"body exceeds 80 words ({len(body.split())})")
    if len(email["subject"].split()) > 6:
        problems.append(f"subject exceeds 6 words ({len(email['subject'].split())})")
    return problems


def _generate(client: Anthropic, prompt: str, correction: str = "") -> dict[str, str]:
    user_content = prompt if not correction else f"{prompt}\n\n{correction}"
    message = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": user_content}],
    )
    raw = "".join(b.text for b in message.content if b.type == "text")
    return _parse_output(raw)


def write_email(brand_name: str, hook_pain: str, hook_evidence: str) -> dict[str, str]:
    """Return {'subject': ..., 'body': ...}. Retries once on rule violation."""
    config.require_keys()
    client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = EMAIL_PROMPT_TEMPLATE.format(
        brand_name=brand_name,
        hook_pain=hook_pain,
        hook_evidence=hook_evidence,
    )

    email = _generate(client, prompt)
    problems = _violations(email)
    if not problems:
        return email

    correction = (
        "Your previous draft broke these rules: "
        + "; ".join(problems)
        + ". Rewrite now, fixing every violation. Return Subject: / Body: format."
    )
    return _generate(client, prompt, correction)


if __name__ == "__main__":
    fake = {
        "subject": "Your creator program attribution",
        "body": (
            "Noticed you ran 12 creator codes last month on TikTok. "
            "Figuring out which creator actually drove each sale gets messy fast "
            "once codes overlap. Squad ties each sale to a specific creator and "
            "tracks their contract and rights in one place. "
            "Worth a 15-min look next week?"
        ),
    }
    print("violations on clean sample:", _violations(fake))
    dirty = {
        "subject": "streamline your creator ops today right now",
        "body": "Quick question — we leverage attribution; unlock growth.",
    }
    print("violations on dirty sample:", _violations(dirty))
    print("(Live API call skipped.)")
