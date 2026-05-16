from __future__ import annotations

import contextlib
import importlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from tests.test_v05_process_source import ensure_sources_schema


QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_processing_queue (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT,
  body TEXT,
  local_path TEXT,
  url TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  error_stage TEXT,
  error_message TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0,
  processed_source_id TEXT,
  graph_status TEXT,
  result_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_attempt_at TEXT,
  last_success_at TEXT
)
"""


def require_pending_module(test: unittest.TestCase) -> Any:
    try:
        return importlib.import_module("tools.process_pending_sources")
    except ModuleNotFoundError as exc:
        if exc.name == "tools.process_pending_sources":
            test.fail("Expected tools.process_pending_sources for v06 pending loop")
        raise


class V06PendingSourceLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp_dir.name)
        self.storage_root = self.tmp / "storage"
        self.storage_root.mkdir(parents=True)
        self.repo_root = self.tmp / "repo"
        self.db_path = self.tmp / "ffxiv.sqlite"
        ensure_sources_schema(self.db_path)
        self._ensure_queue_schema()

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _ensure_queue_schema(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.executescript(QUEUE_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _insert_queue_source(
        self,
        source_id: str,
        *,
        source_type: str = "markdown_file",
        category: str = "patch_notes",
        title: str | None = None,
        body: str | None = None,
        local_path: Path | None = None,
        url: str | None = None,
        status: str = "pending",
        retry_count: int = 0,
    ) -> None:
        timestamp = "2026-05-16T00:00:00+00:00"
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute(
                """
                INSERT INTO source_processing_queue (
                    id, source_type, category, title, body, local_path, url,
                    status, retry_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    source_type,
                    category,
                    title or source_id,
                    body,
                    str(local_path) if local_path else None,
                    url,
                    status,
                    retry_count,
                    timestamp,
                    timestamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _markdown_file(self, name: str, body: str | None = None) -> Path:
        path = self.tmp / name
        path.write_text(body or f"# {name}\n\n- Gunbreaker changed.\n", encoding="utf-8")
        return path

    def _queue_row(self, source_id: str) -> sqlite3.Row:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM source_processing_queue WHERE id = ?",
                (source_id,),
            ).fetchone()
            self.assertIsNotNone(row)
            return row
        finally:
            conn.close()

    def run_pending(self, argv: list[str]) -> dict[str, Any]:
        module = require_pending_module(self)
        process_source = getattr(module, "process_source")
        old_root = getattr(process_source, "ROOT")
        setattr(process_source, "ROOT", self.repo_root)
        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                module.main(
                    [
                        *argv,
                        "--storage-root",
                        str(self.storage_root),
                        "--db-path",
                        str(self.db_path),
                    ]
                )
        finally:
            setattr(process_source, "ROOT", old_root)
        return json.loads(stdout.getvalue())

    def test_pending_loop_processes_pending_sources_up_to_limit(self) -> None:
        self._insert_queue_source("pending_1", local_path=self._markdown_file("one.md"))
        self._insert_queue_source("pending_2", local_path=self._markdown_file("two.md"))
        self._insert_queue_source("pending_3", local_path=self._markdown_file("three.md"))

        result = self.run_pending(["--limit", "2"])

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["targeted"], 2)
        self.assertEqual(result["summary"]["processed"], 2)
        self.assertEqual(self._queue_row("pending_1")["status"], "processed")
        self.assertEqual(self._queue_row("pending_2")["status"], "processed")
        self.assertEqual(self._queue_row("pending_3")["status"], "pending")

    def test_pending_loop_dry_run_does_not_mutate_status(self) -> None:
        self._insert_queue_source("pending_dry", local_path=self._markdown_file("dry.md"))

        result = self.run_pending(["--dry-run", "--limit", "1"])

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["summary"]["targeted"], 1)
        self.assertEqual(result["actions"][0]["status"], "planned")
        row = self._queue_row("pending_dry")
        self.assertEqual(row["status"], "pending")
        self.assertEqual(row["retry_count"], 0)
        self.assertIsNone(row["last_attempt_at"])

    def test_pending_loop_marks_successful_source_processed(self) -> None:
        self._insert_queue_source(
            "pending_success",
            title="Success Source",
            local_path=self._markdown_file("success.md"),
        )

        result = self.run_pending(["--limit", "1"])

        row = self._queue_row("pending_success")
        self.assertEqual(result["actions"][0]["status"], "processed")
        self.assertEqual(row["status"], "processed")
        self.assertTrue(row["processed_source_id"].startswith("local_"))
        self.assertEqual(row["graph_status"], "built")
        self.assertIsNone(row["error_message"])
        self.assertIsNotNone(row["last_success_at"])

    def test_pending_loop_marks_failed_source_error(self) -> None:
        unsupported = self.tmp / "image.png"
        unsupported.write_bytes(b"not really an image")
        self._insert_queue_source(
            "pending_error",
            source_type="binary_attachment",
            category="bis_sheets",
            local_path=unsupported,
        )

        result = self.run_pending(["--limit", "1"])

        row = self._queue_row("pending_error")
        self.assertEqual(result["actions"][0]["status"], "error")
        self.assertEqual(row["status"], "error")
        self.assertEqual(row["error_stage"], "extract")
        self.assertIn("Unsupported source extension: .png", row["error_message"])

    def test_pending_loop_increments_retry_count(self) -> None:
        unsupported = self.tmp / "broken.png"
        unsupported.write_bytes(b"not really an image")
        self._insert_queue_source(
            "pending_retry_count",
            source_type="binary_attachment",
            category="bis_sheets",
            local_path=unsupported,
            retry_count=2,
        )

        self.run_pending(["--limit", "1"])

        row = self._queue_row("pending_retry_count")
        self.assertEqual(row["status"], "error")
        self.assertEqual(row["retry_count"], 3)
        self.assertIsNotNone(row["last_attempt_at"])

    def test_retry_errors_only_retries_below_max_retry(self) -> None:
        self._insert_queue_source(
            "retry_allowed",
            local_path=self._markdown_file("retry-allowed.md"),
            status="error",
            retry_count=1,
        )
        self._insert_queue_source(
            "retry_blocked",
            local_path=self._markdown_file("retry-blocked.md"),
            status="error",
            retry_count=3,
        )

        result = self.run_pending(["--retry-errors", "--max-retry", "3", "--limit", "5"])

        self.assertEqual(result["summary"]["targeted"], 1)
        self.assertEqual(self._queue_row("retry_allowed")["status"], "processed")
        blocked = self._queue_row("retry_blocked")
        self.assertEqual(blocked["status"], "error")
        self.assertEqual(blocked["retry_count"], 3)

    def test_process_pending_sources_skips_derived_wiki_by_default(self) -> None:
        self._insert_queue_source(
            "pending_default_skip",
            source_type="text_note",
            category="patch_notes",
            title="Patch 7.2 Notes",
            body="# Patch 7.2 Notes\n\n## Gunbreaker\n\n- Default skip change.\n",
        )

        self.run_pending(["--limit", "1"])

        row = self._queue_row("pending_default_skip")
        self.assertEqual(row["status"], "processed")
        self.assertFalse((self.repo_root / "wiki" / "jobs" / "gunbreaker.md").exists())

    def test_process_pending_sources_can_build_derived_wiki_when_enabled(self) -> None:
        self._insert_queue_source(
            "pending_build_derived",
            source_type="text_note",
            category="patch_notes",
            title="Patch 7.2 Notes",
            body="# Patch 7.2 Notes\n\n## Gunbreaker\n\n- Hooked derived change.\n",
        )

        result = self.run_pending(["--limit", "1", "--build-derived-wiki"])

        row = self._queue_row("pending_build_derived")
        source_result = json.loads(row["result_json"])
        self.assertEqual(result["actions"][0]["status"], "derived_wiki_built")
        self.assertEqual(row["status"], "derived_wiki_built")
        self.assertEqual(source_result["derived_wiki"]["status"], "ok")
        self.assertTrue((self.repo_root / "wiki" / "jobs" / "gunbreaker.md").exists())

    def test_process_pending_sources_build_derived_wiki_indexes_job_wiki_documents(self) -> None:
        self._insert_queue_source(
            "pending_build_derived_fts",
            source_type="text_note",
            category="patch_notes",
            title="Patch 7.2 Notes",
            body="# Patch 7.2 Notes\n\n## Gunbreaker\n\n- Pending FTS hook change.\n",
        )

        self.run_pending(["--limit", "1", "--build-derived-wiki"])

        row = self._queue_row("pending_build_derived_fts")
        source_result = json.loads(row["result_json"])
        conn = sqlite3.connect(str(self.db_path))
        try:
            fts_row = conn.execute(
                "SELECT title, body FROM wiki_fts WHERE page_id = ?",
                ("job_gunbreaker",),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(row["status"], "derived_wiki_built")
        self.assertEqual(source_result["derived_wiki"]["status"], "ok")
        self.assertEqual(source_result["derived_wiki"]["fts_index"]["status"], "ok")
        self.assertIsNotNone(fts_row)
        self.assertIn("Gunbreaker", fts_row[0])
        self.assertIn("Pending FTS hook change", fts_row[1])

    def test_derived_wiki_failure_records_derived_wiki_stage(self) -> None:
        module = importlib.import_module("tools.process_source")
        self._insert_queue_source(
            "pending_derived_error",
            source_type="text_note",
            category="patch_notes",
            title="Patch 7.2 Notes",
            body="# Patch 7.2 Notes\n\n## Gunbreaker\n\n- Failure path change.\n",
        )

        with patch.object(module.generate_derived_wiki, "run") as run_derived:
            run_derived.side_effect = RuntimeError("derived boom")
            self.run_pending(["--limit", "1", "--build-derived-wiki"])

        row = self._queue_row("pending_derived_error")
        self.assertEqual(row["status"], "processed")
        self.assertEqual(row["error_stage"], "derived_wiki_generate")
        self.assertIn("derived boom", row["error_message"])

    def test_derived_wiki_failure_does_not_mark_source_as_failed(self) -> None:
        module = importlib.import_module("tools.process_source")
        self._insert_queue_source(
            "pending_derived_failure_successful_source",
            source_type="text_note",
            category="patch_notes",
            title="Patch 7.2 Notes",
            body="# Patch 7.2 Notes\n\n## Gunbreaker\n\n- Failure remains processed.\n",
        )

        with patch.object(module.generate_derived_wiki, "run") as run_derived:
            run_derived.side_effect = RuntimeError("derived failed")
            result = self.run_pending(["--limit", "1", "--build-derived-wiki"])

        row = self._queue_row("pending_derived_failure_successful_source")
        source_result = json.loads(row["result_json"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["actions"][0]["result_status"], "ok")
        self.assertEqual(row["status"], "processed")
        self.assertEqual(source_result["status"], "ok")
        self.assertEqual(source_result["derived_wiki"]["status"], "error")


if __name__ == "__main__":
    unittest.main()
