from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools import compile_wiki


def create_drive_source_db(db_path: Path, raw_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sources (
              id TEXT PRIMARY KEY,
              source_type TEXT NOT NULL,
              title TEXT,
              source_url TEXT,
              raw_path TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              language TEXT,
              patch TEXT,
              job TEXT,
              raid TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
        """)
        conn.execute(
            """
            INSERT INTO sources (id, source_type, title, source_url, raw_path, content_hash, created_at, updated_at)
            VALUES (?, 'drive_document', ?, ?, ?, ?, '2026-05-14T00:00:00', '2026-05-14T00:00:00')
            """,
            ("drive_test_source", "Black Mage 7.5 Guide", "gdrive://drive_file_001", str(raw_path), "hash-test"),
        )
        conn.commit()
    finally:
        conn.close()


def ensure_wiki_tables(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sources (
              id TEXT PRIMARY KEY,
              source_type TEXT NOT NULL,
              title TEXT,
              source_url TEXT,
              raw_path TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              language TEXT,
              patch TEXT,
              job TEXT,
              raid TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS wiki_pages (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              title TEXT NOT NULL,
              path TEXT NOT NULL,
              patch TEXT,
              job TEXT,
              raid TEXT,
              source_ids TEXT NOT NULL,
              confidence TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
              page_id, title, body, tokenize = 'unicode61'
            );
        """)
        conn.commit()
    finally:
        conn.close()


class CompileWikiDriveTests(unittest.TestCase):
    def test_extract_text_works_without_optional_bs4_dependency(self) -> None:
        html = """
        <html>
          <head><style>.hidden { display: none; }</style></head>
          <body>
            <nav>Navigation</nav>
            <main><h1>Guide Title</h1><p>Useful body text.</p></main>
            <script>alert("skip")</script>
          </body>
        </html>
        """

        text = compile_wiki.extract_text(html)

        self.assertIn("Guide Title", text)
        self.assertIn("Useful body text.", text)
        self.assertNotIn("Navigation", text)
        self.assertNotIn("alert", text)

    def test_compile_for_drive_document_uses_raw_markdown_without_html_extraction(self) -> None:
        """drive_document source should preserve raw markdown content (skip HTML parsing)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            raw_path = tmp_root / "raw_file.md"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text("# Test Heading\n\nTest paragraph.", encoding="utf-8")

            db_path = tmp_root / "test.db"
            ensure_wiki_tables(db_path)
            create_drive_source_db(db_path, str(raw_path))

            original_root = compile_wiki.ROOT
            original_db_path = compile_wiki.DB_PATH
            original_summary_dir = compile_wiki.SUMMARY_DIR
            compile_wiki.ROOT = tmp_root
            compile_wiki.DB_PATH = db_path
            compile_wiki.SUMMARY_DIR = tmp_root / "wiki" / "source_summaries"

            try:
                result = compile_wiki.compile_for_source("drive_test_source")
            finally:
                compile_wiki.ROOT = original_root
                compile_wiki.DB_PATH = original_db_path
                compile_wiki.SUMMARY_DIR = original_summary_dir

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["source_type"], "drive_document")
            self.assertEqual(result["char_count"], len("# Test Heading\n\nTest paragraph."))

            # Summary file preserves markdown content (no HTML stripping)
            summary_path = tmp_root / "wiki" / "source_summaries" / "drive_test_source.md"
            self.assertTrue(summary_path.exists())
            summary_content = summary_path.read_text(encoding="utf-8")
            self.assertIn("# Test Heading", summary_content)

            # FTS entry has markdown content preserved
            conn = sqlite3.connect(db_path)
            try:
                fts_row = conn.execute(
                    "SELECT page_id, title, body FROM wiki_fts WHERE page_id = ?",
                    ("wiki_drive_test_source",),
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(fts_row)
            self.assertEqual(fts_row[1], "Black Mage 7.5 Guide")
            self.assertIn("Test paragraph.", fts_row[2])

    def test_compile_for_local_file_preserves_raw_content(self) -> None:
        """local_file source should preserve raw markdown content (skip HTML parsing)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            raw_path = tmp_root / "raw_macro.md"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(
                "Use &lt;wait.3&gt; for the opener macro\n& <se.1> after.",
                encoding="utf-8",
            )

            db_path = tmp_root / "test.db"
            ensure_wiki_tables(db_path)
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO sources (id, source_type, title, source_url, raw_path, content_hash, created_at, updated_at)
                    VALUES (?, 'local_file', ?, ?, ?, ?, '2026-05-14T00:00:00', '2026-05-14T00:00:00')
                    """,
                    ("local_file_test", "Black Mage Macro", "local://sources/macros/black_mage.md", str(raw_path), "hash-1"),
                )
                conn.commit()
            finally:
                conn.close()

            original_root = compile_wiki.ROOT
            original_db_path = compile_wiki.DB_PATH
            original_summary_dir = compile_wiki.SUMMARY_DIR
            compile_wiki.ROOT = tmp_root
            compile_wiki.DB_PATH = db_path
            compile_wiki.SUMMARY_DIR = tmp_root / "wiki" / "source_summaries"

            try:
                result = compile_wiki.compile_for_source("local_file_test")
            finally:
                compile_wiki.ROOT = original_root
                compile_wiki.DB_PATH = original_db_path
                compile_wiki.SUMMARY_DIR = original_summary_dir

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["source_type"], "local_file")

            # FTS should preserve raw content (HTML entities not converted, markup not stripped)
            conn = sqlite3.connect(db_path)
            try:
                fts_row = conn.execute(
                    "SELECT body FROM wiki_fts WHERE page_id = ?",
                    ("wiki_local_file_test",),
                ).fetchone()
            finally:
                conn.close()

            self.assertIsNotNone(fts_row)
            self.assertIn("&lt;wait.3&gt;", fts_row[0],
                          "HTML entities should be preserved for local_file sources")
            self.assertIn("<se.1>", fts_row[0],
                          "Angle brackets should be preserved for local_file sources")


if __name__ == "__main__":
    unittest.main()
