from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class FinishCommand:
    label: str
    argv: list[str]


def build_finish_commands(
    *,
    skip_docs_check: bool,
    skip_tests: bool,
    skip_notion_dry_run: bool,
) -> list[FinishCommand]:
    commands: list[FinishCommand] = []

    if not skip_tests:
        commands.append(
            FinishCommand(
                "unittest",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-p",
                    "test_*.py",
                ],
            )
        )

    if not skip_docs_check:
        commands.append(
            FinishCommand(
                "docs freshness check",
                [sys.executable, "scripts/check_docs_freshness.py", "--all"],
            )
        )

    if not skip_notion_dry_run:
        commands.append(
            FinishCommand(
                "Notion handoff dry-run",
                [sys.executable, "scripts/sync_notion_handoff.py", "--dry-run"],
            )
        )

    commands.extend(
        [
            FinishCommand("git status", ["git", "status", "--short"]),
            FinishCommand("git diff stat", ["git", "diff", "--stat"]),
        ]
    )
    return commands


def run_command(command: FinishCommand) -> int:
    print(f"\n==> {command.label}")
    print("$ " + " ".join(command.argv))
    completed = subprocess.run(command.argv)
    if completed.returncode != 0:
        print(f"FAILED: {command.label} exited with {completed.returncode}")
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run task completion checks.")
    parser.add_argument("--skip-docs-check", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-notion-dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.skip_tests:
        print("SKIP: unittest")
    if args.skip_docs_check:
        print("SKIP: docs freshness check")
    if args.skip_notion_dry_run:
        print("SKIP: Notion handoff dry-run")

    failures: list[str] = []
    for command in build_finish_commands(
        skip_docs_check=args.skip_docs_check,
        skip_tests=args.skip_tests,
        skip_notion_dry_run=args.skip_notion_dry_run,
    ):
        if run_command(command) != 0:
            failures.append(command.label)

    if failures:
        print("\nfinish_task failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nfinish_task ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
