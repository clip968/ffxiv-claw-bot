from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.domain_graph.report import generate_graph_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate graph/GRAPH_REPORT.md.")
    parser.add_argument("--db-path", type=Path, default=ROOT / "db" / "ffxiv.sqlite")
    parser.add_argument("--graph-dir", type=Path, default=ROOT / "graph")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    with sqlite3.connect(args.db_path) as conn:
        result = generate_graph_report(conn, args.graph_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
