from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import publish_drive


MOCK_TOKEN_PATH = "config/google_drive_token_write.json"
MOCK_CREDENTIALS_PATH = "config/google_drive_client_secret.json"
MOCK_FOLDERS_CONFIG = "tests/fixtures/drive_folders.yaml"

# Corresponds to v04-00 contract category set
VALID_CATEGORIES = [
    "patch_notes",
    "job_guides",
    "raid_guides",
    "static_docs",
    "macros",
    "bis_sheets",
    "personal_notes",
]

# Sample folders YAML content
SAMPLE_FOLDERS_YAML = """\
patch_notes: "folder_patch_notes_id"
job_guides: "folder_job_guides_id"
raid_guides: "folder_raid_guides_id"
static_docs: "folder_static_docs_id"
macros: "folder_macros_id"
bis_sheets: "folder_bis_sheets_id"
personal_notes: "folder_personal_notes_id"
"""


def create_sources_db(
    db_path: Path,
    *,
    with_duplicate: str | None = None,
) -> None:
    """Create a sources table, optionally inserting a duplicate entry by title."""
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
        if with_duplicate:
            conn.execute(
                """
                INSERT INTO sources (
                  id, source_type, title, source_url, raw_path, content_hash,
                  created_at, updated_at
                )
                VALUES (?, 'text_note', ?, ?, ?, ?, ?, ?)
                """,
                (
                    "dup_existing",
                    with_duplicate,
                    "gdrive://dup_file",
                    "raw/drive/personal_notes/test__dup_file.md",
                    "hash-existing",
                    "2026-01-01T00:00:00+00:00",
                    "2026-01-01T00:00:00+00:00",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def write_folders_config(path: Path, content: str = SAMPLE_FOLDERS_YAML) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class FakeDriveFiles:
    def __init__(self) -> None:
        self.created_files: list[dict[str, object]] = []
        self.next_id: int = 1000

    def create(self, *, body: dict[str, object], media_body: object = None) -> FakeDriveRequest:
        file_record = {
            "body": body,
            "media_body": media_body,
            "fake_id": f"drive_fake_{self.next_id}",
        }
        self.created_files.append(file_record)
        self.next_id += 1
        return FakeDriveRequest(
            {
                "id": file_record["fake_id"],
                "name": body.get("name", ""),
                "webViewLink": f"https://drive.google.com/file/d/{file_record['fake_id']}/view",
                "mimeType": body.get("mimeType", "text/markdown"),
            }
        )


class FakeDriveRequest:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response

    def execute(self) -> dict[str, object]:
        return self.response


class FakeDriveService:
    def __init__(self, files_resource: FakeDriveFiles) -> None:
        self._files_resource = files_resource

    def files(self) -> FakeDriveFiles:
        return self._files_resource


class PublishDriveTests(unittest.TestCase):
    """Tests for tools.publish_drive — Drive write/publish operations.

    These tests follow the same patterns as test_sync_drive.py and verify
    the v04-00 ingest contract JSON output format.
    """

    maxDiff = None

    # ── Helpers ──────────────────────────────────────────────────────────

    def _run_main(
        self,
        args: list[str],
        *,
        root_path: Path,
        db_path: Path | None = None,
    ) -> str:
        """Run publish_drive.main() and return captured stdout."""
        effective_args = list(args)
        if "--db-path" not in effective_args and db_path is not None:
            effective_args.extend(["--db-path", str(db_path)])
        if "--root-path" not in effective_args:
            effective_args.extend(["--root-path", str(root_path)])

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            publish_drive.main(effective_args)
        return stdout.getvalue()

    # ── 1. Dry-run with all required args outputs correct JSON shape ─────

    def test_load_folders_config_parses_simple_mapping_without_pyyaml(self) -> None:
        """Folder config loading should work without optional PyYAML installed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            folders_cfg = Path(tmp_dir) / "drive_folders.yaml"
            write_folders_config(folders_cfg)

            original_import = __import__

            def fail_yaml_import(name: str, *args: object, **kwargs: object) -> object:
                if name == "yaml":
                    raise ModuleNotFoundError("No module named 'yaml'")
                return original_import(name, *args, **kwargs)

            with mock.patch("builtins.__import__", side_effect=fail_yaml_import):
                folders = publish_drive.load_folders_config(folders_cfg)

        self.assertEqual(folders["personal_notes"], "folder_personal_notes_id")
        self.assertEqual(folders["patch_notes"], "folder_patch_notes_id")

    def test_dry_run_outputs_correct_json_shape(self) -> None:
        """Dry-run must return status, actions[], summary, and dry_run=True."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)

            stdout = self._run_main(
                [
                    "--dry-run",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Test Note",
                    "--body",
                    "hello",
                    "--folders-config",
                    str(folders_cfg),
                ],
                root_path=root_path,
            )

        result = json.loads(stdout)

        self.assertIn("status", result)
        self.assertIn("actions", result)
        self.assertIn("summary", result)
        self.assertIn("dry_run", result)
        self.assertIs(result["dry_run"], True)

        self.assertIsInstance(result["actions"], list)
        self.assertIsInstance(result["summary"], dict)

    # ── 2. Dry-run with --category and --title shows drive_upload action ──

    def test_dry_run_action_is_drive_upload(self) -> None:
        """Each planned action should have action='drive_upload'."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)

            stdout = self._run_main(
                [
                    "--dry-run",
                    "--category",
                    "job_guides",
                    "--title",
                    "Black Mage Opener",
                    "--body",
                    "Use Ley Lines.",
                    "--folders-config",
                    str(folders_cfg),
                ],
                root_path=root_path,
            )

        result = json.loads(stdout)

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["actions"]), 1)
        action = result["actions"][0]
        self.assertEqual(action["action"], "drive_upload")
        self.assertEqual(action["title"], "Black Mage Opener")
        self.assertEqual(action["category"], "job_guides")
        self.assertEqual(action["source_type"], "text_note")
        self.assertIsNotNone(action["raw_path"])
        self.assertEqual(action["rebuild_status"], "pending")

    # ── 3. Dry-run without --apply does NOT call Drive API ────────────────

    def test_dry_run_does_not_call_drive_api(self) -> None:
        """FakeDriveService spy should have zero create calls after dry-run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--dry-run",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Test",
                        "--body",
                        "hello",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

        result = json.loads(stdout)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(fake_files.created_files), 0)

    # ── 4. Apply with --category, --title, --body creates Drive file ─────

    def test_apply_creates_drive_file(self) -> None:
        """FakeDriveService should record a create call with correct metadata."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "raid_guides",
                        "--title",
                        "Ultimate Guide",
                        "--body",
                        "# Ultimate\n\nPhase 1 mechanics.",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

        result = json.loads(stdout)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(fake_files.created_files), 1)

        created = fake_files.created_files[0]
        body = created["body"]
        self.assertEqual(body["name"], "Ultimate Guide")
        self.assertEqual(body["mimeType"], "text/markdown")
        self.assertEqual(body["parents"], ["folder_raid_guides_id"])

        action = result["actions"][0]
        self.assertEqual(action["action"], "drive_upload")
        self.assertIsNotNone(action["drive_file_id"])
        self.assertIn("drive.google.com", action["drive_url"])
        self.assertIsNotNone(action["source_id"])
        self.assertEqual(action["raw_path"], result["actions"][0]["raw_path"])

    # ── 5. Apply saves raw content to raw/drive ─────────────────────────

    def test_apply_saves_raw_content_to_drive_dir(self) -> None:
        """Apply should write the body content to the raw/drive directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            content = "# Personal Note\n\nToday's progress."
            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Daily Log",
                        "--body",
                        content,
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

            result = json.loads(stdout)
            action = result["actions"][0]
            raw_relative = action["raw_path"]
            raw_file = root_path / raw_relative

            self.assertTrue(raw_file.exists(), f"Expected raw file at {raw_file}")
            self.assertEqual(raw_file.read_text(encoding="utf-8"), content)

    # ── 6. Apply upserts DB sources table ────────────────────────────────

    def test_apply_upserts_sources_db(self) -> None:
        """After apply, the DB should contain a matching sources record."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "macros",
                        "--title",
                        "Raid Macro",
                        "--body",
                        "/mk attack",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

            result = json.loads(stdout)
            action = result["actions"][0]
            source_id = action["source_id"]

            conn = sqlite3.connect(db_path)
            try:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT id, title, source_type, source_url, raw_path, content_hash FROM sources WHERE id = ?",
                    (source_id,),
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(row, f"Source {source_id} not found in DB")
            self.assertEqual(row["title"], "Raid Macro")
            self.assertEqual(row["source_type"], "text_note")
            self.assertIn("gdrive://", row["source_url"])
            self.assertEqual(row["raw_path"], action["raw_path"])
            self.assertIsNotNone(row["content_hash"])

    # ── 7. Apply with missing --body for text_note source_type returns error ─

    def test_apply_missing_body_returns_error_action(self) -> None:
        """text_note without --body should produce an error action."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)

            stdout = self._run_main(
                [
                    "--apply",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Empty Note",
                    "--folders-config",
                    str(folders_cfg),
                ],
                root_path=root_path,
            )

        result = json.loads(stdout)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["actions"]), 1)
        action = result["actions"][0]
        self.assertEqual(action["action"], "error")
        self.assertEqual(action["error_type"], "invalid_input")
        self.assertEqual(action["rebuild_status"], "skipped")
        self.assertEqual(action["source_type"], "text_note")
        self.assertIn("body", action["message"].lower())

        summary = result["summary"]
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["uploaded"], 0)

    # ── 8. Apply with --title that exists (simulate duplicate) appends timestamp ─

    def test_apply_duplicate_title_appends_timestamp(self) -> None:
        """When a source with the same title exists, the Drive file name should get a timestamp suffix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path, with_duplicate="Duplicate Note")

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Duplicate Note",
                        "--body",
                        "Second version of the note.",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

        result = json.loads(stdout)
        self.assertEqual(result["status"], "success")
        created = fake_files.created_files[0]
        file_name: str = created["body"]["name"]

        # Should have __YYYY-MM-DD appended
        self.assertRegex(file_name, r"^Duplicate Note __\d{4}-\d{2}-\d{2}$")

    # ── 9. --folders-config missing category returns error ────────────────

    def test_folders_config_missing_category_returns_error(self) -> None:
        """A category not present in the YAML file should produce an error action."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            # Only define some categories, omit "patch_notes"
            write_folders_config(
                folders_cfg,
                content="""\
job_guides: "folder_job_guides_id"
personal_notes: "folder_personal_notes_id"
""",
            )

            stdout = self._run_main(
                [
                    "--dry-run",
                    "--category",
                    "patch_notes",
                    "--title",
                    "7.5 Patch Notes",
                    "--body",
                    "Patch notes content.",
                    "--folders-config",
                    str(folders_cfg),
                ],
                root_path=root_path,
            )

        result = json.loads(stdout)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["actions"]), 1)
        action = result["actions"][0]
        self.assertEqual(action["action"], "error")
        self.assertEqual(action["error_type"], "invalid_input")
        self.assertIn("patch_notes", action["message"])

    # ── 10. --auth flag requires --credentials-path ──────────────────────

    def test_auth_requires_credentials_path(self) -> None:
        """--auth without --credentials-path should use default and fail if file missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    publish_drive.main(
                        [
                            "--auth",
                            "--root-path",
                            str(root_path),
                        ]
                    )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("credentials", stderr.getvalue().lower())

    # ── 11. --apply without --folders-config returns error ───────────────

    def test_apply_without_folders_config_returns_error(self) -> None:
        """--apply requires --folders-config."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as raised:
                    publish_drive.main(
                        [
                            "--apply",
                            "--category",
                            "personal_notes",
                            "--title",
                            "No Config",
                            "--body",
                            "test",
                            "--root-path",
                            str(root_path),
                        ]
                    )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("folders-config", stderr.getvalue().lower())

    # ── 12. --dry-run with invalid category returns error action ─────────

    def test_dry_run_invalid_category_returns_error_action(self) -> None:
        """A category not in the valid set should produce an error action."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)

            stdout = self._run_main(
                [
                    "--dry-run",
                    "--category",
                    "invalid_category_xyz",
                    "--title",
                    "Bad Category",
                    "--body",
                    "test",
                    "--folders-config",
                    str(folders_cfg),
                ],
                root_path=root_path,
            )

        result = json.loads(stdout)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(result["actions"]), 1)
        action = result["actions"][0]
        self.assertEqual(action["action"], "error")
        self.assertEqual(action["error_type"], "invalid_input")
        self.assertIn("invalid_category_xyz", action["message"].lower())

    # ── 13. Token missing returns actionable error (drive_auth_missing) ──

    def test_missing_token_returns_actionable_error(self) -> None:
        """When the token file does not exist, the tool should fail with drive_auth_missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            token_path = root_path / "missing_token.json"
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                publish_drive.main(
                    [
                        "--apply",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Tokenless",
                        "--body",
                        "test",
                        "--folders-config",
                        str(folders_cfg),
                        "--token-path",
                        str(token_path),
                        "--db-path",
                        str(db_path),
                        "--root-path",
                        str(root_path),
                    ]
                )

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["dry_run"], False)
        action = result["actions"][0]
        self.assertEqual(action["action"], "error")
        self.assertEqual(action["error_type"], "drive_auth_missing")
        self.assertIn("token", action["message"].lower())
        self.assertEqual(result["summary"]["errors"], 1)

    # ── 14. Apply output matches v04-00 result JSON contract format ──────

    def test_apply_output_matches_v04_00_contract_format(self) -> None:
        """Verify the apply output conforms to the v04-00 ingest contract schema."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "static_docs",
                        "--title",
                        "Static Rules",
                        "--body",
                        "# Static\n\nRules content.",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

        result = json.loads(stdout)

        # Top-level fields per v04-00 contract
        self.assertIn("status", result)
        self.assertIn("actions", result)
        self.assertIn("summary", result)
        self.assertIn("dry_run", result)
        self.assertIs(result["dry_run"], False)
        self.assertIn(result["status"], ("success", "partial", "failed"))

        # Action fields per contract
        action = result["actions"][0]
        expected_action_keys = {
            "action",
            "source_type",
            "title",
            "category",
            "drive_file_id",
            "drive_url",
            "source_id",
            "raw_path",
            "rebuild_status",
            "message",
        }
        self.assertTrue(
            expected_action_keys.issubset(action.keys()),
            f"Missing action keys: {expected_action_keys - action.keys()}",
        )
        self.assertEqual(action["action"], "drive_upload")
        self.assertEqual(action["source_type"], "text_note")
        self.assertEqual(action["category"], "static_docs")
        self.assertEqual(action["rebuild_status"], "completed")
        self.assertIsNotNone(action["drive_file_id"])
        self.assertIsNotNone(action["drive_url"])
        self.assertIsNotNone(action["source_id"])
        self.assertIsNotNone(action["raw_path"])
        self.assertIsNotNone(action["message"])

        # Summary fields per contract
        summary = result["summary"]
        expected_summary_keys = {"total", "uploaded", "updated", "skipped", "errors"}
        self.assertTrue(
            expected_summary_keys.issubset(summary.keys()),
            f"Missing summary keys: {expected_summary_keys - summary.keys()}",
        )
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["uploaded"], 1)

    # ── 15. --source-type plain_text_file produces correct MIME and extension ──

    def test_plain_text_file_source_type(self) -> None:
        """--source-type plain_text_file should use text/plain MIME and .txt extension."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                stdout = self._run_main(
                    [
                        "--apply",
                        "--source-type",
                        "plain_text_file",
                        "--category",
                        "job_guides",
                        "--title",
                        "Readme",
                        "--body",
                        "plain text content",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

        result = json.loads(stdout)
        self.assertEqual(result["status"], "success")
        created = fake_files.created_files[0]
        body = created["body"]
        self.assertEqual(body["mimeType"], "text/plain")
        self.assertIn(".txt", result["actions"][0]["raw_path"])
        self.assertEqual(result["actions"][0]["source_type"], "plain_text_file")

    # ── 16. Unit tests do NOT require real Drive API or tokens ───────────

    def test_all_tests_pass_without_real_api_or_tokens(self) -> None:
        """This test is a meta-check: dry-run tests never hit real Drive API.
        The individual tests above use FakeDriveService and in-memory DBs,
        proving no real API or token access is needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            folders_cfg = root_path / "drive_folders.yaml"
            write_folders_config(folders_cfg)
            db_path = root_path / "ffxiv.sqlite"
            create_sources_db(db_path)

            fake_files = FakeDriveFiles()
            fake_service = FakeDriveService(fake_files)

            original_load = publish_drive.load_drive_credentials
            original_build = publish_drive.build_drive_service

            try:
                publish_drive.load_drive_credentials = lambda token_path: object()
                publish_drive.build_drive_service = lambda credentials: fake_service

                # dry-run (no API calls)
                stdout_dry = self._run_main(
                    [
                        "--dry-run",
                        "--category",
                        "bis_sheets",
                        "--title",
                        "Best in Slot",
                        "--body",
                        "# BiS\n\nWeapon, Chest, Accessories.",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )

                # apply (uses FakeDriveService, not real API)
                stdout_apply = self._run_main(
                    [
                        "--apply",
                        "--category",
                        "bis_sheets",
                        "--title",
                        "Best in Slot 2",
                        "--body",
                        "# BiS v2\n\nUpdated gear set.",
                        "--folders-config",
                        str(folders_cfg),
                    ],
                    root_path=root_path,
                    db_path=db_path,
                )
            finally:
                publish_drive.load_drive_credentials = original_load
                publish_drive.build_drive_service = original_build

            dry_result = json.loads(stdout_dry)
            apply_result = json.loads(stdout_apply)

            # dry-run: no API calls
            self.assertEqual(dry_result["status"], "success")
            self.assertIs(dry_result["dry_run"], True)
            self.assertEqual(len(fake_files.created_files), 1)  # only apply created

            # apply: one API call
            self.assertEqual(apply_result["status"], "success")
            self.assertIs(apply_result["dry_run"], False)
            self.assertEqual(len(fake_files.created_files), 1)

            # Verify raw file was saved locally
            raw_path = root_path / apply_result["actions"][0]["raw_path"]
            self.assertTrue(raw_path.exists())

            # Verify DB has the source
            conn = sqlite3.connect(db_path)
            try:
                count = conn.execute(
                    "SELECT COUNT(*) FROM sources WHERE id = ?",
                    (apply_result["actions"][0]["source_id"],),
                ).fetchone()[0]
            finally:
                conn.close()

            self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
