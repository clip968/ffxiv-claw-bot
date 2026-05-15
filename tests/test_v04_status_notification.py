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


    def test_ok_with_graph_built_promotes_status_and_excludes_body_attachments_drive(self) -> None:
        build_notion_status_update = require_callable(
            self,
            "tools.status_notification",
            "build_notion_status_update",
        )

        result = {
            "status": "ok",
            "graph_status": "built",
            "title": "discord_agent_smoke_test",
            "category": "personal_notes",
            "source_id": "local_862b7d9ed7d2",
            "local_source_path": "/mnt/d/ffixiv-bot-storage/sources/personal_notes/discord_agent_smoke_test.md",
            "wiki_path": "wiki/source_summaries/local_862b7d9ed7d2.md",
            # These fields must never leak into the Notion payload
            "body": "Discord에서 OpenClaw ffxiv agent가 tools/ingest_local.py를 호출할 수 있는지 확인하는 테스트 문서.",
            "attachments": ["https://drive.google.com/file/d/fake1", "https://drive.google.com/file/d/fake2"],
            "drive_url": "https://drive.google.com/drive/folders/fake",
        }

        payload = build_notion_status_update(result)

        # --- Promotion checks ---
        self.assertEqual(payload["Status"], "Graph Built")
        self.assertEqual(payload["Graph Status"], "Built")

        # --- Metadata fields present ---
        self.assertEqual(payload["Title"], "discord_agent_smoke_test")
        self.assertEqual(payload["Category"], "personal_notes")
        self.assertEqual(payload["Source ID"], "local_862b7d9ed7d2")
        self.assertEqual(
            payload["Local Source Path"],
            "/mnt/d/ffixiv-bot-storage/sources/personal_notes/discord_agent_smoke_test.md",
        )
        self.assertEqual(payload["Wiki Path"], "wiki/source_summaries/local_862b7d9ed7d2.md")

        # --- Exclusion checks ---
        self.assertNotIn("body", payload)
        self.assertNotIn("attachments", payload)
        self.assertNotIn("drive_url", payload)
        # Any key that looks like Drive content should be absent
        for key in payload:
            self.assertNotIn("drive", key.lower())

    def test_ok_without_graph_built_stays_indexed(self) -> None:
        build_notion_status_update = require_callable(
            self,
            "tools.status_notification",
            "build_notion_status_update",
        )

        result = {
            "status": "ok",
            "graph_status": "pending",
            "title": "Test Note",
            "category": "personal_notes",
            "source_id": "local_002",
        }

        payload = build_notion_status_update(result)
        self.assertEqual(payload["Status"], "Indexed")
        self.assertEqual(payload["Graph Status"], "Pending")

    def test_ok_missing_graph_status_defaults_indexed(self) -> None:
        build_notion_status_update = require_callable(
            self,
            "tools.status_notification",
            "build_notion_status_update",
        )

        result = {
            "status": "ok",
            "title": "Test Note",
            "category": "personal_notes",
            "source_id": "local_003",
        }

        payload = build_notion_status_update(result)
        self.assertEqual(payload["Status"], "Indexed")
        self.assertNotIn("Graph Status", payload)


if __name__ == "__main__":
    unittest.main()
