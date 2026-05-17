from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sqlite3

from tools import generate_job_wiki
from src.domain_graph.derived_wiki import generate_derived_wiki


SUPPORTED_KINDS = {"jobs"}
KNOWN_FUTURE_KINDS = {"raids", "items", "systems"}


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    try:
        result = run(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate derived wiki documents."
    )
    parser.add_argument(
        "--kind",
        help="Legacy v0.6 derived wiki kind to generate. Supported: jobs.",
    )
    parser.add_argument("--job", default=None)
    parser.add_argument("--patch-range", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-root", default="wiki/source_summaries")
    parser.add_argument("--target-root", default="wiki/jobs")
    parser.add_argument("--include-limited", action="store_true")
    parser.add_argument("--db-path", type=Path, default=ROOT / "db" / "ffxiv.sqlite")
    parser.add_argument("--wiki-root", type=Path, default=ROOT / "wiki")
    parser.add_argument("--graph-dir", type=Path, default=ROOT / "graph")
    parser.add_argument("--types", default="jobs,patches,skills")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    if args.kind:
        if args.kind not in SUPPORTED_KINDS:
            raise ValueError(_unsupported_kind_message(args.kind))
        result = _run_jobs(args)
        result["kind"] = "jobs"
        return result
    return _run_v08(args)


def _run_v08(args: argparse.Namespace) -> dict:
    selected_types = tuple(
        part.strip() for part in args.types.split(",") if part.strip()
    )
    unsupported = sorted(set(selected_types) - {"jobs", "patches", "skills"})
    if unsupported:
        raise ValueError(_unsupported_kind_message(args.kind))
    with sqlite3.connect(args.db_path) as conn:
        return generate_derived_wiki(
            conn,
            args.wiki_root,
            args.graph_dir,
            types=selected_types or ("jobs", "patches", "skills"),
            dry_run=args.dry_run,
            verbose=args.verbose,
        )


def _run_jobs(args: argparse.Namespace) -> dict:
    job_args = argparse.Namespace(
        all=args.job is None,
        job=args.job,
        include_limited=args.include_limited,
        patch_range=args.patch_range,
        dry_run=args.dry_run,
        summary_root=args.summary_root,
        target_root=args.target_root,
    )
    return generate_job_wiki.run(job_args)


def _exit_unsupported_kind(kind: str) -> None:
    print(_unsupported_kind_message(kind), file=sys.stderr)
    raise SystemExit(2)


def _unsupported_kind_message(kind: str) -> str:
    if kind in KNOWN_FUTURE_KINDS:
        return f"Derived wiki kind '{kind}' is not supported in v0.6."
    return f"Unknown derived wiki kind '{kind}'. Supported in v0.6: jobs."


if __name__ == "__main__":
    main()
