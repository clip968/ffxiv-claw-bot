from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.guide_ff14.category_map import parse_category_map
from src.guide_ff14.crawler import crawl_item_pilot
from src.guide_ff14.fetcher import GuideFetcher


DB_ROOT_URL = "https://guide.ff14.co.kr/lodestone/db/item"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl the guide.ff14.co.kr official DB pilot scope.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    category_map = subparsers.add_parser("category-map")
    category_map.add_argument("--dry-run", action="store_true", required=True)
    category_map.add_argument("--delay-seconds", type=float, default=1.0)
    category_map.add_argument("--timeout-seconds", type=float, default=20.0)

    item_pilot = subparsers.add_parser("item-pilot")
    item_pilot.add_argument("--category-url", required=True)
    item_pilot.add_argument("--limit", type=int, default=30)
    mode = item_pilot.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    item_pilot.add_argument("--db-path", type=Path, default=ROOT / "db" / "ffxiv.sqlite")
    item_pilot.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw" / "guide_ff14")
    item_pilot.add_argument("--delay-seconds", type=float, default=1.0)
    item_pilot.add_argument("--timeout-seconds", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None, *, fetcher: Any | None = None) -> None:
    args = build_parser().parse_args(argv)
    active_fetcher = fetcher or GuideFetcher(
        delay_seconds=args.delay_seconds,
        timeout_seconds=args.timeout_seconds,
    )
    result = run(args, fetcher=active_fetcher)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def run(args: argparse.Namespace, *, fetcher: Any) -> dict[str, Any]:
    if args.command == "category-map":
        return run_category_map(fetcher=fetcher)
    if args.command == "item-pilot":
        return crawl_item_pilot(
            category_url=args.category_url,
            limit=args.limit,
            apply=args.apply,
            fetcher=fetcher,
            db_path=args.db_path,
            raw_dir=args.raw_dir,
        )
    raise ValueError(f"unknown command: {args.command}")


def run_category_map(*, fetcher: Any) -> dict[str, Any]:
    fetch = fetcher.fetch(DB_ROOT_URL)
    if fetch.status != "ok" or not fetch.body:
        return {
            "status": "error",
            "root_url": DB_ROOT_URL,
            "categories": [],
            "errors": [{"url": DB_ROOT_URL, "error": fetch.error or "empty response body"}],
            "next_action": "Check guide.ff14.co.kr access before running item-pilot.",
        }
    categories = parse_category_map(fetch.body)
    return {
        "status": "planned",
        "root_url": DB_ROOT_URL,
        "categories": [
            {
                "id": category.id,
                "db_type": category.db_type,
                "label": category.label,
                "url": category.url,
                "category2": category.category2,
                "category3": category.category3,
                "filters": category.filters,
            }
            for category in categories
        ],
        "errors": [],
        "next_action": "Review categories, then run item-pilot with a bounded --limit.",
    }


if __name__ == "__main__":
    main()
