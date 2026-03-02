#!/usr/bin/env python3
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests

BASE_URL = "https://gamma-api.polymarket.com/markets"
CATEGORY_TAGS = {
    "world": 366,   # world-affairs
    "tech": 1401,   # tech
}
LIMIT_PER_CATEGORY = 20

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _parse_json_field(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    return []


def fetch_top_markets(tag_id: int, limit: int) -> List[dict]:
    params = {
        "tag_id": tag_id,
        "limit": limit,
        "active": "true",
        "closed": "false",
        "order": "volume24hr",
        "ascending": "false",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def flatten_market(category: str, market: dict, captured_at: str) -> Dict:
    outcomes = _parse_json_field(market.get("outcomes"))
    prices = _parse_json_field(market.get("outcomePrices"))

    result_pct = {}
    for o, p in zip(outcomes, prices):
        try:
            result_pct[o] = round(float(p) * 100, 4)
        except Exception:
            result_pct[o] = p

    return {
        "captured_at_utc": captured_at,
        "category": category,
        "market_id": str(market.get("id", "")),
        "slug": market.get("slug", ""),
        "question": market.get("question", ""),
        "volume24hr_usd": float(market.get("volume24hr") or 0),
        "volume_total_usd": float(market.get("volumeNum") or market.get("volume") or 0),
        "end_date": market.get("endDateIso") or market.get("endDate") or "",
        "options": outcomes,
        "results_pct": result_pct,
    }


def append_history(rows: List[Dict], path: Path):
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "captured_at_utc",
                "category",
                "market_id",
                "slug",
                "question",
                "volume24hr_usd",
                "volume_total_usd",
                "end_date",
                "options_json",
                "results_pct_json",
            ],
        )
        if not file_exists:
            writer.writeheader()
        for row in rows:
            out = row.copy()
            out["options_json"] = json.dumps(row["options"], ensure_ascii=False)
            out["results_pct_json"] = json.dumps(row["results_pct"], ensure_ascii=False)
            out.pop("options", None)
            out.pop("results_pct", None)
            writer.writerow(out)


def update_wide_snapshot(rows: List[Dict], path: Path, captured_at: str):
    ts_key = captured_at.replace(":", "-")

    existing = {}
    headers = ["category", "market_id", "slug", "question", "end_date"]

    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or headers
            for r in reader:
                existing[(r["category"], r["market_id"])] = r

    new_headers = set(headers)

    for row in rows:
        key = (row["category"], row["market_id"])
        if key not in existing:
            existing[key] = {
                "category": row["category"],
                "market_id": row["market_id"],
                "slug": row["slug"],
                "question": row["question"],
                "end_date": row["end_date"],
            }
        else:
            existing[key]["slug"] = row["slug"]
            existing[key]["question"] = row["question"]
            existing[key]["end_date"] = row["end_date"]

        vol_col = f"{ts_key}__volume24hr_usd"
        existing[key][vol_col] = f"{row['volume24hr_usd']:.6f}"
        new_headers.add(vol_col)

        for opt, pct in row["results_pct"].items():
            safe_opt = str(opt).strip().replace(" ", "_")
            col = f"{ts_key}__{safe_opt}_pct"
            existing[key][col] = str(pct)
            new_headers.add(col)

    base = ["category", "market_id", "slug", "question", "end_date"]
    extra = sorted([h for h in new_headers if h not in base])
    ordered_headers = base + extra

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_headers)
        writer.writeheader()
        for row in sorted(existing.values(), key=lambda r: (r["category"], r["question"])):
            writer.writerow(row)


def main():
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_rows = []

    for category, tag_id in CATEGORY_TAGS.items():
        markets = fetch_top_markets(tag_id=tag_id, limit=LIMIT_PER_CATEGORY)
        for m in markets:
            all_rows.append(flatten_market(category, m, captured_at))

    append_history(all_rows, DATA_DIR / "snapshots_long.csv")
    update_wide_snapshot(all_rows, DATA_DIR / "snapshots_wide.csv", captured_at)

    latest = {
        "captured_at_utc": captured_at,
        "count": len(all_rows),
        "rows": all_rows,
    }
    (DATA_DIR / "latest.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Captured {len(all_rows)} rows at {captured_at}")
    print(f"Wrote: {DATA_DIR / 'snapshots_long.csv'}")
    print(f"Wrote: {DATA_DIR / 'snapshots_wide.csv'}")
    print(f"Wrote: {DATA_DIR / 'latest.json'}")


if __name__ == "__main__":
    main()
