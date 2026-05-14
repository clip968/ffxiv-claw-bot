from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools import sync_storage


def create_sources_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE sources (
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
        )
        conn.executemany(
            """
            INSERT INTO sources (
              id,
              source_type,
              title,
              source_url,
              raw_path,
              content_hash,
              created_at,
              updated_at
            )
            VALUES (?, 'local_document', ?, ?, ?, ?, '2026-05-14T00:00:00+00:00', '2026-05-14T00:00:00+00:00')
            """,
            [
                (
                    "local_002",
                    "Static Rules",
                    "local://sources/static_docs/static_rules.md",
                    "raw/local_storage/static_docs/static_rules__local_002.md",
                    "hash-same",
                ),
                (
                    "local_003",
                    "Savage 3 Macro",
                    "local://sources/macros/savage_3_macro.txt",
                    "raw/local_storage/macros/savage_3_macro__local_003.txt",
                    "hash-old",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


class SyncStorageTests(unittest.TestCase):
    def test_planned_raw_path_uses_local_storage_category_title_source_id_and_extension(self) -> None:
        item = {
            "source_id": "local_001",
            "title": "Black Mage 7.5 Guide",
            "category": "job_guides",
            "content_type": "text/markdown",
            "canonical_path": "sources/job_guides/black_mage_7_5.md",
        }

        self.assertEqual(
            sync_storage.planned_raw_path(item),
            "raw/local_storage/job_guides/black_mage_7.5_guide__local_001.md",
        )

    def test_plan_sync_classifies_new_changed_unchanged_and_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            create_sources_db(db_path)

            result = sync_storage.plan_sync(
                Path("tests/fixtures/storage_manifest.json"),
                db_path,
            )

        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], True)
        self.assertEqual(
            result["summary"],
            {
                "new": 1,
                "changed": 1,
                "unchanged": 1,
                "skipped": 1,
            },
        )

        actions = {item["source_id"]: item["action"] for item in result["items"]}
        self.assertEqual(
            actions,
            {
                "local_001": "new",
                "local_002": "unchanged",
                "local_003": "changed",
                "local_004": "skipped",
            },
        )

        self.assertEqual(
            result["items"][0]["planned_raw_path"],
            "raw/local_storage/job_guides/black_mage_7.5_guide__local_001.md",
        )

    def test_cli_dry_run_outputs_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            create_sources_db(db_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                sync_storage.main(
                    [
                        "--dry-run",
                        "--manifest",
                        "tests/fixtures/storage_manifest.json",
                        "--db-path",
                        str(db_path),
                    ]
                )

        result = json.loads(stdout.getvalue())

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["new"], 1)
        self.assertEqual(result["summary"]["changed"], 1)
        self.assertEqual(result["summary"]["unchanged"], 1)
        self.assertEqual(result["summary"]["skipped"], 1)

    def test_dry_run_does_not_create_raw_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            create_sources_db(db_path)

            sync_storage.plan_sync(
                Path("tests/fixtures/storage_manifest.json"),
                db_path,
                root_path=root_path,
            )

            self.assertFalse((root_path / "raw").exists())


if __name__ == "__main__":
    unittest.main()
