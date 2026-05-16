from __future__ import annotations

import importlib
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "lodestone_patch_7_5.html"
LODESTONE_URL = "https://na.finalfantasyxiv.com/lodestone/topics/detail/patch-7-5"


class FakeResponse:
    def __init__(
        self,
        *,
        text: str,
        content_type: str,
        status_error: Exception | None = None,
    ) -> None:
        self.text = text
        self.headers = {"content-type": content_type}
        self._status_error = status_error

    def raise_for_status(self) -> None:
        if self._status_error:
            raise self._status_error


def require_fetch_url_module(test: unittest.TestCase) -> Any:
    try:
        module = importlib.import_module("tools.fetch_url")
    except ModuleNotFoundError as exc:
        if exc.name == "tools.fetch_url":
            test.fail("Expected tools.fetch_url module for v05-05 URL integration")
        raise

    if not hasattr(module, "fetch_single_url"):
        test.fail("Expected tools.fetch_url.fetch_single_url")
    if not hasattr(module, "UrlFetchError"):
        test.fail("Expected tools.fetch_url.UrlFetchError")
    return module


class V05FetchUrlTests(unittest.TestCase):
    def test_fetch_url_uses_lodestone_extractor_for_lodestone_url(self) -> None:
        module = require_fetch_url_module(self)
        html = FIXTURE_PATH.read_text(encoding="utf-8")

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text=html,
                content_type="text/html; charset=utf-8",
            )

            result = module.fetch_single_url(LODESTONE_URL)

        mock_get.assert_called_once()
        self.assertEqual(result["url"], LODESTONE_URL)
        self.assertEqual(result["content_type"], "text/html; charset=utf-8")
        self.assertEqual(result["title"], "Patch 7.5 Notes")
        self.assertEqual(result["extractor"], "lodestone")
        self.assertIn("New main scenario quests have been added.", result["body"])
        self.assertNotIn("Recent Topics should not be extracted", result["body"])
        self.assertNotIn("Share this article", result["body"])

    def test_fetch_html_extracts_title_and_visible_text(self) -> None:
        module = require_fetch_url_module(self)
        html = """
        <html>
          <head>
            <title>Patch 7.5 Notes</title>
            <script>console.log("ignore me")</script>
          </head>
          <body>
            <nav>Navigation should be ignored</nav>
            <main>
              <h1>Patch 7.5 Notes</h1>
              <p>New raid adjustments are available.</p>
            </main>
          </body>
        </html>
        """
        url = "https://example.com/ffxiv/patch-7-5"

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text=html,
                content_type="text/html; charset=utf-8",
            )

            result = module.fetch_single_url(url)

        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args.args[0], url)
        self.assertEqual(result["url"], url)
        self.assertEqual(result["content_type"], "text/html; charset=utf-8")
        self.assertEqual(result["title"], "Patch 7.5 Notes")
        self.assertEqual(result["extractor"], "generic_html")
        self.assertIn("New raid adjustments are available.", result["body"])
        self.assertNotIn("console.log", result["body"])
        self.assertNotIn("<html", result["body"])

    def test_fetch_plain_text_uses_url_fallback_title(self) -> None:
        module = require_fetch_url_module(self)
        url = "https://example.com/guides/opener.txt"

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text="Use tincture before raid buffs.",
                content_type="text/plain",
            )

            result = module.fetch_single_url(url)

        self.assertEqual(result["title"], "example.com/guides/opener.txt")
        self.assertEqual(result["extractor"], "text")
        self.assertEqual(result["body"], "Use tincture before raid buffs.")

    def test_fetch_json_uses_url_fallback_title_and_json_extractor(self) -> None:
        module = require_fetch_url_module(self)
        url = "https://example.com/api/patch.json"

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text='{"patch":"7.5","title":"Patch 7.5 Notes"}',
                content_type="application/json",
            )

            result = module.fetch_single_url(url)

        self.assertEqual(result["title"], "example.com/api/patch.json")
        self.assertEqual(result["extractor"], "json")
        self.assertEqual(result["body"], '{"patch":"7.5","title":"Patch 7.5 Notes"}')

    def test_fetch_unsupported_content_type_raises_url_fetch_error(self) -> None:
        module = require_fetch_url_module(self)

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text="%PDF-1.7",
                content_type="application/pdf",
            )

            with self.assertRaises(module.UrlFetchError) as raised:
                module.fetch_single_url("https://example.com/file.pdf")

        self.assertIn("unsupported content-type", str(raised.exception))

    def test_fetch_http_error_raises_url_fetch_error(self) -> None:
        module = require_fetch_url_module(self)

        with patch.object(module.requests, "get") as mock_get:
            mock_get.return_value = FakeResponse(
                text="not found",
                content_type="text/plain",
                status_error=RuntimeError("404 Client Error"),
            )

            with self.assertRaises(module.UrlFetchError) as raised:
                module.fetch_single_url("https://example.com/missing")

        self.assertIn("404 Client Error", str(raised.exception))
