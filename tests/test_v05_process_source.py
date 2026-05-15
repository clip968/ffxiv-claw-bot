from __future__ import annotations

import contextlib
import importlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


def require_process_source_main(test: unittest.TestCase) -> Callable[[list[str]], None]:
    try:
        module = importlib.import_module("tools.process_source")
    except ModuleNotFoundError as exc:
        if exc.name == "tools.process_source":
            test.fail("Expected tools.process_source.main for v05 source processing")
        raise

    main = getattr(module, "main", None)
    if not callable(main):
        test.fail("Expected callable tools.process_source.main")
    return main


def run_process_source(test: unittest.TestCase, argv: list[str]) -> dict[str, Any]:
    main = require_process_source_main(test)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(argv)
    return json.loads(stdout.getvalue())


class V05OpenClawSkillDocTests(unittest.TestCase):
    def test_ffxiv_source_processing_skill_doc_defines_openclaw_contract(self) -> None:
        skill_path = Path("docs/skills/ffxiv-source-processing.md")

        self.assertTrue(
            skill_path.exists(),
            "v05-02 must document the OpenClaw Source Processing Skill",
        )

        text = skill_path.read_text(encoding="utf-8")
        required_fragments = [
            "ffxiv-source-processing",
            "python tools/process_source.py",
            "source_type=url",
            "source_type=text_note",
            "source_type=markdown_file",
            "source_type=plain_text_file",
            "Ambiguity",
            "notion_update",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, text)


class V05ProcessSourceSkeletonTests(unittest.TestCase):
    def test_process_missing_body_returns_error(self) -> None:
        result = run_process_source(
            self,
            [
                "--dry-run",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "Missing body note",
            ],
        )

        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["source_id"])
        self.assertEqual(result["source_type"], "text_note")
        self.assertEqual(result["category"], "personal_notes")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertEqual(result["actions"][0]["name"], "validate_request")
        self.assertEqual(result["actions"][0]["status"], "error")
        self.assertIn("--body", result["actions"][0]["error"])
        self.assertIn("next_action", result["summary"])

    def test_process_missing_url_returns_error(self) -> None:
        result = run_process_source(
            self,
            [
                "--dry-run",
                "--source-type",
                "url",
                "--category",
                "patch_notes",
                "--title",
                "Missing URL",
            ],
        )

        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["source_id"])
        self.assertEqual(result["source_type"], "url")
        self.assertEqual(result["category"], "patch_notes")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertIn("--url", result["actions"][0]["error"])

    def test_process_missing_local_path_returns_error(self) -> None:
        for source_type in ("markdown_file", "plain_text_file"):
            with self.subTest(source_type=source_type):
                result = run_process_source(
                    self,
                    [
                        "--dry-run",
                        "--source-type",
                        source_type,
                        "--category",
                        "raid_guides",
                        "--title",
                        "Missing file",
                    ],
                )

                self.assertEqual(result["status"], "error")
                self.assertEqual(result["source_type"], source_type)
                self.assertEqual(result["graph_status"], "skipped")
                self.assertIn("--local-path", result["actions"][0]["error"])

    def test_process_file_not_found_returns_error(self) -> None:
        result = run_process_source(
            self,
            [
                "--dry-run",
                "--source-type",
                "markdown_file",
                "--category",
                "raid_guides",
                "--title",
                "Missing file",
                "--local-path",
                "/tmp/ffxiv-claw-bot-missing-file.md",
            ],
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertIn("does not exist", result["actions"][0]["error"])

    def test_process_dry_run_returns_skipped_status_and_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_root = Path(tmp_dir) / "storage"
            db_path = Path(tmp_dir) / "ffxiv.sqlite"

            result = run_process_source(
                self,
                [
                    "--dry-run",
                    "--source-type",
                    "text_note",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Dry run note",
                    "--body",
                    "This should not be persisted.",
                    "--storage-root",
                    str(storage_root),
                    "--db-path",
                    str(db_path),
                ],
            )

        expected_keys = {
            "status",
            "dry_run",
            "source_id",
            "source_type",
            "category",
            "title",
            "local_source_path",
            "raw_path",
            "wiki_path",
            "graph_status",
            "actions",
            "notion_update",
            "summary",
        }
        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertEqual(result["status"], "skipped")
        self.assertIs(result["dry_run"], True)
        self.assertIsNone(result["source_id"])
        self.assertEqual(result["source_type"], "text_note")
        self.assertEqual(result["category"], "personal_notes")
        self.assertEqual(result["title"], "Dry run note")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertEqual(
            result["actions"],
            [
                {"name": "validate_request", "status": "ok"},
                {"name": "ingest_local", "status": "skipped", "reason": "dry_run"},
                {"name": "rebuild", "status": "skipped", "reason": "dry_run"},
            ],
        )
        self.assertEqual(result["notion_update"], {})
        self.assertIn("No files or database rows were written", result["summary"]["message"])
        self.assertFalse(storage_root.exists(), "dry-run must not create storage directories")
        self.assertFalse(db_path.exists(), "dry-run must not create or modify SQLite DB")

    def test_process_dry_run_cli_script_execution_prints_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "tools/process_source.py",
                "--dry-run",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "CLI dry run",
                "--body",
                "hello",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["actions"][0], {"name": "validate_request", "status": "ok"})

    def test_process_apply_and_dry_run_mutual_exclusion(self) -> None:
        result = run_process_source(
            self,
            [
                "--apply",
                "--dry-run",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "Bad mode",
                "--body",
                "hello",
            ],
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertIn("--apply and --dry-run cannot be used together", result["actions"][0]["error"])
