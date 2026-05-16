from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from tests.test_v06_extractors import write_sample_xlsx


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


def ensure_sources_schema(db_path: Path) -> None:
    from tools.init_db import SCHEMA

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def run_process_source_with_temp_root(
    test: unittest.TestCase,
    argv: list[str],
    root_path: Path,
) -> dict[str, Any]:
    module = importlib.import_module("tools.process_source")
    old_root = getattr(module, "ROOT")
    setattr(module, "ROOT", root_path)
    try:
        return run_process_source(test, argv)
    finally:
        setattr(module, "ROOT", old_root)


class ProcessSourceTempCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp_dir.name)
        self.storage_root = self.tmp / "storage"
        self.storage_root.mkdir(parents=True)
        self.repo_root = self.tmp / "repo"
        self.db_path = self.tmp / "ffxiv.sqlite"
        ensure_sources_schema(self.db_path)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def run_process(self, argv: list[str]) -> dict[str, Any]:
        return run_process_source_with_temp_root(
            self,
            [
                *argv,
                "--storage-root",
                str(self.storage_root),
                "--db-path",
                str(self.db_path),
            ],
            self.repo_root,
        )


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


class V05ProcessSourceLocalIntegrationTests(ProcessSourceTempCase):
    def test_process_text_note_ok(self) -> None:
        body = "Use Reprisal before the tank buster."

        result = self.run_process(
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
            ],
        )

        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], False)
        self.assertTrue(result["source_id"].startswith("local_"))
        self.assertEqual(
            result["local_source_path"],
            "sources/personal_notes/raid_mitigation_note.md",
        )
        self.assertEqual(result["canonical_path"], result["local_source_path"])
        self.assertEqual(
            result["content_hash"],
            hashlib.sha256(body.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(result["graph_status"], "built")
        self.assertEqual(
            result["wiki_path"],
            f"wiki/source_summaries/{result['source_id']}.md",
        )
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("ingest_local", "ok"),
                ("compile_wiki", "ok"),
                ("index_fts", "ok"),
                ("build_graph", "ok"),
                ("build_notion_payload", "ok"),
            ],
        )
        self.assertEqual(
            (self.storage_root / result["local_source_path"]).read_text(encoding="utf-8"),
            body,
        )
        self.assertEqual(
            (self.repo_root / result["raw_path"]).read_text(encoding="utf-8"),
            body,
        )
        self.assertIn(
            body,
            (self.repo_root / result["wiki_path"]).read_text(encoding="utf-8"),
        )
        conn = sqlite3.connect(str(self.db_path))
        try:
            fts_row = conn.execute(
                "SELECT title, body FROM wiki_fts WHERE page_id = ?",
                (f"wiki_{result['source_id']}",),
            ).fetchone()
            graph_node_count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            graph_edge_count = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
        finally:
            conn.close()
        self.assertIsNotNone(fts_row)
        self.assertEqual(fts_row[0], "Raid mitigation note")
        self.assertIn("Use Reprisal", fts_row[1])
        self.assertGreaterEqual(graph_node_count, 2)
        self.assertGreaterEqual(graph_edge_count, 1)
        self.assertTrue((self.repo_root / "graph" / "nodes.json").exists())
        self.assertTrue((self.repo_root / "graph" / "edges.json").exists())

    def test_process_duplicate_source_upserts_existing_source_id(self) -> None:
        body_v1 = "Use Reprisal before the tank buster."
        body_v2 = "Use Addle before the raidwide, then Reprisal."
        base_args = [
            "--apply",
            "--source-type",
            "text_note",
            "--category",
            "personal_notes",
            "--title",
            "Raid mitigation note",
        ]

        result_v1 = self.run_process([*base_args, "--body", body_v1])
        result_v2 = self.run_process([*base_args, "--body", body_v2])

        self.assertEqual(result_v1["status"], "ok")
        self.assertEqual(result_v2["status"], "ok")
        self.assertEqual(result_v2["source_id"], result_v1["source_id"])
        self.assertEqual(result_v2["canonical_path"], result_v1["canonical_path"])
        self.assertEqual(
            result_v2["content_hash"],
            hashlib.sha256(body_v2.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            (self.storage_root / result_v2["local_source_path"]).read_text(encoding="utf-8"),
            body_v2,
        )
        self.assertEqual(
            (self.repo_root / result_v2["raw_path"]).read_text(encoding="utf-8"),
            body_v2,
        )

        conn = sqlite3.connect(str(self.db_path))
        try:
            row_count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            row = conn.execute(
                "SELECT id, content_hash, raw_path FROM sources WHERE id = ?",
                (result_v1["source_id"],),
            ).fetchone()
        finally:
            conn.close()

        self.assertEqual(row_count, 1)
        self.assertIsNotNone(row)
        self.assertEqual(row[0], result_v1["source_id"])
        self.assertEqual(row[1], result_v2["content_hash"])
        self.assertEqual(row[2], result_v2["raw_path"])

    def test_process_markdown_file_ok(self) -> None:
        source_file = self.tmp / "guide.md"
        body = "# Raid Guide\n\nStack middle for towers.\n"
        source_file.write_text(body, encoding="utf-8")

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "markdown_file",
                "--category",
                "raid_guides",
                "--title",
                "Tower Guide",
                "--local-path",
                str(source_file),
            ],
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["graph_status"], "built")
        self.assertTrue(result["wiki_path"].startswith("wiki/source_summaries/"))
        self.assertTrue(result["source_id"].startswith("local_"))
        self.assertEqual(result["local_source_path"], "sources/raid_guides/tower_guide.md")
        self.assertEqual(
            (self.storage_root / result["local_source_path"]).read_text(encoding="utf-8"),
            body,
        )
        self.assertEqual(
            (self.repo_root / result["raw_path"]).read_text(encoding="utf-8"),
            body,
        )

    def test_process_plain_text_file_ok(self) -> None:
        source_file = self.tmp / "macro.txt"
        body = "/p Spread then stack\n"
        source_file.write_text(body, encoding="utf-8")

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "plain_text_file",
                "--category",
                "macros",
                "--title",
                "Spread Stack Macro",
                "--local-path",
                str(source_file),
            ],
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["graph_status"], "built")
        self.assertTrue(result["wiki_path"].startswith("wiki/source_summaries/"))
        self.assertTrue(result["source_id"].startswith("local_"))
        self.assertEqual(
            result["local_source_path"],
            "sources/macros/spread_stack_macro.md",
        )
        self.assertEqual(
            (self.storage_root / result["local_source_path"]).read_text(encoding="utf-8"),
            body,
        )
        self.assertEqual(
            (self.repo_root / result["raw_path"]).read_text(encoding="utf-8"),
            body,
        )

    def test_process_ingest_error_skips_rebuild(self) -> None:
        missing_storage_root = self.tmp / "missing-storage"

        result = run_process_source_with_temp_root(
            self,
            [
                "--apply",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "Storage failure",
                "--body",
                "hello",
                "--storage-root",
                str(missing_storage_root),
                "--db-path",
                str(self.db_path),
            ],
            self.repo_root,
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("ingest_local", "error"),
                ("rebuild", "skipped"),
            ],
        )
        self.assertIn("Storage root", result["actions"][1]["error"])
        self.assertEqual(result["actions"][2]["reason"], "upstream_ingest_error")


class V06ProcessSourceExtractorIntegrationTests(ProcessSourceTempCase):
    def test_process_source_uses_extractor_for_local_file_source(self) -> None:
        source_file = self.tmp / "guide.md"
        source_file.write_text("# Patch Notes\n\n## Gunbreaker\n- Continuation adjusted.\n", encoding="utf-8")

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "markdown_file",
                "--category",
                "patch_notes",
                "--title",
                "Patch Notes",
                "--local-path",
                str(source_file),
            ],
        )

        self.assertEqual(result["status"], "ok")
        extract_action = next(action for action in result["actions"] if action["name"] == "extract")
        self.assertEqual(extract_action["status"], "ok")
        self.assertEqual(extract_action["extractor"], "markdown")
        self.assertEqual(result["extract_metadata"]["extractor_name"], "markdown")
        self.assertIn(
            "Continuation adjusted",
            (self.repo_root / result["wiki_path"]).read_text(encoding="utf-8"),
        )

    def test_process_source_preserves_extracted_metadata(self) -> None:
        source_file = self.tmp / "drops.xlsx"
        write_sample_xlsx(source_file)

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "binary_attachment",
                "--category",
                "bis_sheets",
                "--title",
                "Drop Table",
                "--local-path",
                str(source_file),
            ],
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["extract_metadata"]["extractor_name"], "xlsx")
        self.assertEqual(result["extract_metadata"]["sheet_count"], 3)
        self.assertEqual(result["extract_metadata"]["empty_sheets"], ["Empty Sheet"])
        self.assertIn(
            "Hypostatic Gear",
            (self.storage_root / result["local_source_path"]).read_text(encoding="utf-8"),
        )

    def test_process_source_records_extract_error_for_unsupported_file(self) -> None:
        source_file = self.tmp / "image.png"
        source_file.write_bytes(b"not really an image")

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "binary_attachment",
                "--category",
                "bis_sheets",
                "--title",
                "Image Source",
                "--local-path",
                str(source_file),
            ],
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_stage"], "extract")
        self.assertEqual(result["graph_status"], "skipped")
        self.assertIn("Unsupported source extension: .png", result["last_error"])
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("extract", "error"),
                ("ingest_local", "skipped"),
                ("rebuild", "skipped"),
            ],
        )

    def test_process_source_text_note_body_path_unchanged(self) -> None:
        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "Body Only",
                "--body",
                "No extractor should run.",
            ],
        )

        self.assertEqual(result["status"], "ok")
        self.assertNotIn("extract", [action["name"] for action in result["actions"]])
        self.assertEqual(result["extract_metadata"], {})


class V05ProcessSourceUrlIntegrationTests(ProcessSourceTempCase):
    def test_process_lodestone_url_records_lodestone_extractor_action(self) -> None:
        url = "https://na.finalfantasyxiv.com/lodestone/topics/detail/patch-7-5"
        fetched_body = "Patch 7.5 Notes\nNew main scenario quests have been added."
        module = importlib.import_module("tools.process_source")

        with patch.object(module, "fetch_single_url") as fetch_single_url:
            fetch_single_url.return_value = {
                "url": url,
                "content_type": "text/html; charset=utf-8",
                "title": "Patch 7.5 Notes",
                "body": fetched_body,
                "extractor": "lodestone",
                "raw_html": "<html>raw source must not enter notion_update</html>",
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "url",
                    "--category",
                    "patch_notes",
                    "--url",
                    url,
                ],
            )

        self.assertEqual(result["status"], "ok")
        fetch_action = next(
            action for action in result["actions"] if action["name"] == "fetch_url"
        )
        self.assertEqual(fetch_action["status"], "ok")
        self.assertEqual(fetch_action["url"], url)
        self.assertEqual(fetch_action["content_type"], "text/html; charset=utf-8")
        self.assertEqual(fetch_action["extractor"], "lodestone")

        payload = result["notion_update"]
        payload_text = json.dumps(payload, ensure_ascii=False)
        for forbidden_field in (
            "body",
            "raw_body",
            "raw_html",
            "attachments",
            "binary",
            "binary_data",
        ):
            self.assertNotIn(forbidden_field, payload)
        self.assertNotIn(fetched_body, payload_text)
        self.assertNotIn("raw source must not enter notion_update", payload_text)

    def test_process_url_ok_fetches_single_url_and_ingests_local_storage(self) -> None:
        url = "https://example.com/ffxiv/patch-7-5"
        fetched_body = "Patch 7.5 Notes\nNew raid adjustments are available."
        module = importlib.import_module("tools.process_source")

        with patch.object(module, "fetch_single_url") as fetch_single_url:
            fetch_single_url.return_value = {
                "url": url,
                "content_type": "text/html; charset=utf-8",
                "title": "Patch 7.5 Notes",
                "body": fetched_body,
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "url",
                    "--category",
                    "patch_notes",
                    "--url",
                    url,
                ],
            )

        fetch_single_url.assert_called_once_with(url)
        self.assertEqual(result["status"], "ok")
        self.assertIs(result["dry_run"], False)
        self.assertTrue(result["source_id"].startswith("local_"))
        self.assertEqual(result["source_type"], "url")
        self.assertEqual(result["category"], "patch_notes")
        self.assertEqual(result["title"], "Patch 7.5 Notes")
        self.assertEqual(
            result["local_source_path"],
            "sources/patch_notes/patch_7.5_notes.md",
        )
        self.assertEqual(
            result["content_hash"],
            hashlib.sha256(fetched_body.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(result["graph_status"], "built")
        self.assertTrue(result["wiki_path"].startswith("wiki/source_summaries/"))
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("fetch_url", "ok"),
                ("ingest_local", "ok"),
                ("compile_wiki", "ok"),
                ("index_fts", "ok"),
                ("build_graph", "ok"),
                ("build_notion_payload", "ok"),
            ],
        )
        self.assertEqual(result["actions"][1]["url"], url)
        self.assertEqual(
            (self.storage_root / result["local_source_path"]).read_text(encoding="utf-8"),
            fetched_body,
        )
        self.assertEqual(
            (self.repo_root / result["raw_path"]).read_text(encoding="utf-8"),
            fetched_body,
        )

    def test_process_url_prefers_cli_title_over_fetched_title(self) -> None:
        url = "https://example.com/ffxiv/patch"
        module = importlib.import_module("tools.process_source")

        with patch.object(module, "fetch_single_url") as fetch_single_url:
            fetch_single_url.return_value = {
                "url": url,
                "content_type": "text/html",
                "title": "Fetched HTML Title",
                "body": "Fetched page body",
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "url",
                    "--category",
                    "patch_notes",
                    "--title",
                    "Maintainer Provided Patch Title",
                    "--url",
                    url,
                ],
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["title"], "Maintainer Provided Patch Title")
        self.assertEqual(
            result["local_source_path"],
            "sources/patch_notes/maintainer_provided_patch_title.md",
        )

    def test_process_url_fetch_fails_returns_error_without_ingest(self) -> None:
        url = "https://example.com/missing"
        module = importlib.import_module("tools.process_source")

        with patch.object(module, "fetch_single_url") as fetch_single_url:
            fetch_single_url.side_effect = RuntimeError("404 Client Error")

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "url",
                    "--category",
                    "patch_notes",
                    "--url",
                    url,
                ],
            )

        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["source_id"])
        self.assertEqual(result["graph_status"], "skipped")
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("fetch_url", "error"),
                ("ingest_local", "skipped"),
                ("rebuild", "skipped"),
            ],
        )
        self.assertIn("404 Client Error", result["actions"][1]["error"])
        self.assertEqual(result["actions"][2]["reason"], "upstream_fetch_error")
        self.assertEqual(result["actions"][3]["reason"], "upstream_fetch_error")
        self.assertFalse(any((self.storage_root / "sources").rglob("*")))

        conn = sqlite3.connect(str(self.db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 0)


class V05ProcessSourceRebuildIntegrationTests(ProcessSourceTempCase):
    def test_process_rebuild_error_returns_partial(self) -> None:
        local_rebuild = importlib.import_module("tools.local_rebuild")

        with patch.object(local_rebuild, "rebuild_after_ingest") as rebuild:
            rebuild.return_value = {
                "status": "partial",
                "source_id": "local_placeholder",
                "wiki_path": None,
                "actions": [
                    {
                        "action": "compile_wiki",
                        "status": "failed",
                        "message": "Source not found",
                    },
                    {
                        "action": "index_fts",
                        "status": "skipped",
                        "message": "Skipped due to compile_wiki failure",
                    },
                    {
                        "action": "build_graph",
                        "status": "ok",
                        "message": "Graph built",
                    },
                ],
                "summary": {"total": 3, "ok": 1, "partial": 0, "errors": 1, "skipped": 1},
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "text_note",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Rebuild failure note",
                    "--body",
                    "This source should still be saved.",
                ],
            )

        rebuild.assert_called_once()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["graph_status"], "built")
        self.assertIsNone(result["wiki_path"])
        self.assertEqual(
            [(action["name"], action["status"]) for action in result["actions"]],
            [
                ("validate_request", "ok"),
                ("ingest_local", "ok"),
                ("compile_wiki", "error"),
                ("index_fts", "skipped"),
                ("build_graph", "ok"),
                ("build_notion_payload", "ok"),
            ],
        )
        self.assertIn("Source not found", result["last_error"])

    def test_process_rebuild_partial_skips_derived_wiki_hook(self) -> None:
        local_rebuild = importlib.import_module("tools.local_rebuild")
        process_source = importlib.import_module("tools.process_source")

        with patch.object(local_rebuild, "rebuild_after_ingest") as rebuild:
            rebuild.return_value = {
                "status": "partial",
                "source_id": "local_placeholder",
                "wiki_path": None,
                "actions": [
                    {
                        "action": "compile_wiki",
                        "status": "failed",
                        "message": "Source summary failed",
                    },
                ],
                "summary": {"total": 1, "ok": 0, "partial": 0, "errors": 1, "skipped": 0},
            }
            with patch.object(process_source.generate_derived_wiki, "run") as run_derived:
                result = self.run_process(
                    [
                        "--apply",
                        "--source-type",
                        "text_note",
                        "--category",
                        "personal_notes",
                        "--title",
                        "Partial rebuild hook guard",
                        "--body",
                        "Derived wiki should not run after partial rebuild.",
                        "--build-derived-wiki",
                    ],
                )

        run_derived.assert_not_called()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["derived_wiki"]["status"], "skipped")
        self.assertEqual(result["derived_wiki"]["reason"], "upstream_source_not_ok")

    def test_process_graph_failure_sets_graph_status_failed(self) -> None:
        local_rebuild = importlib.import_module("tools.local_rebuild")

        with patch.object(local_rebuild, "rebuild_after_ingest") as rebuild:
            rebuild.return_value = {
                "status": "partial",
                "source_id": "local_placeholder",
                "wiki_path": "wiki/source_summaries/local_placeholder.md",
                "actions": [
                    {
                        "action": "compile_wiki",
                        "status": "ok",
                        "wiki_path": "wiki/source_summaries/local_placeholder.md",
                    },
                    {"action": "index_fts", "status": "ok"},
                    {
                        "action": "build_graph",
                        "status": "failed",
                        "message": "graph table missing",
                    },
                ],
                "summary": {"total": 3, "ok": 2, "partial": 0, "errors": 1, "skipped": 0},
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "text_note",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Graph failure note",
                    "--body",
                    "Wiki should remain usable if graph fails.",
                ],
            )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["graph_status"], "failed")
        self.assertEqual(result["wiki_path"], "wiki/source_summaries/local_placeholder.md")
        self.assertIn("graph table missing", result["last_error"])
        self.assertEqual(result["actions"][-2]["name"], "build_graph")
        self.assertEqual(result["actions"][-2]["status"], "error")
        self.assertEqual(result["actions"][-1]["name"], "build_notion_payload")
        self.assertEqual(result["actions"][-1]["status"], "ok")


class V05ProcessSourceNotionPayloadIntegrationTests(ProcessSourceTempCase):
    def test_process_notion_payload_excludes_body(self) -> None:
        body = "Sensitive strategy body that must stay out of Notion."

        result = self.run_process(
            [
                "--apply",
                "--source-type",
                "text_note",
                "--category",
                "personal_notes",
                "--title",
                "Notion payload body exclusion",
                "--body",
                body,
            ],
        )

        payload = result["notion_update"]
        self.assertEqual(result["status"], "ok")
        self.assertIn("Status", payload)
        self.assertIn("Graph Status", payload)
        self.assertEqual(payload["Status"], "Graph Built")
        self.assertEqual(payload["Graph Status"], "Built")
        self.assertEqual(payload["Source ID"], result["source_id"])
        self.assertEqual(payload["Local Source Path"], result["local_source_path"])
        self.assertEqual(payload["Wiki Path"], result["wiki_path"])
        self.assertIn("Last Processed", payload)
        self.assertNotIn("body", payload)
        self.assertNotIn("raw_html", payload)
        self.assertNotIn("attachments", payload)
        self.assertNotIn(body, json.dumps(payload, ensure_ascii=False))

    def test_process_notion_payload_ok_graph_pending(self) -> None:
        local_rebuild = importlib.import_module("tools.local_rebuild")

        with patch.object(local_rebuild, "rebuild_after_ingest") as rebuild:
            rebuild.return_value = {
                "status": "ok",
                "source_id": "local_placeholder",
                "wiki_path": "wiki/source_summaries/local_placeholder.md",
                "actions": [
                    {
                        "action": "compile_wiki",
                        "status": "ok",
                        "wiki_path": "wiki/source_summaries/local_placeholder.md",
                    },
                    {"action": "index_fts", "status": "ok"},
                ],
                "summary": {"total": 2, "ok": 2, "partial": 0, "errors": 0, "skipped": 0},
            }

            result = self.run_process(
                [
                    "--apply",
                    "--source-type",
                    "text_note",
                    "--category",
                    "personal_notes",
                    "--title",
                    "Pending graph note",
                    "--body",
                    "Graph can be pending for this payload.",
                ],
            )

        payload = result["notion_update"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["graph_status"], "pending")
        self.assertIn("Status", payload)
        self.assertIn("Graph Status", payload)
        self.assertEqual(payload["Status"], "Indexed")
        self.assertEqual(payload["Graph Status"], "Pending")


class V05ProcessSourceRunbookTests(unittest.TestCase):
    def _process_source_runbook(self) -> str:
        return Path("docs/runbooks/process-source.md").read_text(encoding="utf-8")

    def test_process_source_runbook_documents_completed_v05_workflow(self) -> None:
        runbook = self._process_source_runbook()

        required_fragments = [
            "wiki/FTS/graph rebuild",
            "build_notion_payload",
            "notion_update",
            "Last Processed",
            "Graph Built",
            "python scripts/finish_task.py",
            "No crawler",
            "No scheduler",
            "Notion API",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, runbook)

        self.assertNotIn("v05-06 rebuild execution is not implemented", runbook)
        self.assertNotIn("v05-07 Notion success payload generation is not implemented", runbook)

    def test_process_source_runbook_names_process_source_as_official_entrypoint(self) -> None:
        runbook = self._process_source_runbook()

        self.assertIn("official source processing entrypoint", runbook)
        self.assertIn("tools/process_source.py", runbook)
        self.assertIn("normal OpenClaw source processing", runbook)

    def test_process_source_runbook_warns_against_ingest_local_body_path_misuse(self) -> None:
        runbook = self._process_source_runbook()

        self.assertIn('python tools/ingest_local.py', runbook)
        self.assertIn('--body "/mnt/d/ffixiv-bot-storage/incoming/patch-7-5.md"', runbook)
        self.assertIn("stores the path string itself", runbook)
        self.assertIn("not the file contents", runbook)
        self.assertIn("already-read body text", runbook)

    def test_process_source_runbook_documents_local_rebuild_library_only(self) -> None:
        runbook = self._process_source_runbook()

        self.assertIn("tools/local_rebuild.py", runbook)
        self.assertIn("library-only", runbook)
        self.assertIn("Do not run `python tools/local_rebuild.py`", runbook)
        self.assertIn("local_rebuild.rebuild_after_ingest()", runbook)

    def test_process_source_runbook_documents_status_notification_payload_only(self) -> None:
        runbook = self._process_source_runbook()

        self.assertIn("tools/status_notification.py", runbook)
        self.assertIn("payload-builder-only", runbook)
        self.assertIn("not a Notion write CLI", runbook)
        self.assertIn("status_notification.build_notion_status_update()", runbook)

    def test_process_source_runbook_documents_notion_update_not_auto_applied(self) -> None:
        runbook = self._process_source_runbook()

        self.assertIn('result["notion_update"]', runbook)
        self.assertIn("process_source.py itself does not call the Notion API", runbook)
        self.assertIn("OpenClaw may apply it", runbook)
        self.assertIn("not already applied", runbook)
