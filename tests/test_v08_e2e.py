from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables


FIXTURE_SOURCE_ID = "local_v08_e2e"
FIXTURE_TEXT = "Patch 7.5 includes adjustments to Gunbreaker. No Mercy duration was changed."
QUESTION = "건브 7.5 변경점 알려줘"


class V08EndToEndSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.wiki_root = self.root / "wiki"
        self.summary_dir = self.wiki_root / "source_summaries"
        self.entities_dir = self.root / "data" / "ffxiv_entities"
        self.graph_dir = self.root / "graph"
        self.summary_dir.mkdir(parents=True)
        self.entities_dir.mkdir(parents=True)
        self._write_registry()
        self._write_summary(FIXTURE_SOURCE_ID, FIXTURE_TEXT)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _write_registry(self) -> None:
        (self.entities_dir / "jobs.json").write_text(
            json.dumps(
                [
                    {
                        "type": "Job",
                        "canonical": "Gunbreaker",
                        "slug": "gunbreaker",
                        "aliases": ["Gunbreaker", "GNB", "건브", "건브레이커"],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.entities_dir / "skills.json").write_text(
            json.dumps(
                [
                    {
                        "type": "Skill",
                        "canonical": "No Mercy",
                        "slug": "no_mercy",
                        "aliases": ["No Mercy", "노 머시", "노머시"],
                        "job": "Gunbreaker",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (self.entities_dir / "patches.json").write_text(
            json.dumps(
                [
                    {
                        "type": "Patch",
                        "canonical": "Patch 7.5",
                        "slug": "7_5",
                        "aliases": ["7.5", "Patch 7.5", "패치 7.5"],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _write_summary(self, source_id: str, body: str) -> None:
        (self.summary_dir / f"{source_id}.md").write_text(
            f"# Fixture {source_id}\n\n> Source: `{source_id}`\n\n---\n\n{body}\n",
            encoding="utf-8",
        )

    def _rebuild(self) -> dict[str, object]:
        from tools.rebuild_domain_graph import rebuild_domain_graph

        return rebuild_domain_graph(
            db_path=self.db_path,
            wiki_root=self.wiki_root,
            entities_dir=self.entities_dir,
            graph_dir=self.graph_dir,
            reset_domain_graph=True,
        )

    def _generate_derived_wiki(self) -> dict[str, object]:
        from src.domain_graph.derived_wiki import generate_derived_wiki

        conn = sqlite3.connect(self.db_path)
        try:
            return generate_derived_wiki(conn, self.wiki_root, self.graph_dir)
        finally:
            conn.close()

    def _run_pipeline(self) -> None:
        ensure_wiki_tables(self.db_path)
        self._rebuild()
        self._generate_derived_wiki()
        from tools.compile_wiki import index_wiki_documents

        index_wiki_documents(root_path=self.root, db_path=self.db_path)

    def _fetch_ids(self, table: str, where: str, params: tuple[object, ...] = ()) -> set[str]:
        return self._fetch_values(table, "id", where, params)

    def _fetch_values(
        self,
        table: str,
        column: str,
        where: str,
        params: tuple[object, ...] = (),
    ) -> set[str]:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(f"SELECT {column} FROM {table} WHERE {where}", params).fetchall()
        finally:
            conn.close()
        return {row[0] for row in rows}

    def test_e2e_entity_extraction(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities
        from src.domain_graph.entity_registry import load_entity_registry

        registry = load_entity_registry(self.entities_dir)
        entities = extract_entities(FIXTURE_TEXT, registry)

        self.assertEqual(
            {entity.node_id for entity in entities},
            {"job:gunbreaker", "patch:7_5", "skill:no_mercy"},
        )

    def test_e2e_domain_graph_rebuild(self) -> None:
        result = self._rebuild()

        self.assertEqual(result["status"], "ok")
        node_ids = self._fetch_ids("graph_nodes", "1 = 1")
        edge_types = self._fetch_values("graph_edges", "type", "1 = 1")

        self.assertIn("job:gunbreaker", node_ids)
        self.assertIn("patch:7_5", node_ids)
        self.assertIn("skill:no_mercy", node_ids)
        self.assertTrue(any(node_id.startswith("fact:") for node_id in node_ids))
        self.assertTrue(
            {
                "MENTIONS",
                "SUPPORTS",
                "AFFECTS_JOB",
                "AFFECTS_SKILL",
                "VALID_IN_PATCH",
            }
            <= edge_types
        )

    def test_e2e_derived_wiki_generation(self) -> None:
        self._rebuild()
        result = self._generate_derived_wiki()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.wiki_root / "jobs" / "gunbreaker.md").exists())
        self.assertTrue((self.wiki_root / "patches" / "7_5.md").exists())
        self.assertTrue((self.wiki_root / "skills" / "no_mercy.md").exists())

    def test_e2e_graph_report(self) -> None:
        self._rebuild()

        report_path = self.graph_dir / "GRAPH_REPORT.md"
        self.assertTrue(report_path.exists())
        self.assertIn("## Summary", report_path.read_text(encoding="utf-8"))

    def test_e2e_hybrid_retrieval(self) -> None:
        self._run_pipeline()

        from src.retrieval.hybrid import (
            load_entity_index,
            match_query_entities,
            retrieve_graph_neighborhood,
        )

        entity_index = load_entity_index(self.graph_dir)
        matches = match_query_entities(QUESTION, entity_index)
        self.assertEqual(matches, ("job:gunbreaker", "patch:7_5"))

        conn = sqlite3.connect(self.db_path)
        try:
            graph_results = retrieve_graph_neighborhood(conn, matches)
        finally:
            conn.close()
        self.assertTrue(any(result.source_id == FIXTURE_SOURCE_ID for result in graph_results))
        self.assertTrue(any("No Mercy duration" in result.snippet for result in graph_results))

    def test_e2e_ask_uses_fts_and_graph_context(self) -> None:
        self._run_pipeline()

        result = _run_ask(
            [
                QUESTION,
                "--db-path",
                str(self.db_path),
                "--root-path",
                str(self.root),
                "--graph-dir",
                str(self.graph_dir),
            ]
        )

        context_ids = {context["page_id"] for context in result["contexts"]}
        context_types = {context["wiki_type"] for context in result["contexts"]}
        answer_body = result["answer"]["body"]

        self.assertEqual(result["status"], "ok")
        self.assertIn("job_gunbreaker", context_ids)
        self.assertIn("source_summary", context_types)
        self.assertIn("No Mercy duration was changed.", answer_body)


def _run_ask(args: list[str]) -> dict[str, object]:
    from tools.ask import main

    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(args)
    return json.loads(stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
