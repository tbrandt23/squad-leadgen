"""Orchestrator: chains research -> qualifier -> email_writer.

Single entry point `process_lead(brand_name)` returning a dict shaped for
the leads CSV. Errors at any stage are caught so partial data is preserved.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from src import email_writer, qualifier, research


def _empty_scorecard() -> dict[str, Any]:
    return {
        "creator_volume": 0,
        "attribution_pain": 0,
        "contract_pain": 0,
        "buyer_fit": 0,
        "intent_urgency": 0,
        "total_score": 0,
        "hook_pain": "",
        "hook_evidence": "",
        "summary": "",
    }


def _empty_email() -> dict[str, str]:
    return {"subject": "", "body": ""}


def process_lead(brand_name: str) -> dict[str, Any]:
    """Run the full pipeline for one brand and return a flat lead dict.

    Each stage is wrapped so an upstream failure still yields a row with the
    partial data gathered so far plus an `error` field describing the first
    thing that broke.
    """
    lead: dict[str, Any] = {
        "brand_name": brand_name,
        "date_added": date.today().isoformat(),
        "research_dump": "",
        "error": "",
    }
    scorecard = _empty_scorecard()
    email = _empty_email()

    try:
        lead["research_dump"] = research.research_brand(brand_name)
    except Exception as exc:
        lead["error"] = f"research: {exc}"
        return _flatten(lead, scorecard, email)

    try:
        scorecard = qualifier.qualify(lead["research_dump"])
    except Exception as exc:
        lead["error"] = f"qualifier: {exc}"
        return _flatten(lead, scorecard, email)

    try:
        email = email_writer.write_email(
            brand_name=brand_name,
            hook_pain=scorecard["hook_pain"],
            hook_evidence=scorecard["hook_evidence"],
        )
    except Exception as exc:
        lead["error"] = f"email: {exc}"

    return _flatten(lead, scorecard, email)


def _flatten(
    lead: dict[str, Any],
    scorecard: dict[str, Any],
    email: dict[str, str],
) -> dict[str, Any]:
    return {
        "brand_name": lead["brand_name"],
        "date_added": lead["date_added"],
        "score": scorecard["total_score"],
        "creator_volume": scorecard["creator_volume"],
        "attribution_pain": scorecard["attribution_pain"],
        "contract_pain": scorecard["contract_pain"],
        "buyer_fit": scorecard["buyer_fit"],
        "intent_urgency": scorecard["intent_urgency"],
        "hook_pain": scorecard["hook_pain"],
        "hook_evidence": scorecard["hook_evidence"],
        "summary": scorecard["summary"],
        "research_dump": lead["research_dump"],
        "email_subject": email["subject"],
        "email_body": email["body"],
        "error": lead.get("error", ""),
    }


if __name__ == "__main__":
    sample_lead = {"brand_name": "Sample Co", "date_added": "2025-01-01", "research_dump": "x"}
    print(
        "flatten shape:",
        list(_flatten(sample_lead, _empty_scorecard(), _empty_email()).keys()),
    )
    print("(Live API chain skipped.)")
