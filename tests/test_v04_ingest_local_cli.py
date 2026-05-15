from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

SOURCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT,
  source_url TEXT,
  raw_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  language TEXT,
  patch TEXT,
  job TEXT,
  raid TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
"""


def _ensure_db_schema(db_path: Path) -> None:
    """Create the sources table if it does not exist."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(SOURCES_SCHEMA)
        conn.commit()
    finally:
        conn.close()


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

    def test_text_note_apply_stores_content_hash_on_insert(self) -> None:
        """Regression: content_hash must be computed and stored on INSERT."""
        main = require_callable(self, "tools.ingest_local", "main")

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_root = Path(tmp_dir) / "storage"
            storage_root.mkdir(parents=True, exist_ok=True)
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            _ensure_db_schema(db_path)

            body = "Use Reprisal before the tank buster."

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "--apply",
                        "--source-type",
                        "text_note",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Raid mitigation note",
                        "--body",
                        body,
                        "--storage-root",
                        str(storage_root),
                        "--db-path",
                        str(db_path),
                    ]
                )

            result = json.loads(stdout.getvalue())
            self.assertEqual(result["status"], "ok")
            upsert_action = next(
                a for a in result["actions"] if a["action"] == "upsert_source"
            )
            self.assertEqual(upsert_action["status"], "inserted")
            source_id = result["source_id"]

            conn = sqlite3.connect(str(db_path))
            try:
                row = conn.execute(
                    "SELECT content_hash FROM sources WHERE id = ?", (source_id,)
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row, "source row must exist in DB")
            stored_hash = row[0]
            expected_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            self.assertEqual(
                stored_hash,
                expected_hash,
                f"content_hash ({stored_hash}) must match SHA-256 of body ({expected_hash})",
            )

    def test_text_note_apply_stores_content_hash_on_update(self) -> None:
        """Regression: content_hash must be updated on UPDATE (second apply)."""
        main = require_callable(self, "tools.ingest_local", "main")

        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_root = Path(tmp_dir) / "storage"
            storage_root.mkdir(parents=True, exist_ok=True)
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            _ensure_db_schema(db_path)

            body_v1 = "Use Reprisal before the tank buster."

            # First apply: INSERT
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "--apply",
                        "--source-type",
                        "text_note",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Raid mitigation note",
                        "--body",
                        body_v1,
                        "--storage-root",
                        str(storage_root),
                        "--db-path",
                        str(db_path),
                    ]
                )
            result = json.loads(stdout.getvalue())
            source_id = result["source_id"]

            body_v2 = "Use Addle before the tank buster, then Reprisal."

            # Second apply with different body: UPDATE
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "--apply",
                        "--source-type",
                        "text_note",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Raid mitigation note",
                        "--body",
                        body_v2,
                        "--storage-root",
                        str(storage_root),
                        "--db-path",
                        str(db_path),
                    ]
                )
            result_v2 = json.loads(stdout.getvalue())
            upsert_v2 = next(
                a for a in result_v2["actions"] if a["action"] == "upsert_source"
            )
            self.assertEqual(upsert_v2["status"], "updated")

            conn = sqlite3.connect(str(db_path))
            try:
                row = conn.execute(
                    "SELECT content_hash FROM sources WHERE id = ?", (source_id,)
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row)
            stored_hash = row[0]
            expected_hash = hashlib.sha256(body_v2.encode("utf-8")).hexdigest()
            self.assertEqual(
                stored_hash,
                expected_hash,
                f"content_hash ({stored_hash}) must match SHA-256 of new body ({expected_hash})",
            )


if __name__ == "__main__":
    unittest.main()
