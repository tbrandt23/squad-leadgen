"""Batch runner: process every brand in data/seed_brands.csv.

Run from the project root:  python -m scripts.batch_run
Sleeps 2 seconds between brands to stay under API rate limits.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

# Make the src package importable when invoked as `python scripts/batch_run.py`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import config, storage  # noqa: E402
from src.lead_agent import process_lead  # noqa: E402

SLEEP_SECONDS = 2


def _read_seed_brands() -> list[str]:
    path = config.SEED_BRANDS_CSV_PATH
    if not path.exists():
        raise FileNotFoundError(f"Seed brand list not found at {path}")
    with path.open("r", newline="", encoding="utf-8") as f:
        return [row["brand_name"].strip() for row in csv.DictReader(f) if row.get("brand_name")]


def main() -> None:
    brands = _read_seed_brands()
    total = len(brands)
    print(f"Processing {total} brands from {config.SEED_BRANDS_CSV_PATH.name}...")
    storage.init_csv_if_missing()

    successes = 0
    for idx, brand in enumerate(brands, start=1):
        print(f"[{idx}/{total}] {brand}")
        try:
            lead = process_lead(brand)
            storage.append_lead(lead)
            if lead.get("error"):
                print(f"    partial: {lead['error']}")
            else:
                print(f"    score={lead['score']} hook={lead['hook_pain']}")
                successes += 1
        except Exception as exc:
            print(f"    hard failure: {exc}")

        if idx < total:
            time.sleep(SLEEP_SECONDS)

    print(f"Done. {successes}/{total} clean runs. Output: {config.LEADS_CSV_PATH}")


if __name__ == "__main__":
    main()
