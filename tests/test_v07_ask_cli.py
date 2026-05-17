from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path


def _run_ask(args: list[str]) -> dict:
    from tools.ask import main

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(args)
    return json.loads(stdout.getvalue())


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


if __name__ == "__main__":
    unittest.main()
