from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools import sync_drive


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
            VALUES (?, 'drive_document', ?, ?, ?, ?, '2026-05-14T00:00:00+00:00', '2026-05-14T00:00:00+00:00')
            """,
            [
                (
                    "src_existing_unchanged",
                    "Static Rules",
                    "gdrive://drive_file_002",
                    "raw/drive/static_docs/static_rules__drive_file_002.md",
                    "hash-same",
                ),
                (
                    "src_existing_changed",
                    "Savage 3 Macro",
                    "gdrive://drive_file_003",
                    "raw/drive/macros/savage_3_macro__drive_file_003.txt",
                    "hash-old",
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


class SyncDriveTests(unittest.TestCase):
    def test_planned_raw_path_uses_category_safe_title_file_id_and_extension(self) -> None:
        item = {
            "id": "drive_file_001",
            "name": "Black Mage 7.5 Guide",
            "category": "job_guides",
            "exportExt": "md",
        }

        self.assertEqual(
            sync_drive.planned_raw_path(item),
            "raw/drive/job_guides/black_mage_7.5_guide__drive_file_001.md",
        )

    def test_plan_sync_classifies_new_changed_unchanged_and_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            create_sources_db(db_path)

            result = sync_drive.plan_sync(
                Path("tests/fixtures/drive_manifest.json"),
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

        actions = {item["drive_file_id"]: item["action"] for item in result["items"]}
        self.assertEqual(
            actions,
            {
                "drive_file_001": "new",
                "drive_file_002": "unchanged",
                "drive_file_003": "changed",
                "drive_file_004": "skipped",
            },
        )

        self.assertEqual(
            result["items"][0]["planned_raw_path"],
            "raw/drive/job_guides/black_mage_7.5_guide__drive_file_001.md",
        )

    def test_cli_dry_run_outputs_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            create_sources_db(db_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                sync_drive.main(
                    [
                        "--dry-run",
                        "--manifest",
                        "tests/fixtures/drive_manifest.json",
                        "--db-path",
                        str(db_path),
                    ]
                )

        result = json.loads(stdout.getvalue())

        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], True)
        self.assertEqual(result["summary"]["new"], 1)
        self.assertEqual(result["summary"]["changed"], 1)

    def test_apply_writes_new_and_changed_raw_files_and_upserts_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            result = sync_drive.apply_sync(
                Path("tests/fixtures/drive_manifest.json"),
                db_path,
                root_path,
            )

            self.assertEqual(result["status"], "ok")
            self.assertIs(result["dry_run"], False)
            self.assertEqual(
                result["summary"],
                {
                    "new": 1,
                    "changed": 1,
                    "unchanged": 1,
                    "skipped": 1,
                },
            )

            new_raw = (
                root_path
                / "raw/drive/job_guides/black_mage_7.5_guide__drive_file_001.md"
            )
            changed_raw = (
                root_path
                / "raw/drive/macros/savage_3_macro__drive_file_003.txt"
            )

            self.assertEqual(
                new_raw.read_text(encoding="utf-8"),
                "# Black Mage 7.5 Guide\n\nUse Ley Lines with the updated opener.\n",
            )
            self.assertEqual(
                changed_raw.read_text(encoding="utf-8"),
                "Savage 3 macro updated for clock spots.\n",
            )

            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT id, title, source_url, raw_path, content_hash
                      FROM sources
                     WHERE source_type = 'drive_document'
                     ORDER BY source_url
                    """
                ).fetchall()

            self.assertEqual(len(rows), 3)
            by_url = {row["source_url"]: dict(row) for row in rows}
            self.assertEqual(
                by_url["gdrive://drive_file_001"]["raw_path"],
                "raw/drive/job_guides/black_mage_7.5_guide__drive_file_001.md",
            )
            self.assertEqual(
                by_url["gdrive://drive_file_001"]["content_hash"],
                "hash-new",
            )
            self.assertEqual(
                by_url["gdrive://drive_file_003"]["content_hash"],
                "hash-updated",
            )

    def test_apply_is_idempotent_for_repeated_manifest_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            first = sync_drive.apply_sync(
                Path("tests/fixtures/drive_manifest.json"),
                db_path,
                root_path,
            )
            second = sync_drive.apply_sync(
                Path("tests/fixtures/drive_manifest.json"),
                db_path,
                root_path,
            )

            self.assertEqual(first["summary"]["new"], 1)
            self.assertEqual(first["summary"]["changed"], 1)
            self.assertEqual(second["summary"]["new"], 0)
            self.assertEqual(second["summary"]["changed"], 0)
            self.assertEqual(second["summary"]["unchanged"], 3)

            with sqlite3.connect(db_path) as conn:
                count = conn.execute(
                    """
                    SELECT COUNT(*)
                      FROM sources
                     WHERE source_type = 'drive_document'
                    """
                ).fetchone()[0]

            self.assertEqual(count, 3)

    def test_cli_apply_outputs_json_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                sync_drive.main(
                    [
                        "--apply",
                        "--manifest",
                        "tests/fixtures/drive_manifest.json",
                        "--db-path",
                        str(db_path),
                        "--root-path",
                        str(root_path),
                    ]
                )

        result = json.loads(stdout.getvalue())

        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], False)
        self.assertEqual(result["summary"]["new"], 1)
        self.assertEqual(result["summary"]["changed"], 1)


if __name__ == "__main__":
    unittest.main()
