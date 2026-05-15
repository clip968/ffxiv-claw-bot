from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


def require_callable(test: unittest.TestCase, module_name: str, function_name: str) -> Callable[..., Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            test.fail(f"Expected {module_name}.{function_name} for v04 local publish-then-rebuild")
        raise

    function = getattr(module, function_name, None)
    if not callable(function):
        test.fail(f"Expected callable {module_name}.{function_name} for v04 local publish-then-rebuild")
    return function


class V04LocalPublishThenRebuildRedTests(unittest.TestCase):
    def test_successful_local_ingest_dry_run_plans_compile_fts_and_graph_actions(self) -> None:
        rebuild_after_ingest = require_callable(
            self,
            "tools.local_rebuild",
            "rebuild_after_ingest",
        )

        ingest_result = {
            "status": "ok",
            "dry_run": False,
            "source_id": "local_001",
            "title": "Black Mage 7.5 Guide",
            "source_type": "local_document",
            "raw_path": "raw/local_storage/job_guides/black_mage_7_5__local_001.md",
            "actions": [
                {"action": "write_local_source", "status": "written"},
                {"action": "snapshot_raw", "status": "written"},
                {"action": "upsert_source", "status": "inserted"},
            ],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = rebuild_after_ingest(
                ingest_result,
                root_path=Path(tmp_dir) / "repo",
                db_path=Path(tmp_dir) / "ffxiv.sqlite",
                dry_run=True,
            )

        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], True)
        self.assertEqual(
            [action["action"] for action in result["actions"]],
            ["compile_wiki", "index_fts", "build_graph"],
        )
        self.assertNotIn("Drive", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
