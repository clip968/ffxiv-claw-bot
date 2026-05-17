from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


class GuideFF14StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp_dir.name) / "ffxiv.sqlite"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self) -> None:
        self.conn.close()
        self._tmp_dir.cleanup()

    def test_schema_creation_is_idempotent(self) -> None:
        from src.guide_ff14.storage import ensure_guide_ff14_schema

        ensure_guide_ff14_schema(self.conn)
        ensure_guide_ff14_schema(self.conn)

        tables = {
            row["name"]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertIn("guide_crawl_pages", tables)
        self.assertIn("guide_categories", tables)
        self.assertIn("guide_items", tables)
        self.assertIn("guide_item_sources", tables)

    def test_upsert_crawl_page_dedupes_by_url_and_updates_status_hash(self) -> None:
        from src.guide_ff14.models import GuideCrawlPage
        from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_crawl_page

        ensure_guide_ff14_schema(self.conn)
        url = "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110"
        upsert_crawl_page(
            self.conn,
            GuideCrawlPage(
                url=url,
                kind="category_page",
                status="fetched",
                http_status=200,
                content_hash="hash-a",
                raw_path="data/raw/guide_ff14/category-a.html",
            ),
            now="2026-05-17T00:00:00+00:00",
        )
        upsert_crawl_page(
            self.conn,
            GuideCrawlPage(
                url=url,
                kind="category_page",
                status="parsed",
                http_status=200,
                content_hash="hash-b",
                raw_path="data/raw/guide_ff14/category-a.html",
            ),
            now="2026-05-17T00:01:00+00:00",
        )

        rows = self.conn.execute("SELECT * FROM guide_crawl_pages").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "parsed")
        self.assertEqual(rows[0]["content_hash"], "hash-b")
        self.assertEqual(rows[0]["created_at"], "2026-05-17T00:00:00+00:00")
        self.assertEqual(rows[0]["updated_at"], "2026-05-17T00:01:00+00:00")

    def test_upsert_category_dedupes_by_url_and_preserves_filters_json(self) -> None:
        from src.guide_ff14.models import GuideCategory
        from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_category

        ensure_guide_ff14_schema(self.conn)
        url = "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110"
        upsert_category(
            self.conn,
            GuideCategory(
                id="guide:item:1:110",
                db_type="item",
                label="건블레이드",
                url=url,
                category2="1",
                category3="110",
                filters={"max_item_lv": "700", "min_item_lv": "650"},
            ),
            now="2026-05-17T00:00:00+00:00",
        )
        upsert_category(
            self.conn,
            GuideCategory(
                id="guide:item:1:110",
                db_type="item",
                label="건블레이드",
                url=url,
                category2="1",
                category3="110",
                filters={"max_item_lv": "710", "min_item_lv": "650"},
            ),
            now="2026-05-17T00:01:00+00:00",
        )

        rows = self.conn.execute("SELECT * FROM guide_categories").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], url)
        self.assertEqual(rows[0]["label"], "건블레이드")
        self.assertEqual(
            json.loads(rows[0]["filters_json"]),
            {"max_item_lv": "710", "min_item_lv": "650"},
        )

    def test_upsert_item_dedupes_by_detail_id_and_stores_valid_json(self) -> None:
        from src.guide_ff14.models import GuideItem
        from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_item

        ensure_guide_ff14_schema(self.conn)
        url = "https://guide.ff14.co.kr/lodestone/db/item/5398978e726"
        item = GuideItem(
            id="5398978e726",
            name="테스트 건블레이드",
            name_ko="테스트 건블레이드",
            url=url,
            category="무기",
            subcategory="건블레이드",
            item_level=700,
            equip_level=100,
            jobs=["건브레이커", "Gunbreaker"],
            stats={"힘": 123, "활력": 456},
            source={"type": "unknown"},
            description="테스트 설명",
            content_hash="hash-a",
            raw_path="data/raw/guide_ff14/items/5398978e726.html",
        )

        upsert_item(self.conn, item, now="2026-05-17T00:00:00+00:00")
        item.content_hash = "hash-b"
        item.stats = {"활력": 999}
        upsert_item(self.conn, item, now="2026-05-17T00:02:00+00:00")

        rows = self.conn.execute("SELECT * FROM guide_items").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "5398978e726")
        self.assertEqual(rows[0]["url"], url)
        self.assertEqual(rows[0]["content_hash"], "hash-b")
        self.assertEqual(json.loads(rows[0]["jobs_json"]), ["건브레이커", "Gunbreaker"])
        self.assertEqual(json.loads(rows[0]["stats_json"]), {"활력": 999})
        self.assertEqual(json.loads(rows[0]["source_json"]), {"type": "unknown"})
        self.assertEqual(rows[0]["created_at"], "2026-05-17T00:00:00+00:00")
        self.assertEqual(rows[0]["updated_at"], "2026-05-17T00:02:00+00:00")

    def test_upsert_item_source_dedupes_by_stable_id(self) -> None:
        from src.guide_ff14.models import GuideItemSource
        from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_item_source

        ensure_guide_ff14_schema(self.conn)
        source = GuideItemSource(
            id="source:5398978e726:unknown",
            item_id="5398978e726",
            source_type="unknown",
            source_name="획득처 미확인",
            properties={"note": "fixture"},
        )

        upsert_item_source(self.conn, source, now="2026-05-17T00:00:00+00:00")
        source.properties = {"note": "updated"}
        upsert_item_source(self.conn, source, now="2026-05-17T00:03:00+00:00")

        rows = self.conn.execute("SELECT * FROM guide_item_sources").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["item_id"], "5398978e726")
        self.assertEqual(json.loads(rows[0]["properties_json"]), {"note": "updated"})
        self.assertEqual(rows[0]["created_at"], "2026-05-17T00:00:00+00:00")
        self.assertEqual(rows[0]["updated_at"], "2026-05-17T00:03:00+00:00")


if __name__ == "__main__":
    unittest.main()
