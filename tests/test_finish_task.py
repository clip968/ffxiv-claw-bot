from __future__ import annotations

import sys
import unittest

from scripts.finish_task import build_finish_commands


class FinishTaskTests(unittest.TestCase):
    def test_default_commands_run_in_required_order(self) -> None:
        commands = build_finish_commands(
            skip_docs_check=False,
            skip_tests=False,
            skip_notion_dry_run=False,
        )

        self.assertEqual(
            [command.label for command in commands],
            [
                "unittest",
                "docs freshness check",
                "Notion handoff dry-run",
                "git status",
                "git diff stat",
            ],
        )
        self.assertEqual(
            commands[0].argv,
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        )
        self.assertEqual(
            commands[1].argv,
            [sys.executable, "scripts/check_docs_freshness.py", "--all"],
        )
        self.assertEqual(
            commands[2].argv,
            [sys.executable, "scripts/sync_notion_handoff.py", "--dry-run"],
        )

    def test_skip_options_omit_requested_commands(self) -> None:
        commands = build_finish_commands(
            skip_docs_check=True,
            skip_tests=True,
            skip_notion_dry_run=True,
        )

        self.assertEqual(
            [command.label for command in commands],
            [
                "git status",
                "git diff stat",
            ],
        )


if __name__ == "__main__":
    unittest.main()
