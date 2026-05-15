from __future__ import annotations

import contextlib
import importlib
import io
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
            test.fail(f"Expected {module_name}.{function_name} for v04 local ingest CLI")
        raise

    function = getattr(module, function_name, None)
    if not callable(function):
        test.fail(f"Expected callable {module_name}.{function_name} for v04 local ingest CLI")
    return function


class V04IngestLocalCliRedTests(unittest.TestCase):
    def test_text_note_dry_run_outputs_local_ingest_actions_without_writing_files(self) -> None:
        main = require_callable(self, "tools.ingest_local", "main")

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_root = Path(tmp_dir) / "storage"
            db_path = Path(tmp_dir) / "ffxiv.sqlite"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "--dry-run",
                        "--source-type",
                        "text_note",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Raid mitigation note",
                        "--body",
                        "Use Reprisal before the tank buster.",
                        "--storage-root",
                        str(storage_root),
                        "--db-path",
                        str(db_path),
                    ]
                )

            result = json.loads(stdout.getvalue())
            action_names = [action["action"] for action in result["actions"]]

            self.assertEqual(result["status"], "ok")
            self.assertIs(result["dry_run"], True)
            self.assertEqual(
                action_names,
                [
                    "validate_request",
                    "write_local_source",
                    "snapshot_raw",
                    "upsert_source",
                ],
            )
            self.assertNotIn("update_notion_status", action_names)
            self.assertFalse(
                (storage_root / "sources/personal_notes/raid_mitigation_note.md").exists(),
                "dry-run must not write the local source file",
            )


if __name__ == "__main__":
    unittest.main()
