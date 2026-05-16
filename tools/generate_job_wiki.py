from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.derived_wiki.job_catalog import list_jobs, resolve_job
from src.derived_wiki.job_wiki_generator import generate_job_wiki
from src.derived_wiki.summary_loader import load_summaries


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    result = run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate derived FFXIV job wiki files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Generate all non-limited jobs")
    group.add_argument("--job", help="Job slug or alias to generate")
    parser.add_argument("--include-limited", action="store_true")
    parser.add_argument("--patch-range", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-root", default="wiki/source_summaries")
    parser.add_argument("--target-root", default="wiki/jobs")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, Any]:
    summaries = load_summaries(Path(args.summary_root))
    jobs = _jobs_from_args(args)
    if not jobs:
        return {
            "status": "error",
            "dry_run": bool(args.dry_run),
            "actions": [],
            "summary": {"generated": 0, "skipped": 0, "errors": 1},
            "error": f"Unknown job: {args.job}",
        }

    actions: list[dict[str, Any]] = []
    for job in jobs:
        generated = generate_job_wiki(
            job,
            summaries,
            Path(args.target_root),
            dry_run=args.dry_run,
            patch_range=args.patch_range,
        )
        if generated is None:
            actions.append(
                {
                    "job": job.slug,
                    "status": "skipped",
                    "reason": "no_matching_entries",
                }
            )
            continue
        actions.append(
            {
                "job": job.slug,
                "status": "generated",
                "path": str(generated.path),
                "written": generated.written,
                "entry_count": len(generated.entries),
            }
        )

    generated_count = sum(1 for action in actions if action["status"] == "generated")
    return {
        "status": "ok" if generated_count or actions else "skipped",
        "dry_run": bool(args.dry_run),
        "summary_root": str(args.summary_root),
        "target_root": str(args.target_root),
        "patch_range": args.patch_range,
        "actions": actions,
        "summary": {
            "generated": generated_count,
            "skipped": sum(1 for action in actions if action["status"] == "skipped"),
            "errors": 0,
        },
    }


def _jobs_from_args(args: argparse.Namespace):
    if args.all:
        return list_jobs(include_limited=args.include_limited)
    job = resolve_job(args.job or "")
    return [job] if job else []


if __name__ == "__main__":
    main()
