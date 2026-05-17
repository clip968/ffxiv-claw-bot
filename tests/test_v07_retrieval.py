from __future__ import annotations

import dataclasses
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables


class V07RetrievalPlannerTests(unittest.TestCase):
    def test_job_change_history_plan_prefers_job_wiki(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
        plan = build_retrieval_plan(parsed)

        self.assertTrue(dataclasses.is_dataclass(plan))
        self.assertEqual(plan.primary[0].wiki_type, "job")
        self.assertEqual(plan.primary[0].topic, "gunbreaker")
        self.assertIn("gunbreaker", plan.primary[0].query)
        self.assertEqual(plan.limit, 5)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            plan.limit = 10

    def test_generic_search_plan_has_no_topic_filter(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("M4S 공략 찾아줘")
        plan = build_retrieval_plan(parsed, limit=3)

        self.assertEqual(plan.primary[0].wiki_type, None)
        self.assertEqual(plan.primary[0].topic, None)
        self.assertEqual(plan.primary[0].query, parsed.normalized_query)
        self.assertEqual(plan.limit, 3)

    def test_job_change_history_plan_has_source_summary_fallback(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("GNB change history")
        plan = build_retrieval_plan(parsed)

        self.assertEqual(plan.fallback[0].wiki_type, "source_summary")
        self.assertEqual(plan.fallback[0].topic, None)
        self.assertTrue(any(target.wiki_type is None for target in plan.fallback))


class V07FilteredFtsSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        ensure_wiki_tables(self.db_path)
        self._insert_page(
            "job_gunbreaker",
            "job",
            "Gunbreaker Changes",
            "wiki/jobs/gunbreaker.md",
            "gunbreaker",
            "Gunbreaker Continuation changes",
        )
        self._insert_page(
            "job_black_mage",
            "job",
            "Black Mage Changes",
            "wiki/jobs/black_mage.md",
            "black_mage",
            "Black Mage changes",
        )
        self._insert_page(
            "wiki_patch_7_0",
            "source_summary",
            "Patch 7.0 Notes",
            "wiki/source_summaries/patch_7_0.md",
            None,
            "Gunbreaker source summary changes",
        )

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _insert_page(
        self,
        page_id: str,
        wiki_type: str,
        title: str,
        path: str,
        job: str | None,
        body: str,
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO wiki_pages (
                    id, type, title, path, job, source_ids, confidence,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, '[]', 'high', '2026-05-17', '2026-05-17')
                """,
                (page_id, wiki_type, title, path, job),
            )
            conn.execute(
                "INSERT INTO wiki_fts (page_id, title, body) VALUES (?, ?, ?)",
                (page_id, title, body),
            )
            conn.commit()
        finally:
            conn.close()

    def test_search_wiki_filters_by_wiki_type_job(self) -> None:
        from src.retrieval.fts_search import search_wiki

        results = search_wiki("Gunbreaker", wiki_type="job", db_path=self.db_path)

        self.assertEqual([result.page_id for result in results], ["job_gunbreaker"])
        self.assertTrue(all(result.wiki_type == "job" for result in results))

    def test_search_wiki_filters_by_topic(self) -> None:
        from src.retrieval.fts_search import search_wiki

        results = search_wiki("changes", wiki_type="job", topic="gunbreaker", db_path=self.db_path)

        self.assertEqual([result.page_id for result in results], ["job_gunbreaker"])
        self.assertEqual(results[0].topic, "gunbreaker")

    def test_search_wiki_returns_source_summary_fallback(self) -> None:
        from src.retrieval.fts_search import search_wiki

        results = search_wiki("Gunbreaker", wiki_type="source_summary", db_path=self.db_path)

        self.assertEqual([result.page_id for result in results], ["wiki_patch_7_0"])
        self.assertEqual(results[0].wiki_type, "source_summary")

    def test_search_wiki_sanitizes_fts_query(self) -> None:
        from src.retrieval.fts_search import search_wiki

        results = search_wiki('Gunbreaker " * (', db_path=self.db_path)

        self.assertTrue(any(result.page_id == "job_gunbreaker" for result in results))


if __name__ == "__main__":
    unittest.main()
