from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables


def _run_ask(args: list[str]) -> dict[str, object]:
    from tools.ask import main

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(args)
    return json.loads(stdout.getvalue())


def _context(
    *,
    page_id: str,
    wiki_type: str,
    title: str,
    path: str,
    content: str,
    source_ids: tuple[str, ...] = (),
) -> object:
    from src.retrieval import ContextDocument

    return ContextDocument(
        page_id=page_id,
        wiki_type=wiki_type,
        title=title,
        path=path,
        score=1.0,
        snippet=content[:160],
        content_excerpt=content,
        source_ids=source_ids,
    )


def _context_pack(contexts: tuple[object, ...], question: str) -> object:
    from src.query import parse_query
    from src.retrieval import AskContextPack, build_retrieval_plan

    parsed = parse_query(question)
    return AskContextPack(
        question=question,
        parsed_query=parsed,
        retrieval_plan=build_retrieval_plan(parsed),
        contexts=contexts,
        confidence="source_grounded" if contexts else "N/A",
    )


class V085OfficialJobGuideExtractionTests(unittest.TestCase):
    def test_official_job_guide_html_removes_cross_job_nav_and_records_job(self) -> None:
        from src.source_processing.extractors.html import extract_html_file

        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "gunbreaker.html"
            source_path.write_text(
                """
                <html>
                  <head><title>Job Guide: Gunbreaker | FINAL FANTASY XIV</title></head>
                  <body>
                    <main>
                      <h1>Job Guide: Gunbreaker | FINAL FANTASY XIV</h1>
                      <section class="job__menu">
                        <a>Paladin</a><a>Black Mage</a><a>Gunbreaker</a>
                      </section>
                      <section class="job__actions">
                        <h2>Job Actions</h2>
                        <div>Keen Edge</div>
                        <div>Continuation</div>
                      </section>
                    </main>
                  </body>
                </html>
                """,
                encoding="utf-8",
            )

            extracted = extract_html_file(source_path)

        self.assertEqual(extracted.metadata["official_job"], "gunbreaker")
        self.assertIn("Continuation", extracted.text)
        self.assertNotIn("Black Mage", extracted.text)
        self.assertNotIn("Paladin", extracted.text)


class V085SourceSummaryMetadataTests(unittest.TestCase):
    def test_official_job_guide_source_summary_indexes_job_metadata(self) -> None:
        from tools.compile_wiki import index_wiki_documents

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            db_path = root / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            summary_dir = root / "wiki" / "source_summaries"
            summary_dir.mkdir(parents=True)
            (summary_dir / "local_gnb.md").write_text(
                "# Official FFXIV Job Guide - Gunbreaker\n\n"
                "> Source: `local_gnb`\n\n"
                "---\n\n"
                "Job Guide: Gunbreaker | FINAL FANTASY XIV\n"
                "Paladin\n"
                "Black Mage\n"
                "Gunbreaker\n"
                "Actions & Traits\n"
                "Keen Edge\n"
                "Continuation\n",
                encoding="utf-8",
            )

            result = index_wiki_documents(root_path=root, db_path=db_path)
            conn = sqlite3.connect(db_path)
            try:
                row = conn.execute(
                    "SELECT type, job FROM wiki_pages WHERE id = ?",
                    ("wiki_local_gnb",),
                ).fetchone()
            finally:
                conn.close()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(row, ("source_summary", "gunbreaker"))


class V085JobSpecificRetrievalPrecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.graph_dir = self.root / "graph"
        self.summary_dir = self.root / "wiki" / "source_summaries"
        self.graph_dir.mkdir(parents=True)
        self.summary_dir.mkdir(parents=True)
        ensure_wiki_tables(self.db_path)
        self._write_entity_index()
        self._write_source_summary(
            "local_blm",
            "Official FFXIV Job Guide - Black Mage",
            "Job Guide: Black Mage | FINAL FANTASY XIV\nGunbreaker\nPaladin\nBlizzard\n",
        )
        self._write_source_summary(
            "local_gnb",
            "Official FFXIV Job Guide - Gunbreaker",
            "Job Guide: Gunbreaker | FINAL FANTASY XIV\nContinuation\nNo Mercy\n",
        )
        self._write_source_summary(
            "local_pld",
            "Official FFXIV Job Guide - Paladin",
            "Job Guide: Paladin | FINAL FANTASY XIV\nFight or Flight\n",
        )
        self._seed_graph()

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_gunbreaker_query_excludes_black_mage_job_guide_context(self) -> None:
        result = self._ask("Gunbreaker 스킬 알려줘")

        titles = [context["title"] for context in result["contexts"]]
        self.assertIn("Official FFXIV Job Guide - Gunbreaker", titles)
        self.assertNotIn("Official FFXIV Job Guide - Black Mage", titles)

    def test_paladin_query_excludes_black_mage_and_gunbreaker_job_guide_contexts(self) -> None:
        result = self._ask("Paladin 스킬 알려줘")

        titles = [context["title"] for context in result["contexts"]]
        self.assertIn("Official FFXIV Job Guide - Paladin", titles)
        self.assertNotIn("Official FFXIV Job Guide - Black Mage", titles)
        self.assertNotIn("Official FFXIV Job Guide - Gunbreaker", titles)

    def _ask(self, question: str) -> dict[str, object]:
        return _run_ask(
            [
                question,
                "--db-path",
                str(self.db_path),
                "--root-path",
                str(self.root),
                "--graph-dir",
                str(self.graph_dir),
            ]
        )

    def _write_entity_index(self) -> None:
        (self.graph_dir / "entity_index.json").write_text(
            json.dumps(
                {
                    "Gunbreaker": "job:gunbreaker",
                    "Paladin": "job:paladin",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _write_source_summary(self, source_id: str, title: str, body: str) -> None:
        (self.summary_dir / f"{source_id}.md").write_text(
            f"# {title}\n\n> Source: `{source_id}`\n\n---\n\n{body}",
            encoding="utf-8",
        )

    def _seed_graph(self) -> None:
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        conn = sqlite3.connect(self.db_path)
        try:
            ensure_graph_schema(conn)
            for node_id, name in (
                ("job:gunbreaker", "Gunbreaker"),
                ("job:paladin", "Paladin"),
            ):
                upsert_node(
                    conn,
                    {
                        "id": node_id,
                        "type": "Job",
                        "name": name,
                        "canonical_name": name,
                    },
                )
            for source_id, title, job in (
                ("local_blm", "Official FFXIV Job Guide - Black Mage", "black_mage"),
                ("local_gnb", "Official FFXIV Job Guide - Gunbreaker", "gunbreaker"),
                ("local_pld", "Official FFXIV Job Guide - Paladin", "paladin"),
            ):
                upsert_node(
                    conn,
                    {
                        "id": f"src:{source_id}",
                        "type": "SourceDocument",
                        "name": source_id,
                        "canonical_name": source_id,
                        "properties": {
                            "path": f"wiki/source_summaries/{source_id}.md",
                            "title": title,
                            "job": job,
                            "source_kind": "official_job_guide",
                        },
                    },
                )
            for source_id in ("local_blm", "local_gnb"):
                upsert_edge(
                    conn,
                    {
                        "source_node_id": f"src:{source_id}",
                        "target_node_id": "job:gunbreaker",
                        "relation_type": "MENTIONS",
                        "source_id": source_id,
                    },
                )
            for source_id in ("local_blm", "local_gnb", "local_pld"):
                upsert_edge(
                    conn,
                    {
                        "source_node_id": f"src:{source_id}",
                        "target_node_id": "job:paladin",
                        "relation_type": "MENTIONS",
                        "source_id": source_id,
                    },
                )
        finally:
            conn.close()


class V085AnswerComposerNoiseFilterTests(unittest.TestCase):
    def test_gunbreaker_change_answer_drops_job_guide_title_noise(self) -> None:
        from src.answering.composer import compose_answer

        context = _context(
            page_id="job_gunbreaker",
            wiki_type="job",
            title="Gunbreaker",
            path="wiki/jobs/gunbreaker.md",
            content=(
                "# Gunbreaker\n\n"
                "## Recent Facts\n"
                "- title: Official FFXIV Job Guide - Black Mage\n"
                "- No Mercy duration was changed.\n"
            ),
        )

        answer = compose_answer(_context_pack((context,), "건브 7.5 변경점"))

        self.assertIn("No Mercy duration was changed.", answer.body)
        self.assertNotIn("title: Official FFXIV Job Guide - Black Mage", answer.body)

    def test_continuation_answer_drops_patch_menu_and_location_noise(self) -> None:
        from src.answering.composer import compose_answer

        context = _context(
            page_id="skill_continuation",
            wiki_type="skill",
            title="Continuation",
            path="wiki/skills/continuation.md",
            content=(
                "# Continuation\n\n"
                "## Facts\n"
                "- Recast\n"
                "- The arrival coordinates when teleporting or returning to Solution Nine have been adjusted.\n"
                "- The name of the client for the Tuliyollal leve \"Shielding My Students\" has been changed.\n"
                "- Continuation can now be executed after Fated Brand.\n"
            ),
        )

        answer = compose_answer(_context_pack((context,), "Continuation 관련 변경 있어?"))

        self.assertIn("Continuation can now be executed after Fated Brand.", answer.body)
        self.assertNotIn("Recast", answer.body)
        self.assertNotIn("Solution Nine", answer.body)
        self.assertNotIn("leve", answer.body)


if __name__ == "__main__":
    unittest.main()
