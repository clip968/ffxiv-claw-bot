from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables
from tools.compile_wiki import index_wiki_documents


def _run_ask(args: list[str]) -> dict:
    return json.loads(_run_ask_stdout(args))


def _run_ask_stdout(args: list[str]) -> str:
    from tools.ask import main

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(args)
    return stdout.getvalue()


class V07AskCliTests(unittest.TestCase):
    def test_ask_cli_json_contract_no_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            result = _run_ask(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--db-path",
                    str(root / "ffxiv.sqlite"),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["question"], "7.x 건브레이커 변경 이력 알려줘")
        self.assertEqual(result["contexts"], [])
        self.assertEqual(result["actions"], [])
        self.assertEqual(result["answer"]["format"], "text")
        self.assertEqual(result["answer"]["confidence"], "N/A")
        self.assertEqual(result["answer"]["sources"], [])

    def test_ask_cli_rejects_empty_question(self) -> None:
        result = _run_ask([""])

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_stage"], "parse")
        self.assertIn("question", result["error_message"])
        self.assertEqual(result["actions"], [])

    def test_ask_cli_debug_includes_parsed_query_and_retrieval_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            result = _run_ask(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--debug",
                    "--db-path",
                    str(root / "ffxiv.sqlite"),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertEqual(result["parsed_query"]["job"], "gunbreaker")
        self.assertEqual(result["parsed_query"]["patch_range"], "7.0..7.99")
        self.assertEqual(result["retrieval_plan"]["primary"][0]["wiki_type"], "job")
        self.assertEqual(result["retrieval_plan"]["primary"][0]["topic"], "gunbreaker")

    def test_ask_cli_text_output_contains_answer_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output = _run_ask_stdout(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--format",
                    "text",
                    "--db-path",
                    str(root / "ffxiv.sqlite"),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertIn("관련 KB 문서를 찾지 못했습니다", output)

    def test_ask_cli_text_output_no_json_braces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output = _run_ask_stdout(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--format",
                    "text",
                    "--db-path",
                    str(root / "ffxiv.sqlite"),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertNotIn("{", output)
        self.assertNotIn("}", output)

    def test_ask_cli_job_change_history_uses_job_wiki_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            job_dir = root / "wiki" / "jobs"
            source_dir = root / "wiki" / "source_summaries"
            job_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            (job_dir / "gunbreaker.md").write_text(
                "# Gunbreaker 변경 이력\n\n"
                "source_id: job_wiki_manual\n\n"
                "## 7.0\n\n"
                "- Continuation potency adjusted.\n",
                encoding="utf-8",
            )
            (source_dir / "patch_7_0.md").write_text(
                "# Patch 7.0 Notes\n\n"
                "source_id: patch_7_0\n\n"
                "Gunbreaker source summary fallback content.\n",
                encoding="utf-8",
            )
            index_wiki_documents(root_path=root, db_path=db_path)

            result = _run_ask(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--db-path",
                    str(db_path),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertEqual(result["contexts"][0]["page_id"], "job_gunbreaker")
        self.assertEqual(result["contexts"][0]["path"], "wiki/jobs/gunbreaker.md")
        self.assertIn("wiki/jobs/gunbreaker.md", result["answer"]["body"])
        self.assertIn("Continuation potency adjusted", result["answer"]["body"])

    def test_ask_cli_source_summary_fallback_when_no_job_wiki(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            source_dir = root / "wiki" / "source_summaries"
            source_dir.mkdir(parents=True)
            (source_dir / "patch_7_0.md").write_text(
                "# Patch 7.0 Notes\n\n"
                "source_id: patch_7_0\n\n"
                "Gunbreaker source summary fallback content.\n",
                encoding="utf-8",
            )
            index_wiki_documents(root_path=root, db_path=db_path)

            result = _run_ask(
                [
                    "7.x 건브레이커 변경 이력 알려줘",
                    "--db-path",
                    str(db_path),
                    "--root-path",
                    str(root),
                ]
            )

        self.assertEqual(result["contexts"][0]["wiki_type"], "source_summary")
        self.assertEqual(result["contexts"][0]["path"], "wiki/source_summaries/patch_7_0.md")
        self.assertIn("wiki/source_summaries/patch_7_0.md", result["answer"]["body"])
        self.assertIn("patch_7_0", result["answer"]["body"])


if __name__ == "__main__":
    unittest.main()
