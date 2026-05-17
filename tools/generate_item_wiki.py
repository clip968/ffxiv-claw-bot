from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.derived_wiki.item_wiki_generator import generate_item_wiki


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate derived wiki pages for guide.ff14.co.kr items.")
    parser.add_argument("--db-path", type=Path, default=ROOT / "db" / "ffxiv.sqlite")
    parser.add_argument("--wiki-root", type=Path, default=ROOT / "wiki")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    with sqlite3.connect(args.db_path) as conn:
        result = generate_item_wiki(
            conn,
            args.wiki_root,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
