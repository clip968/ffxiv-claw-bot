from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import tools.build_graph as build_graph_module
import tools.compile_wiki as compile_wiki_module

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


def ensure_wiki_tables(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS wiki_pages (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              title TEXT NOT NULL,
              path TEXT NOT NULL,
              patch TEXT,
              job TEXT,
              raid TEXT,
              source_ids TEXT NOT NULL,
              confidence TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
              page_id, title, body, tokenize = 'unicode61'
            );
            CREATE TABLE IF NOT EXISTS graph_nodes (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              name TEXT NOT NULL,
              aliases TEXT,
              properties TEXT
            );
            CREATE TABLE IF NOT EXISTS graph_edges (
              id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL,
              target_id TEXT NOT NULL,
              type TEXT NOT NULL,
              confidence TEXT NOT NULL,
              score REAL,
              source_page_id TEXT,
              source_ids TEXT,
              properties TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()


class FakeDriveRequest:
    def __init__(self, response: object) -> None:
        self.response = response

    def execute(self) -> object:
        return self.response


class FakeDriveFiles:
    def __init__(
        self,
        *,
        listed_files: list[dict[str, object]] | None = None,
        export_contents: dict[str, bytes] | None = None,
        download_contents: dict[str, bytes] | None = None,
    ) -> None:
        self.listed_files = listed_files or []
        self.export_contents = export_contents or {}
        self.download_contents = download_contents or {}
        self.exports: list[tuple[str, str]] = []
        self.downloads: list[str] = []

    def list(self, **kwargs: object) -> FakeDriveRequest:
        return FakeDriveRequest({"files": self.listed_files})

    def export_media(self, *, fileId: str, mimeType: str) -> FakeDriveRequest:
        self.exports.append((fileId, mimeType))
        return FakeDriveRequest(self.export_contents[fileId])

    def get_media(self, *, fileId: str) -> FakeDriveRequest:
        self.downloads.append(fileId)
        return FakeDriveRequest(self.download_contents[fileId])


class FakeDriveService:
    def __init__(self, files_resource: FakeDriveFiles) -> None:
        self.files_resource = files_resource

    def files(self) -> FakeDriveFiles:
        return self.files_resource


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

            conn = sqlite3.connect(db_path)
            try:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT id, title, source_url, raw_path, content_hash
                      FROM sources
                     WHERE source_type = 'drive_document'
                     ORDER BY source_url
                    """
                ).fetchall()
            finally:
                conn.close()

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

            conn = sqlite3.connect(db_path)
            try:
                count = conn.execute(
                    """
                    SELECT COUNT(*)
                      FROM sources
                     WHERE source_type = 'drive_document'
                    """
                ).fetchone()[0]
            finally:
                conn.close()

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

    def test_drive_files_to_manifest_maps_api_response_to_manifest_items(self) -> None:
        files = [
            {
                "id": "folder_job",
                "name": "job_guides",
                "mimeType": sync_drive.GOOGLE_DRIVE_FOLDER_MIME,
            },
            {
                "id": "drive_doc_001",
                "name": "Black Mage Guide",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-05-14T01:00:00Z",
                "webViewLink": "https://drive.google.com/file/d/drive_doc_001/view",
                "parents": ["folder_job"],
                "headRevisionId": "rev-doc-001",
            },
            {
                "id": "drive_txt_001",
                "name": "Macro Notes",
                "mimeType": "text/plain",
                "modifiedTime": "2026-05-14T01:05:00Z",
                "webViewLink": "https://drive.google.com/file/d/drive_txt_001/view",
                "parents": ["folder_job"],
                "md5Checksum": "md5-txt-001",
            },
        ]

        manifest = sync_drive.drive_files_to_manifest(
            files,
            root_folder="FFXIV_KB",
            category_by_folder_id={"folder_job": "job_guides"},
        )

        self.assertEqual(manifest["root_folder"], "FFXIV_KB")
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(
            manifest["files"][0],
            {
                "id": "drive_doc_001",
                "name": "Black Mage Guide",
                "category": "job_guides",
                "mimeType": "application/vnd.google-apps.document",
                "modifiedTime": "2026-05-14T01:00:00Z",
                "webViewLink": "https://drive.google.com/file/d/drive_doc_001/view",
                "exportExt": "md",
                "contentHash": "rev-doc-001",
            },
        )
        self.assertEqual(manifest["files"][1]["exportExt"], "txt")
        self.assertEqual(manifest["files"][1]["contentHash"], "md5-txt-001")

    def test_download_drive_contents_exports_google_docs_to_markdown_and_hashes_sha256(self) -> None:
        content = b"# Black Mage Guide\n\nUse Ley Lines.\n"
        files_resource = FakeDriveFiles(export_contents={"drive_doc_001": content})
        service = FakeDriveService(files_resource)
        manifest = {
            "root_folder": "FFXIV_KB",
            "files": [
                {
                    "id": "drive_doc_001",
                    "name": "Black Mage Guide",
                    "category": "job_guides",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": "2026-05-14T01:00:00Z",
                    "webViewLink": "https://drive.google.com/file/d/drive_doc_001/view",
                    "exportExt": "md",
                    "contentHash": "rev-doc-001",
                }
            ],
        }

        downloaded_manifest, content_by_file_id = sync_drive.download_drive_contents(
            service,
            manifest,
        )

        self.assertEqual(
            files_resource.exports,
            [("drive_doc_001", "text/markdown")],
        )
        self.assertEqual(content_by_file_id["drive_doc_001"], content)
        self.assertEqual(
            downloaded_manifest["files"][0]["contentHash"],
            hashlib.sha256(content).hexdigest(),
        )

    def test_download_drive_contents_downloads_binary_files_and_hashes_sha256(self) -> None:
        content = b"%PDF-1.7\nbinary pdf content\n"
        files_resource = FakeDriveFiles(download_contents={"drive_pdf_001": content})
        service = FakeDriveService(files_resource)
        manifest = {
            "root_folder": "FFXIV_KB",
            "files": [
                {
                    "id": "drive_pdf_001",
                    "name": "Raid Timeline.pdf",
                    "category": "raid_guides",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-05-14T01:00:00Z",
                    "webViewLink": "https://drive.google.com/file/d/drive_pdf_001/view",
                }
            ],
        }

        downloaded_manifest, content_by_file_id = sync_drive.download_drive_contents(
            service,
            manifest,
        )

        self.assertEqual(files_resource.downloads, ["drive_pdf_001"])
        self.assertEqual(content_by_file_id["drive_pdf_001"], content)
        self.assertEqual(downloaded_manifest["files"][0]["exportExt"], "pdf")
        self.assertEqual(
            downloaded_manifest["files"][0]["contentHash"],
            hashlib.sha256(content).hexdigest(),
        )

    def test_download_drive_contents_skips_google_sheets(self) -> None:
        files_resource = FakeDriveFiles()
        service = FakeDriveService(files_resource)
        manifest = {
            "root_folder": "FFXIV_KB",
            "files": [
                {
                    "id": "drive_sheet_001",
                    "name": "BiS Sheet.csv",
                    "category": "bis_sheets",
                    "mimeType": "application/vnd.google-apps.spreadsheet",
                    "modifiedTime": "2026-05-14T01:00:00Z",
                    "webViewLink": "https://drive.google.com/file/d/drive_sheet_001/view",
                }
            ],
        }

        downloaded_manifest, content_by_file_id = sync_drive.download_drive_contents(
            service,
            manifest,
        )

        self.assertEqual(files_resource.downloads, [])
        self.assertEqual(content_by_file_id, {})
        self.assertEqual(
            downloaded_manifest["files"][0]["skipReason"],
            "unsupported download mime type",
        )

    def test_cli_from_drive_download_apply_writes_exported_doc_and_hash(self) -> None:
        content = b"# Black Mage Guide\n\nUse Ley Lines.\n"
        files_resource = FakeDriveFiles(
            listed_files=[
                {
                    "id": "folder_job",
                    "name": "job_guides",
                    "mimeType": sync_drive.GOOGLE_DRIVE_FOLDER_MIME,
                },
                {
                    "id": "drive_doc_001",
                    "name": "Black Mage Guide",
                    "mimeType": "application/vnd.google-apps.document",
                    "modifiedTime": "2026-05-14T01:00:00Z",
                    "webViewLink": "https://drive.google.com/file/d/drive_doc_001/view",
                    "parents": ["folder_job"],
                    "headRevisionId": "rev-doc-001",
                },
            ],
            export_contents={"drive_doc_001": content},
        )
        service = FakeDriveService(files_resource)
        original_load_credentials = sync_drive.load_drive_credentials
        original_build_service = sync_drive.build_drive_service

        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            try:
                sync_drive.load_drive_credentials = lambda token_path: object()
                sync_drive.build_drive_service = lambda credentials: service

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    sync_drive.main(
                        [
                            "--from-drive",
                            "--download",
                            "--apply",
                            "--drive-folder-id",
                            "folder_root",
                            "--db-path",
                            str(db_path),
                            "--root-path",
                            str(root_path),
                        ]
                    )
            finally:
                sync_drive.load_drive_credentials = original_load_credentials
                sync_drive.build_drive_service = original_build_service

            result = json.loads(stdout.getvalue())
            raw_path = (
                root_path
                / "raw/drive/job_guides/black_mage_guide__drive_doc_001.md"
            )

            self.assertEqual(result["status"], "ok")
            self.assertIs(result["dry_run"], False)
            self.assertEqual(result["summary"]["new"], 1)
            self.assertEqual(raw_path.read_bytes(), content)

            conn = sqlite3.connect(db_path)
            try:
                content_hash = conn.execute(
                    """
                    SELECT content_hash
                      FROM sources
                     WHERE source_url = 'gdrive://drive_doc_001'
                    """
                ).fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(content_hash, hashlib.sha256(content).hexdigest())

    def test_missing_oauth_token_raises_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_path = Path(tmp_dir) / "missing-token.json"

            with self.assertRaisesRegex(
                sync_drive.DriveAuthError,
                "OAuth token not found",
            ):
                sync_drive.load_drive_credentials(token_path)

    def test_cli_from_drive_without_token_outputs_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_path = Path(tmp_dir) / "missing-token.json"

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    sync_drive.main(
                        [
                            "--from-drive",
                            "--dry-run",
                            "--drive-folder-id",
                            "folder_root",
                            "--token-path",
                            str(token_path),
                        ]
                    )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("OAuth token not found", stderr.getvalue())

    def test_cli_rejects_from_drive_apply_without_download(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                sync_drive.main(
                    [
                        "--from-drive",
                        "--apply",
                        "--drive-folder-id",
                        "folder_root",
                    ]
        )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "--from-drive --apply requires --download",
            stderr.getvalue(),
        )

    def test_rebuild_for_items_after_apply_compiles_and_builds_graph(self) -> None:
        """rebuild_for_items should run compile_wiki and build_graph for new/changed sources."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            db_path = root_path / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            create_sources_db(db_path)

            # Run apply_sync to write raw files and upsert sources
            apply_result = sync_drive.apply_sync(
                Path("tests/fixtures/drive_manifest.json"),
                db_path,
                root_path,
            )

            # Collect source IDs of new/changed items
            source_ids = [
                item["source_id"]
                for item in apply_result["items"]
                if item.get("action") in ("new", "changed") and item.get("source_id")
            ]
            self.assertEqual(len(source_ids), 2)
            # New item uses generated drive_source_id; changed item uses existing DB id
            self.assertIn("drive_drive_file_001", source_ids)
            self.assertIn("src_existing_changed", source_ids)

            # Override module-level constants for compile_wiki and build_graph
            original_compile_root = compile_wiki_module.ROOT
            original_compile_db = compile_wiki_module.DB_PATH
            original_compile_summary = compile_wiki_module.SUMMARY_DIR
            original_build_db = build_graph_module.DB_PATH
            original_build_graph_dir = build_graph_module.GRAPH_DIR

            compile_wiki_module.ROOT = root_path
            compile_wiki_module.DB_PATH = db_path
            compile_wiki_module.SUMMARY_DIR = root_path / "wiki" / "source_summaries"
            build_graph_module.DB_PATH = db_path
            build_graph_module.GRAPH_DIR = root_path / "graph"

            try:
                rebuild_result = sync_drive.rebuild_for_items(source_ids)
            finally:
                compile_wiki_module.ROOT = original_compile_root
                compile_wiki_module.DB_PATH = original_compile_db
                compile_wiki_module.SUMMARY_DIR = original_compile_summary
                build_graph_module.DB_PATH = original_build_db
                build_graph_module.GRAPH_DIR = original_build_graph_dir

            # Verify rebuild results
            self.assertTrue(rebuild_result["rebuild"])
            self.assertEqual(rebuild_result["compile_count"], 2)
            self.assertEqual(len(rebuild_result["compile_errors"]), 0)
            self.assertEqual(len(rebuild_result["compile_ok_ids"]), 2)
            self.assertEqual(rebuild_result["graph_errors"], [])

            # Verify wiki summaries were created
            summary_dir = root_path / "wiki" / "source_summaries"
            self.assertTrue((summary_dir / "drive_drive_file_001.md").exists())
            self.assertTrue((summary_dir / "src_existing_changed.md").exists())

            # Verify FTS entries exist for both sources
            conn = sqlite3.connect(db_path)
            try:
                fts_count = conn.execute(
                    "SELECT COUNT(*) FROM wiki_fts WHERE page_id IN (?, ?)",
                    ("wiki_drive_drive_file_001", "wiki_existing_changed"),
                ).fetchone()[0]
                self.assertEqual(fts_count, 2)

                # Verify graph entries exist
                node_count = conn.execute(
                    "SELECT COUNT(*) FROM graph_nodes"
                ).fetchone()[0]
                edge_count = conn.execute(
                    "SELECT COUNT(*) FROM graph_edges"
                ).fetchone()[0]
                self.assertGreater(node_count, 0)
                self.assertGreater(edge_count, 0)
            finally:
                conn.close()

    def test_cli_rebuild_requires_apply(self) -> None:
        """--rebuild without --apply should be rejected."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                sync_drive.main(
                    [
                        "--rebuild",
                        "--dry-run",
                        "--manifest",
                        "tests/fixtures/drive_manifest.json",
                    ]
                )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn(
            "--rebuild requires --apply",
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
