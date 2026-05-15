from __future__ import annotations

import importlib
import unittest
from typing import Any, Callable


def require_callable(test: unittest.TestCase, module_name: str, function_name: str) -> Callable[..., Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            test.fail(f"Expected {module_name}.{function_name} for v04 status notification")
        raise

    function = getattr(module, function_name, None)
    if not callable(function):
        test.fail(f"Expected callable {module_name}.{function_name} for v04 status notification")
    return function


class V04StatusNotificationRedTests(unittest.TestCase):
    def test_partial_result_formats_discord_summary_and_notion_status_without_drive_url(self) -> None:
        format_discord_summary = require_callable(
            self,
            "tools.status_notification",
            "format_discord_summary",
        )
        build_notion_status_update = require_callable(
            self,
            "tools.status_notification",
            "build_notion_status_update",
        )

        result = {
            "status": "partial",
            "title": "Black Mage 7.5 Guide",
            "category": "job_guides",
            "source_id": "local_001",
            "local_source_path": "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
            "wiki_path": "wiki/jobs/black_mage/7_5.md",
            "graph_status": "failed",
            "last_error": "build_graph failed",
            "next_action": "rerun local rebuild",
        }

        message = format_discord_summary(result)
        notion_update = build_notion_status_update(result)

        self.assertIn("Black Mage 7.5 Guide", message)
        self.assertIn("job_guides", message)
        self.assertIn("/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md", message)
        self.assertIn("wiki/jobs/black_mage/7_5.md", message)
        self.assertIn("build_graph failed", message)
        self.assertNotIn("Drive", message)
        self.assertEqual(notion_update["Status"], "Partial")
        self.assertEqual(notion_update["Graph Status"], "Failed")
        self.assertEqual(notion_update["Last Error"], "build_graph failed")
        self.assertEqual(notion_update["Next Action"], "rerun local rebuild")


if __name__ == "__main__":
    unittest.main()
