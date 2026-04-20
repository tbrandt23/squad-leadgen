"""CSV storage for qualified leads.

Reads and writes `data/leads.csv` using the stdlib csv module so multi-line
fields (research dump, email body) are escaped correctly.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src import config

COLUMNS = [
    "brand_name",
    "date_added",
    "score",
    "creator_volume",
    "attribution_pain",
    "contract_pain",
    "buyer_fit",
    "intent_urgency",
    "hook_pain",
    "hook_evidence",
    "summary",
    "research_dump",
    "email_subject",
    "email_body",
]


def _csv_path() -> Path:
    path = config.LEADS_CSV_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_csv_if_missing() -> None:
    """Create the leads CSV with header row if it does not exist yet."""
    path = _csv_path()
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()


def append_lead(lead: dict[str, Any]) -> None:
    """Append a single lead row. Missing columns are written as empty strings."""
    init_csv_if_missing()
    row = {col: ("" if lead.get(col) is None else str(lead.get(col))) for col in COLUMNS}
    with _csv_path().open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writerow(row)


def load_leads() -> list[dict[str, str]]:
    """Return all leads as a list of dicts. Empty list if the file is missing."""
    path = _csv_path()
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    print("COLUMNS:", COLUMNS)
    print(f"CSV path: {config.LEADS_CSV_PATH}")
    print("Existing leads count:", len(load_leads()))
    print("(No writes performed in test block.)")
