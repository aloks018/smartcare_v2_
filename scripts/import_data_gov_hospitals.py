import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


API_URL = "https://api.data.gov.in/resource/national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month"


def fetch_records(api_key: str, state: str, limit: int) -> list[dict[str, str]]:
    params = urlencode(
        {
            "api-key": api_key,
            "format": "json",
            "limit": limit,
            "filters[state]": state,
        }
    )
    with urlopen(f"{API_URL}?{params}", timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("records", [])


def read_csv(path: Path, state: str, limit: int) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    state_lower = state.lower()
    filtered = [row for row in rows if state_lower in " ".join(row.values()).lower()]
    return filtered[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Uttar Pradesh hospitals from official data.gov.in/NHD data.")
    parser.add_argument("--api-key", default="579b464db66ec23bdd000001", help="data.gov.in API key")
    parser.add_argument("--state", default="Uttar Pradesh")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--csv", type=Path, help="Optional downloaded National Hospital Directory CSV")
    parser.add_argument("--out", type=Path, default=Path("data/up_hospitals_import.json"))
    args = parser.parse_args()

    records = read_csv(args.csv, args.state, args.limit) if args.csv else fetch_records(args.api_key, args.state, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()

