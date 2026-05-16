from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "lodestone_patch_7_5.html"
LODESTONE_URL = "https://na.finalfantasyxiv.com/lodestone/topics/detail/patch-7-5"


def require_lodestone_module(test: unittest.TestCase) -> Any:
    try:
        module = importlib.import_module("tools.extractors.lodestone")
    except ModuleNotFoundError as exc:
        if exc.name in {"tools.extractors", "tools.extractors.lodestone"}:
            test.fail("Expected tools.extractors.lodestone for v05.1 Lodestone extraction")
        raise

    for attr in ("LodestoneExtractionError", "extract_lodestone_article", "is_lodestone_url"):
        if not hasattr(module, attr):
            test.fail(f"Expected tools.extractors.lodestone.{attr}")
    return module


class V051LodestoneExtractorTests(unittest.TestCase):
    def test_lodestone_url_detection_accepts_official_regions(self) -> None:
        module = require_lodestone_module(self)

        for region in ("na", "eu", "jp", "de", "fr"):
            with self.subTest(region=region):
                url = f"https://{region}.finalfantasyxiv.com/lodestone/topics/detail/abc123"
                self.assertTrue(module.is_lodestone_url(url))

        self.assertFalse(module.is_lodestone_url("https://example.com/lodestone/topics/detail/abc123"))
        self.assertFalse(module.is_lodestone_url("https://na.finalfantasyxiv.com/news/detail/abc123"))

    def test_lodestone_extractor_uses_news_detail_wrapper(self) -> None:
        module = require_lodestone_module(self)
        html = FIXTURE_PATH.read_text(encoding="utf-8")

        result = module.extract_lodestone_article(html, LODESTONE_URL)

        self.assertEqual(result["extractor"], "lodestone")
        self.assertIn("New main scenario quests have been added.", result["body"])
        self.assertIn("Several battle system adjustments have been made.", result["body"])
        self.assertIn("New gear and recipes are now available from select vendors.", result["body"])
        self.assertNotIn("Recent Topics should not be extracted", result["body"])

    def test_lodestone_extractor_excludes_navigation_noise(self) -> None:
        module = require_lodestone_module(self)
        html = FIXTURE_PATH.read_text(encoding="utf-8")

        result = module.extract_lodestone_article(html, LODESTONE_URL)

        body = result["body"]
        self.assertNotIn("Lodestone Global Navigation", body)
        self.assertNotIn("Lodestone Footer Links", body)
        self.assertNotIn("Share this article", body)
        self.assertNotIn("should not be extracted", body)
        self.assertNotIn("<article", body)

    def test_lodestone_extractor_extracts_patch_title(self) -> None:
        module = require_lodestone_module(self)
        html = FIXTURE_PATH.read_text(encoding="utf-8")

        result = module.extract_lodestone_article(html, LODESTONE_URL)

        self.assertEqual(result["title"], "Patch 7.5 Notes")
        self.assertTrue(result["body"].startswith("Patch 7.5 Notes"))

    def test_lodestone_extractor_rejects_empty_body(self) -> None:
        module = require_lodestone_module(self)
        html = """
        <html>
          <head><title>Patch 7.5 Notes</title></head>
          <body>
            <div class="news__detail__wrapper">
              <div class="news__detail__share">Share this article</div>
              <script>console.log("empty")</script>
            </div>
          </body>
        </html>
        """

        with self.assertRaises(module.LodestoneExtractionError) as raised:
            module.extract_lodestone_article(html, LODESTONE_URL)

        self.assertIn("empty", str(raised.exception).lower())


if __name__ == "__main__":
    unittest.main()
