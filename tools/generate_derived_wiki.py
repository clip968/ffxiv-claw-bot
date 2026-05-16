from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import generate_job_wiki


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
        description="Generate derived wiki documents. v0.6 supports kind: jobs."
    )
    parser.add_argument(
        "--kind",
        required=True,
        help="Derived wiki kind to generate. Supported in v0.6: jobs.",
    )
    parser.add_argument("--job", default=None)
    parser.add_argument("--patch-range", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--summary-root", default="wiki/source_summaries")
    parser.add_argument("--target-root", default="wiki/jobs")
    parser.add_argument("--include-limited", action="store_true")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    if args.kind not in SUPPORTED_KINDS:
        raise ValueError(_unsupported_kind_message(args.kind))
    result = _run_jobs(args)
    result["kind"] = "jobs"
    return result


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
