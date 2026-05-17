from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.guide_ff14.fetcher import FetchResult


CATEGORY_URL = "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110"
DETAIL_URL = "https://guide.ff14.co.kr/lodestone/db/item/5398978e726"
SECOND_DETAIL_URL = "https://guide.ff14.co.kr/lodestone/db/item/abc123def45"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guide_ff14"


class FakeFetcher:
    def __init__(self, responses: dict[str, FetchResult]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def fetch(self, url: str) -> FetchResult:
        self.calls.append(url)
        return self.responses[url]


def _ok(url: str, body: str) -> FetchResult:
    return FetchResult(
        url=url,
        status="ok",
        http_status=200,
        final_url=url,
        body=body,
        encoding="utf-8",
        content_hash=f"hash-{abs(hash((url, body))) % 100000}",
    )


def _error(url: str, message: str) -> FetchResult:
    return FetchResult(url=url, status="error", error=message)


class GuideFF14CrawlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.raw_dir = self.root / "raw" / "guide_ff14"
        self.category_html = (FIXTURE_DIR / "item_category_gunblade.html").read_text(encoding="utf-8")
        self.item_html = (FIXTURE_DIR / "item_detail_gunblade.html").read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_item_pilot_dry_run_returns_planned_urls_without_mutation(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        fetcher = FakeFetcher({CATEGORY_URL: _ok(CATEGORY_URL, self.category_html)})

        result = crawl_item_pilot(
            category_url=CATEGORY_URL,
            limit=2,
            apply=False,
            fetcher=fetcher,
            db_path=self.db_path,
            raw_dir=self.raw_dir,
        )

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["planned_urls"], [DETAIL_URL, SECOND_DETAIL_URL])
        self.assertFalse(self.db_path.exists())
        self.assertFalse(self.raw_dir.exists())

    def test_item_pilot_apply_limit_one_fetches_and_stores_one_item(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        fetcher = FakeFetcher(
            {
                CATEGORY_URL: _ok(CATEGORY_URL, self.category_html),
                DETAIL_URL: _ok(DETAIL_URL, self.item_html),
            }
        )

        result = crawl_item_pilot(
            category_url=CATEGORY_URL,
            limit=1,
            apply=True,
            fetcher=fetcher,
            db_path=self.db_path,
            raw_dir=self.raw_dir,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["parsed"], 1)
        conn = sqlite3.connect(self.db_path)
        try:
            item_count = conn.execute("SELECT COUNT(*) FROM guide_items").fetchone()[0]
            crawl_count = conn.execute("SELECT COUNT(*) FROM guide_crawl_pages").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(item_count, 1)
        self.assertEqual(crawl_count, 2)
        self.assertTrue(any(self.raw_dir.rglob("*.html")))

    def test_apply_rerun_is_idempotent(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        for _ in range(2):
            fetcher = FakeFetcher(
                {
                    CATEGORY_URL: _ok(CATEGORY_URL, self.category_html),
                    DETAIL_URL: _ok(DETAIL_URL, self.item_html),
                }
            )
            crawl_item_pilot(
                category_url=CATEGORY_URL,
                limit=1,
                apply=True,
                fetcher=fetcher,
                db_path=self.db_path,
                raw_dir=self.raw_dir,
            )

        conn = sqlite3.connect(self.db_path)
        try:
            item_count = conn.execute("SELECT COUNT(*) FROM guide_items").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(item_count, 1)

    def test_category_failure_returns_error_without_detail_fetches(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        fetcher = FakeFetcher({CATEGORY_URL: _error(CATEGORY_URL, "category unavailable")})

        result = crawl_item_pilot(
            category_url=CATEGORY_URL,
            limit=2,
            apply=True,
            fetcher=fetcher,
            db_path=self.db_path,
            raw_dir=self.raw_dir,
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("category unavailable", result["errors"][0]["error"])
        self.assertEqual(fetcher.calls, [CATEGORY_URL])

    def test_detail_failure_is_recorded_and_remaining_details_continue(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        fetcher = FakeFetcher(
            {
                CATEGORY_URL: _ok(CATEGORY_URL, self.category_html),
                DETAIL_URL: _error(DETAIL_URL, "detail reset"),
                SECOND_DETAIL_URL: _ok(SECOND_DETAIL_URL, self.item_html),
            }
        )

        result = crawl_item_pilot(
            category_url=CATEGORY_URL,
            limit=2,
            apply=True,
            fetcher=fetcher,
            db_path=self.db_path,
            raw_dir=self.raw_dir,
        )

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["parsed"], 1)
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("detail reset", result["errors"][0]["error"])

    def test_discovered_detail_urls_are_absolute_and_limited(self) -> None:
        from src.guide_ff14.crawler import discover_item_detail_urls

        urls = discover_item_detail_urls(self.category_html, base_url=CATEGORY_URL, limit=1)

        self.assertEqual(urls, [DETAIL_URL])

    def test_result_contains_required_json_keys(self) -> None:
        from src.guide_ff14.crawler import crawl_item_pilot

        fetcher = FakeFetcher({CATEGORY_URL: _ok(CATEGORY_URL, self.category_html)})

        result = crawl_item_pilot(
            category_url=CATEGORY_URL,
            limit=1,
            apply=False,
            fetcher=fetcher,
            db_path=self.db_path,
            raw_dir=self.raw_dir,
        )

        self.assertTrue(
            {
                "status",
                "category_url",
                "planned_urls",
                "fetched",
                "parsed",
                "skipped",
                "errors",
                "next_action",
            }.issubset(result)
        )

    def test_cli_prints_structured_json_with_fake_fetcher(self) -> None:
        from tools.crawl_guide_ff14 import main

        fetcher = FakeFetcher({CATEGORY_URL: _ok(CATEGORY_URL, self.category_html)})
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main(
                [
                    "item-pilot",
                    "--category-url",
                    CATEGORY_URL,
                    "--limit",
                    "1",
                    "--dry-run",
                    "--db-path",
                    str(self.db_path),
                    "--raw-dir",
                    str(self.raw_dir),
                ],
                fetcher=fetcher,
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["planned_urls"], [DETAIL_URL])


if __name__ == "__main__":
    unittest.main()
