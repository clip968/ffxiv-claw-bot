from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.search_kb import format_query, sanitize_fts_query


class SanitizeFtsQueryTests(unittest.TestCase):
    """santize_fts_query must strip FTS5-special characters from user input.

    FTS5 interprets ``@``, ``(``, ``)``, ``"``, ``-``, ``+``,
    ``*``, ``^``, ``:``, and ``/`` as syntax operators.  Raw user
    input containing these characters must never reach the FTS5
    MATCH clause or an ``sqlite3.OperationalError`` will be raised.
    """

    def test_path_separator_removed(self) -> None:
        """@[/] is an FTS5 NEAR operator and must be removed."""
        sanitized = sanitize_fts_query("tools/ingest_local.py 호출 확인")
        self.assertEqual(sanitized, "tools ingest_local.py 호출 확인")

    def test_at_sign_removed(self) -> None:
        """@ is an FTS5 NEAR operator."""
        sanitized = sanitize_fts_query("test @foo")
        self.assertEqual(sanitized, "test foo")

    def test_parentheses_removed(self) -> None:
        """() are FTS5 grouping operators."""
        sanitized = sanitize_fts_query("foo(bar) baz")
        self.assertEqual(sanitized, "foo bar baz")

    def test_double_quote_removed(self) -> None:
        """\" is the FTS5 phrase delimiter."""
        sanitized = sanitize_fts_query('"hello world" test')
        self.assertEqual(sanitized, "hello world test")

    def test_minus_and_plus_removed(self) -> None:
        """- and + are FTS5 NOT / required operators."""
        sanitized = sanitize_fts_query("foo -bar +baz")
        self.assertEqual(sanitized, "foo bar baz")

    def test_colon_removed(self) -> None:
        """: is the FTS5 column prefix."""
        sanitized = sanitize_fts_query("title:foo")
        self.assertEqual(sanitized, "title foo")

    def test_star_and_hat_removed(self) -> None:
        """* and ^ are FTS5 prefix / boost operators."""
        sanitized = sanitize_fts_query("foo* bar^2")
        self.assertEqual(sanitized, "foo bar 2")

    def test_mixed_special_chars(self) -> None:
        """Multiple special characters in realistic input."""
        sanitized = sanitize_fts_query("OpenClaw/Discord 테스트")
        self.assertEqual(sanitized, "OpenClaw Discord 테스트")

    def test_alphanumeric_only_preserved(self) -> None:
        """Normal text without special characters is unchanged."""
        sanitized = sanitize_fts_query("discord_agent_smoke_test")
        self.assertEqual(sanitized, "discord_agent_smoke_test")

    def test_korean_text_preserved(self) -> None:
        """Korean characters are not affected."""
        sanitized = sanitize_fts_query("한국어 검색 테스트")
        self.assertEqual(sanitized, "한국어 검색 테스트")

    def test_underscores_preserved(self) -> None:
        """Underscores are not FTS5-special and should be preserved."""
        sanitized = sanitize_fts_query("foo_bar baz_qux")
        self.assertEqual(sanitized, "foo_bar baz_qux")

    def test_whitespace_collapsed(self) -> None:
        """Consecutive spaces from removed chars are collapsed."""
        sanitized = sanitize_fts_query("@   @   foo")
        self.assertEqual(sanitized, "foo")

    def test_query_with_foo_bar_baz(self) -> None:
        """'foo/bar baz' must not cause FTS5 syntax error."""
        sanitized = sanitize_fts_query("foo/bar baz")
        self.assertEqual(sanitized, "foo bar baz")


class FormatQueryTests(unittest.TestCase):
    """format_query must apply sanitisation and reject empty input."""

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            format_query("  ")

    def test_sanitize_applied(self) -> None:
        result = format_query("tools/ingest_local.py")
        self.assertEqual(result, "tools ingest_local.py")


class AnswerBuildContextsNoCrashTests(unittest.TestCase):
    """build_contexts must not crash on FTS5-special character inputs.

    These tests verify the defence-in-depth in answer.py that catches
    sqlite3.OperationalError and falls through to empty results.
    """

    def test_path_separator_does_not_crash(self) -> None:
        """@[/] in question must not cause build_contexts to raise."""
        from tools.answer import build_contexts

        # connect to real DB — if it doesn't exist or has no FTS,
        # the OperationalError handler will catch it and return [].
        try:
            contexts = build_contexts("tools/ingest_local.py 호출 확인")
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_at_sign_does_not_crash(self) -> None:
        from tools.answer import build_contexts

        try:
            contexts = build_contexts("test @foo bar")
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_double_quote_does_not_crash(self) -> None:
        from tools.answer import build_contexts

        try:
            contexts = build_contexts('"hello world" test')
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_mixed_special_chars_does_not_crash(self) -> None:
        from tools.answer import build_contexts

        try:
            contexts = build_contexts("OpenClaw/Discord 테스트")
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_discord_agent_smoke_test_does_not_crash(self) -> None:
        from tools.answer import build_contexts

        try:
            contexts = build_contexts("discord_agent_smoke_test")
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_foo_bar_baz_does_not_crash(self) -> None:
        from tools.answer import build_contexts

        try:
            contexts = build_contexts("foo/bar baz")
        except Exception as exc:
            self.fail(f"build_contexts raised {type(exc).__name__}: {exc}")
        self.assertIsInstance(contexts, list)

    def test_empty_results_formats_helpfully(self) -> None:
        """When no results found, answer should not crash."""
        from tools.answer import build_contexts, format_answer_text

        contexts = build_contexts("zzzzz_nonexistent_xxxxx")
        text = format_answer_text("zzzzz_nonexistent_xxxxx", contexts)
        self.assertIn("찾을 수 없습니다", text)
        self.assertIn("N/A", text)


if __name__ == "__main__":
    unittest.main()
