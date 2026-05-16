from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables
from tests.test_v05_process_source import ensure_sources_schema


class V06WikiDocumentScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        source_dir = self.root / "wiki" / "source_summaries"
        job_dir = self.root / "wiki" / "jobs"
        source_dir.mkdir(parents=True)
        job_dir.mkdir(parents=True)
        (source_dir / "patch_7_0.md").write_text(
            "# Patch 7.0 Notes\n\nsource_id: patch_7_0\n\nGunbreaker changed.\n",
            encoding="utf-8",
        )
        (job_dir / "gunbreaker.md").write_text(
            "# Gunbreaker 변경 이력\n\n## 7.0\n\n- Continuation potency adjusted.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _documents_by_path(self):
        from src.wiki_indexing.wiki_document_scanner import scan_wiki_documents

        return {doc.path.as_posix(): doc for doc in scan_wiki_documents(self.root)}

    def test_fts_scanner_includes_source_summaries(self) -> None:
        documents = self._documents_by_path()

        self.assertIn((self.root / "wiki/source_summaries/patch_7_0.md").as_posix(), documents)

    def test_fts_scanner_includes_job_wiki_pages(self) -> None:
        documents = self._documents_by_path()

        self.assertIn((self.root / "wiki/jobs/gunbreaker.md").as_posix(), documents)

    def test_fts_scanner_sets_wiki_type_for_source_summaries(self) -> None:
        documents = self._documents_by_path()
        doc = documents[(self.root / "wiki/source_summaries/patch_7_0.md").as_posix()]

        self.assertEqual(doc.wiki_type, "source_summary")

    def test_fts_scanner_sets_wiki_type_for_job_pages(self) -> None:
        documents = self._documents_by_path()
        doc = documents[(self.root / "wiki/jobs/gunbreaker.md").as_posix()]

        self.assertEqual(doc.wiki_type, "job")

    def test_fts_scanner_sets_topic_from_job_filename(self) -> None:
        documents = self._documents_by_path()
        doc = documents[(self.root / "wiki/jobs/gunbreaker.md").as_posix()]

        self.assertEqual(doc.topic, "gunbreaker")
        self.assertEqual(doc.page_id, "job_gunbreaker")


class V06WikiFtsIndexingTests(unittest.TestCase):
    def test_index_wiki_documents_indexes_job_wiki_pages(self) -> None:
        from tools.compile_wiki import index_wiki_documents

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            job_dir = root / "wiki" / "jobs"
            job_dir.mkdir(parents=True)
            (job_dir / "gunbreaker.md").write_text(
                "# Gunbreaker 변경 이력\n\nContinuation potency adjusted.\n",
                encoding="utf-8",
            )

            result = index_wiki_documents(root_path=root, db_path=db_path)

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["summary"]["indexed"], 1)
            conn = sqlite3.connect(str(db_path))
            try:
                page = conn.execute(
                    "SELECT type, job FROM wiki_pages WHERE id = ?",
                    ("job_gunbreaker",),
                ).fetchone()
                fts = conn.execute(
                    "SELECT title, body FROM wiki_fts WHERE page_id = ?",
                    ("job_gunbreaker",),
                ).fetchone()
            finally:
                conn.close()

        self.assertEqual(page, ("job", "gunbreaker"))
        self.assertIsNotNone(fts)
        self.assertIn("Gunbreaker", fts[0])
        self.assertIn("Continuation potency", fts[1])

    def test_existing_source_summary_indexing_still_works(self) -> None:
        from tools import compile_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "ffxiv.sqlite"
            raw_path = root / "raw" / "local.md"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_text("Gunbreaker changed in this source.", encoding="utf-8")
            ensure_sources_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            try:
                conn.execute(
                    """
                    INSERT INTO sources (
                        id, source_type, title, source_url, raw_path, content_hash,
                        created_at, updated_at
                    )
                    VALUES (?, 'local_document', ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "local_test_source",
                        "Patch Source",
                        "local://sources/patch.md",
                        str(raw_path),
                        "hash",
                        "2026-05-16T00:00:00+00:00",
                        "2026-05-16T00:00:00+00:00",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            result = compile_wiki.compile_for_source(
                "local_test_source",
                db_path=db_path,
                root_path=root,
                summary_dir=root / "wiki" / "source_summaries",
            )

            conn = sqlite3.connect(str(db_path))
            try:
                fts = conn.execute(
                    "SELECT title, body FROM wiki_fts WHERE page_id = ?",
                    ("wiki_local_test_source",),
                ).fetchone()
            finally:
                conn.close()

        self.assertEqual(result["status"], "ok")
        self.assertIsNotNone(fts)
        self.assertEqual(fts[0], "Patch Source")
        self.assertIn("Gunbreaker changed", fts[1])


if __name__ == "__main__":
    unittest.main()
