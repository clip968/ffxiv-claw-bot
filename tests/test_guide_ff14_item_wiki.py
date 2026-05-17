from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.guide_ff14.models import GuideItem
from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_item
from tests.test_compile_wiki import ensure_wiki_tables


class GuideFF14ItemWikiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.wiki_root = self.root / "wiki"
        ensure_wiki_tables(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            ensure_guide_ff14_schema(conn)
            upsert_item(
                conn,
                GuideItem(
                    id="5398978e726",
                    name="영웅의 건블레이드",
                    name_ko="영웅의 건블레이드",
                    url="https://guide.ff14.co.kr/lodestone/db/item/5398978e726",
                    category="무기",
                    subcategory="건블레이드",
                    item_level=700,
                    equip_level=100,
                    jobs=["건브레이커", "Gunbreaker"],
                    stats={"힘": 123, "활력": 456},
                    source={},
                    description="건브레이커를 위한 한국어 설명입니다.",
                    content_hash="hash-a",
                    raw_path="data/raw/guide_ff14/items/5398978e726.html",
                ),
                now="2026-05-17T00:00:00+00:00",
            )

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_dry_run_returns_planned_paths_and_writes_nothing(self) -> None:
        from src.derived_wiki.item_wiki_generator import generate_item_wiki

        with sqlite3.connect(self.db_path) as conn:
            result = generate_item_wiki(conn, self.wiki_root, dry_run=True, verbose=True)

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["dry_run"])
        self.assertIn("wiki/items/index.md", result["planned_paths"])
        self.assertFalse((self.wiki_root / "items").exists())
        self.assertIsNone(self._page("item_5398978e726"))

    def test_apply_writes_index_category_and_item_pages(self) -> None:
        self._generate()

        self.assertTrue((self.wiki_root / "items" / "index.md").exists())
        self.assertTrue((self.wiki_root / "items" / "categories" / "geombeulreideu.md").exists())
        self.assertTrue((self.wiki_root / "items" / "5398978e726.md").exists())

    def test_item_page_includes_official_url_and_levels(self) -> None:
        self._generate()

        content = (self.wiki_root / "items" / "5398978e726.md").read_text(encoding="utf-8")

        self.assertIn("https://guide.ff14.co.kr/lodestone/db/item/5398978e726", content)
        self.assertIn("Item level: 700", content)
        self.assertIn("Equip level: 100", content)

    def test_missing_acquisition_data_has_explicit_absence_note(self) -> None:
        self._generate()

        content = (self.wiki_root / "items" / "5398978e726.md").read_text(encoding="utf-8")

        self.assertIn("Current KB has no acquisition data for this item.", content)

    def test_apply_indexes_item_pages_into_wiki_pages_and_fts(self) -> None:
        self._generate()

        self.assertEqual(self._page("item_5398978e726"), ("item", "영웅의 건블레이드"))
        conn = sqlite3.connect(self.db_path)
        try:
            fts_row = conn.execute(
                "SELECT title, body FROM wiki_fts WHERE page_id = ?",
                ("item_5398978e726",),
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(fts_row)
        self.assertEqual(fts_row[0], "영웅의 건블레이드")
        self.assertIn("건블레이드", fts_row[1])

    def test_rerun_does_not_duplicate_wiki_db_records(self) -> None:
        self._generate()
        self._generate()

        conn = sqlite3.connect(self.db_path)
        try:
            page_count = conn.execute(
                "SELECT COUNT(*) FROM wiki_pages WHERE id = ?",
                ("item_5398978e726",),
            ).fetchone()[0]
            fts_count = conn.execute(
                "SELECT COUNT(*) FROM wiki_fts WHERE page_id = ?",
                ("item_5398978e726",),
            ).fetchone()[0]
        finally:
            conn.close()

        self.assertEqual(page_count, 1)
        self.assertEqual(fts_count, 1)

    def test_wiki_index_links_to_items_index(self) -> None:
        self._generate()

        content = (self.wiki_root / "index.md").read_text(encoding="utf-8")

        self.assertIn("[Items](items/index.md)", content)

    def test_compile_wiki_scanner_can_index_item_pages(self) -> None:
        from tools.compile_wiki import index_wiki_documents

        self._generate()
        result = index_wiki_documents(root_path=self.root, db_path=self.db_path)

        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["summary"]["item"], 1)
        self.assertEqual(self._page("item_5398978e726"), ("item", "영웅의 건블레이드"))

    def test_cli_prints_json_result(self) -> None:
        from tools.generate_item_wiki import main

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main(["--db-path", str(self.db_path), "--wiki-root", str(self.wiki_root), "--dry-run"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["dry_run"])

    def _generate(self) -> dict:
        from src.derived_wiki.item_wiki_generator import generate_item_wiki

        with sqlite3.connect(self.db_path) as conn:
            return generate_item_wiki(conn, self.wiki_root, dry_run=False, verbose=True)

    def _page(self, page_id: str) -> tuple[str, str] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT type, title FROM wiki_pages WHERE id = ?",
                (page_id,),
            ).fetchone()
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
