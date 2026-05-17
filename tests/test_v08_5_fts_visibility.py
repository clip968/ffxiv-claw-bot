from __future__ import annotations

import sqlite3
import tempfile
import unittest
import json
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables


class V085FtsVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        ensure_wiki_tables(self.db_path)
        self._write_wiki()

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _write_wiki(self) -> None:
        files = {
            "wiki/source_summaries/local_v08_5_source.md": (
                "# Patch 7.5 Source\n\n"
                "> Source: `local_v08_5_source`\n\n"
                "---\n\n"
                "Gunbreaker source summary fallback mentions No Mercy.\n"
            ),
            "wiki/jobs/gunbreaker.md": (
                "# Gunbreaker\n\n"
                "## Recent Facts\n\n"
                "- No Mercy duration was changed in Patch 7.5.\n"
            ),
            "wiki/patches/7_5.md": (
                "# Patch 7.5\n\n"
                "## Affected Jobs\n\n"
                "- Gunbreaker\n"
            ),
            "wiki/skills/no_mercy.md": (
                "# No Mercy\n\n"
                "## Job\n\n"
                "- Gunbreaker\n"
            ),
        }
        for relative_path, content in files.items():
            path = self.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def _index(self) -> dict:
        from tools.compile_wiki import index_wiki_documents

        return index_wiki_documents(root_path=self.root, db_path=self.db_path)

    def _page(self, page_id: str) -> tuple[str, str, str | None] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT type, title, job FROM wiki_pages WHERE id = ?",
                (page_id,),
            ).fetchone()
        finally:
            conn.close()

    def test_generated_job_wiki_in_wiki_pages(self) -> None:
        self._index()

        self.assertEqual(self._page("job_gunbreaker"), ("job", "Gunbreaker", "gunbreaker"))

    def test_generated_patch_wiki_in_wiki_pages(self) -> None:
        self._index()

        self.assertEqual(self._page("patch_7_5"), ("patch", "Patch 7.5", None))

    def test_generated_skill_wiki_in_wiki_pages(self) -> None:
        self._index()

        self.assertEqual(self._page("skill_no_mercy"), ("skill", "No Mercy", None))

    def test_generated_wiki_searchable(self) -> None:
        from src.retrieval.fts_search import search_wiki

        self._index()

        patch_results = search_wiki("Patch 7.5", wiki_type="patch", db_path=self.db_path)
        skill_results = search_wiki("No Mercy", wiki_type="skill", db_path=self.db_path)

        self.assertEqual([result.page_id for result in patch_results], ["patch_7_5"])
        self.assertEqual([result.page_id for result in skill_results], ["skill_no_mercy"])

    def test_source_summary_fallback_preserved(self) -> None:
        from src.retrieval.fts_search import search_wiki

        self._index()

        results = search_wiki("fallback", wiki_type="source_summary", db_path=self.db_path)

        self.assertEqual([result.page_id for result in results], ["wiki_local_v08_5_source"])

    def test_entity_match_falls_back_to_generated_skill_page(self) -> None:
        from src.retrieval.hybrid import execute_graph_aware_retrieval

        self._index()
        graph_dir = self.root / "graph"
        graph_dir.mkdir()
        (graph_dir / "entity_index.json").write_text(
            json.dumps({"no mercy": "skill:no_mercy"}, ensure_ascii=False),
            encoding="utf-8",
        )

        results = execute_graph_aware_retrieval(
            "No Mercy 관련 변경 있어?",
            (),
            db_path=self.db_path,
            graph_dir=graph_dir,
        )

        self.assertEqual([result.page_id for result in results], ["skill_no_mercy"])


if __name__ == "__main__":
    unittest.main()
