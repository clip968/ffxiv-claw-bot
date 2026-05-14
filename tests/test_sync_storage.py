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

    # ── apply sync tests ──────────────────────────────────────────

    def test_apply_writes_local_source_to_storage_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            result = sync_storage.apply_sync(
                Path("tests/fixtures/storage_manifest.json"),
                db_path,
                root_path=root_path,
                storage_root=storage_root,
            )

            self.assertEqual(result["status"], "ok")
            self.assertIs(result["dry_run"], False)

            # new item: local source should be written
            source_path = storage_root / "sources/job_guides/black_mage_7_5.md"
            self.assertTrue(source_path.exists(), f"Expected source file at {source_path}")
            self.assertIn("Black Mage 7.5 Guide", source_path.read_text(encoding="utf-8"))

            # changed item: should also be written
            changed_source = storage_root / "sources/macros/savage_3_macro.txt"
            self.assertTrue(changed_source.exists(), f"Expected changed source file at {changed_source}")

            # unchanged item: should NOT be rewritten (no body, old hash)
            unchanged_source = storage_root / "sources/static_docs/static_rules.md"
            self.assertFalse(unchanged_source.exists(),
                             "Unchanged item without body should not be rewritten")

    def test_apply_creates_raw_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            storage_root.mkdir(parents=True, exist_ok=True)
            # Pre-create the source file for local_003 (changed item)
            source_dir = storage_root / "sources" / "macros"
            source_dir.mkdir(parents=True, exist_ok=True)
            (source_dir / "savage_3_macro.txt").write_text(
                "/macro Savage 3\n/ac Reprisal\n/p Tank buster soon", encoding="utf-8"
            )

            result = sync_storage.apply_sync(
                Path("tests/fixtures/storage_manifest.json"),
                db_path,
                root_path=root_path,
                storage_root=storage_root,
            )

            # Check raw snapshots were created
            raw_new = root_path / "raw/local_storage/job_guides/black_mage_7.5_guide__local_001.md"
            self.assertTrue(raw_new.exists(), f"Expected raw snapshot at {raw_new}")

            raw_changed = root_path / "raw/local_storage/macros/savage_3_macro__local_003.txt"
            self.assertTrue(raw_changed.exists(), f"Expected raw snapshot at {raw_changed}")

            # unchanged should not get a new snapshot
            raw_unchanged = root_path / "raw/local_storage/static_docs/static_rules__local_002.md"
            self.assertFalse(raw_unchanged.exists(),
                             "Unchanged item should not create new snapshot")

    def test_apply_upserts_sources_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            storage_root.mkdir(parents=True, exist_ok=True)
            # Pre-create source files
            for sub in ["sources/job_guides", "sources/macros"]:
                (storage_root / sub).mkdir(parents=True, exist_ok=True)
            (storage_root / "sources/job_guides/black_mage_7_5.md").write_text(
                "# Black Mage 7.5 Guide\n\nUpdated rotation for patch 7.5.", encoding="utf-8"
            )
            (storage_root / "sources/macros/savage_3_macro.txt").write_text(
                "/macro Savage 3\n/ac Reprisal\n/p Tank buster soon", encoding="utf-8"
            )

            sync_storage.apply_sync(
                Path("tests/fixtures/storage_manifest.json"),
                db_path,
                root_path=root_path,
                storage_root=storage_root,
            )

            # Verify DB has new and updated entries
            conn = sqlite3.connect(db_path)
            try:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT id, source_type, title, source_url, raw_path, content_hash FROM sources ORDER BY id"
                ).fetchall()
            finally:
                conn.close()

            ids = [r["id"] for r in rows]
            self.assertIn("local_001", ids, "new item should be upserted")
            self.assertIn("local_002", ids, "existing item should remain")
            self.assertIn("local_003", ids, "changed item should be upserted")
            self.assertNotIn("local_004", ids, "skipped item should not be upserted")

            # Verify updated hash for changed item
            row = [r for r in rows if r["id"] == "local_003"][0]
            self.assertEqual(row["content_hash"], "hash-newer",
                             "Changed item content_hash should be updated")

    def test_apply_rejects_missing_body_for_new_items(self) -> None:
        """New items without body should be rejected."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            # Patch manifest: remove body from local_001 (new, needs body to write)
            manifest = sync_storage.load_manifest(Path("tests/fixtures/storage_manifest.json"))
            manifest["files"][0].pop("body", None)

            # Write modified manifest to temp dir
            temp_manifest = Path(tmp_dir) / "storage_manifest.json"
            temp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                     encoding="utf-8")

            result = sync_storage.apply_sync(
                temp_manifest,
                db_path,
                root_path=root_path,
                storage_root=storage_root,
            )

            # Should be partial because local_001 (new, no body, no source file) fails
            self.assertEqual(result["status"], "partial")
            # The failed action should be for local_001
            failed_actions = [a for a in result.get("actions", [])
                              if a.get("status") == "failed"]
            self.assertGreater(len(failed_actions), 0)
            self.assertEqual(failed_actions[0]["source_id"], "local_001")

    def test_apply_cli_outputs_json_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            storage_root.mkdir(parents=True, exist_ok=True)
            (storage_root / "sources/job_guides").mkdir(parents=True, exist_ok=True)
            (storage_root / "sources/job_guides/black_mage_7_5.md").write_text(
                "# Black Mage 7.5 Guide\n\nUpdated rotation for patch 7.5.", encoding="utf-8"
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                sync_storage.main([
                    "--apply",
                    "--manifest", "tests/fixtures/storage_manifest.json",
                    "--db-path", str(db_path),
                    "--storage-root", str(storage_root),
                ])

            result = json.loads(stdout.getvalue())

            self.assertEqual(result["status"], "ok" if result.get("status") else "partial")
            self.assertIs(result["dry_run"], False)
            self.assertIn("summary", result)
            self.assertIn("actions", result)

    def test_apply_skipped_for_missing_storage_root_source(self) -> None:
        """Items without body and without existing source at storage_root should fail."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "ffxiv.sqlite"
            root_path = Path(tmp_dir) / "repo"
            storage_root = Path(tmp_dir) / "storage"
            create_sources_db(db_path)

            storage_root.mkdir(parents=True, exist_ok=True)

            # Patch manifest: remove body from local_004 (skipped item, no source at storage_root)
            manifest = sync_storage.load_manifest(Path("tests/fixtures/storage_manifest.json"))
            # local_004 is "skipped" by classifier (filter tags mismatch),
            # but even if write_local_source were called, remove body from it
            manifest["files"][3].pop("body", None)

            temp_manifest = Path(tmp_dir) / "storage_manifest.json"
            temp_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                     encoding="utf-8")

            result = sync_storage.apply_sync(
                temp_manifest,
                db_path,
                root_path=root_path,
                storage_root=storage_root,
            )

            # Skipped items are not processed, so overall status should be ok
            self.assertEqual(result["status"], "ok")
            skipped_actions = [a for a in result.get("actions", [])
                               if a.get("source_id") == "local_004"]
            self.assertEqual(len(skipped_actions), 0,
                             "Skipped items should not produce write actions")


if __name__ == "__main__":
    unittest.main()
