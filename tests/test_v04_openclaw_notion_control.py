from __future__ import annotations

import importlib
import unittest
from typing import Any, Callable


def require_callable(test: unittest.TestCase, module_name: str, function_name: str) -> Callable[..., Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            test.fail(f"Expected {module_name}.{function_name} for v04 OpenClaw Notion control")
        raise

    function = getattr(module, function_name, None)
    if not callable(function):
        test.fail(f"Expected callable {module_name}.{function_name} for v04 OpenClaw Notion control")
    return function


class V04OpenClawNotionControlRedTests(unittest.TestCase):
    def test_cli_result_maps_to_notion_status_without_file_payload(self) -> None:
        build_notion_update = require_callable(
            self,
            "tools.openclaw_notion_control",
            "build_notion_update",
        )

        result = {
            "status": "ok",
            "title": "Black Mage 7.5 Guide",
            "category": "job_guides",
            "source_id": "local_001",
            "local_source_path": "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
            "wiki_path": "wiki/jobs/black_mage/7_5.md",
            "graph_status": "built",
            "body": "# Black Mage guide body must not be sent to Notion",
            "attachments": [{"name": "guide.md", "content": "must not be uploaded"}],
        }

        update = build_notion_update(result)

        self.assertEqual(update["Status"], "Graph Built")
        self.assertEqual(update["Title"], "Black Mage 7.5 Guide")
        self.assertEqual(update["Category"], "job_guides")
        self.assertEqual(update["Source ID"], "local_001")
        self.assertEqual(
            update["Local Source Path"],
            "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
        )
        self.assertEqual(update["Wiki Path"], "wiki/jobs/black_mage/7_5.md")
        self.assertEqual(update["Graph Status"], "Built")
        self.assertNotIn("body", update)
        self.assertNotIn("attachments", update)


if __name__ == "__main__":
    unittest.main()
