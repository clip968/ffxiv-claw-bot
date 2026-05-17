from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.test_compile_wiki import ensure_wiki_tables


ITEM_ID = "5398978e726"
ITEM_URL = f"https://guide.ff14.co.kr/lodestone/db/item/{ITEM_ID}"


class GuideFF14ItemRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.graph_dir = self.root / "graph"
        self.graph_dir.mkdir()
        ensure_wiki_tables(self.db_path)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_item_query_plan_searches_item_pages_before_general_fts(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("건브 무기")
        plan = build_retrieval_plan(parsed)

        self.assertEqual(plan.primary[0].wiki_type, "item")
        self.assertTrue(any(target.wiki_type is None for target in plan.fallback))

    def test_item_query_ranks_item_context_before_unrelated_job_guide(self) -> None:
        self._insert_item_page()
        self._insert_page(
            page_id="job_black_mage",
            wiki_type="job",
            title="Black Mage Weapon Notes",
            path="wiki/jobs/black_mage.md",
            job="black_mage",
            body="건브 무기 건브 무기 건브 무기 unrelated Black Mage job guide.",
        )

        payload = self._ask("건브 무기")

        self.assertEqual(payload["contexts"][0]["page_id"], f"item_{ITEM_ID}")
        self.assertEqual(payload["contexts"][0]["wiki_type"], "item")

    def test_item_answer_includes_official_url_and_missing_acquisition_note(self) -> None:
        self._insert_item_page()

        payload = self._ask("영웅의 건블레이드")

        body = payload["answer"]["body"]
        self.assertIn(ITEM_URL, body)
        self.assertIn("Current KB has no acquisition data for this item.", body)
        self.assertIn(f"wiki/items/{ITEM_ID}.md", body)

    def test_non_item_job_change_plan_stays_job_first(self) -> None:
        from src.query import parse_query
        from src.retrieval import build_retrieval_plan

        parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
        plan = build_retrieval_plan(parsed)

        self.assertEqual(plan.primary[0].wiki_type, "job")
        self.assertEqual(plan.primary[0].topic, "gunbreaker")

    def _insert_item_page(self) -> None:
        body = "\n".join(
            [
                "# 영웅의 건블레이드",
                "",
                "## Official Source",
                "",
                f"- URL: {ITEM_URL}",
                "- Raw path: `data/raw/guide_ff14/items/5398978e726.html`",
                "",
                "## Item Facts",
                "",
                "- Category: 무기",
                "- Subcategory: 건블레이드",
                "- Item level: 700",
                "- Equip level: 100",
                "- Allowed jobs: 건브레이커, Gunbreaker",
                "",
                "## Acquisition",
                "",
                "- Current KB has no acquisition data for this item.",
                "",
                "## Description",
                "",
                "건브레이커 무기입니다.",
                "",
            ]
        )
        path = self.root / "wiki" / "items" / f"{ITEM_ID}.md"
        path.parent.mkdir(parents=True)
        path.write_text(body, encoding="utf-8")
        self._insert_page(
            page_id=f"item_{ITEM_ID}",
            wiki_type="item",
            title="영웅의 건블레이드",
            path=f"wiki/items/{ITEM_ID}.md",
            job=None,
            body=body,
        )

    def _insert_page(
        self,
        *,
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

    def _ask(self, question: str) -> dict:
        from tools.ask import run_ask

        return run_ask(
            SimpleNamespace(
                question=question,
                debug=False,
                limit=5,
                db_path=self.db_path,
                root_path=self.root,
                graph_dir=self.graph_dir,
            )
        )


if __name__ == "__main__":
    unittest.main()
