from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


class V085RealGraphPopulationTests(unittest.TestCase):
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
        self._write_summary()

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
                        "role": "Tank",
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

    def _write_summary(self) -> None:
        source_id = "local_v08_5_graph_population"
        (self.summary_dir / f"{source_id}.md").write_text(
            "\n".join(
                [
                    "# Fixture Patch Note",
                    "",
                    f"> Source: `{source_id}`",
                    "",
                    "---",
                    "",
                    "Patch 7.5 includes Gunbreaker adjustments.",
                    "No Mercy duration was changed.",
                    "",
                ]
            ),
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
            verbose=True,
        )

    def _count_by_type(self, table: str, type_name: str) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE type = ?",
                (type_name,),
            ).fetchone()[0]
        finally:
            conn.close()

    def _total_counts(self) -> tuple[int, int]:
        conn = sqlite3.connect(self.db_path)
        try:
            nodes = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            edges = conn.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
            return nodes, edges
        finally:
            conn.close()

    def test_rebuild_creates_job_patch_skill_fact_nodes(self) -> None:
        result = self._rebuild()

        self.assertEqual(result["status"], "ok")
        self.assertGreater(self._count_by_type("graph_nodes", "Job"), 0)
        self.assertGreater(self._count_by_type("graph_nodes", "Patch"), 0)
        self.assertGreater(self._count_by_type("graph_nodes", "Skill"), 0)
        self.assertGreater(self._count_by_type("graph_nodes", "Fact"), 0)

    def test_rebuild_creates_required_edge_types(self) -> None:
        self._rebuild()

        self.assertGreater(self._count_by_type("graph_edges", "MENTIONS"), 0)
        self.assertGreater(self._count_by_type("graph_edges", "SUPPORTS"), 0)
        self.assertGreater(self._count_by_type("graph_edges", "VALID_IN_PATCH"), 0)
        self.assertGreater(self._count_by_type("graph_edges", "AFFECTS_JOB"), 0)
        self.assertGreater(self._count_by_type("graph_edges", "AFFECTS_SKILL"), 0)

    def test_rebuild_creates_graph_export_files(self) -> None:
        result = self._rebuild()

        self.assertEqual(result["export"]["status"], "ok")
        self.assertTrue((self.graph_dir / "nodes.json").exists())
        self.assertTrue((self.graph_dir / "edges.json").exists())
        self.assertTrue((self.graph_dir / "domain_graph.json").exists())
        self.assertTrue((self.graph_dir / "entity_index.json").exists())

        domain_graph = json.loads((self.graph_dir / "domain_graph.json").read_text(encoding="utf-8"))
        entity_index = json.loads((self.graph_dir / "entity_index.json").read_text(encoding="utf-8"))

        self.assertGreater(domain_graph["metadata"]["node_count"], 0)
        self.assertEqual(entity_index["gunbreaker"], "job:gunbreaker")
        self.assertEqual(entity_index["no mercy"], "skill:no_mercy")

    def test_rebuild_idempotent(self) -> None:
        self._rebuild()
        first_counts = self._total_counts()

        self._rebuild()
        second_counts = self._total_counts()

        self.assertEqual(first_counts, second_counts)

    def test_export_tolerates_legacy_source_of_confidence(self) -> None:
        from src.domain_graph.export import export_graph
        from src.domain_graph.storage import ensure_graph_schema

        conn = sqlite3.connect(self.db_path)
        try:
            ensure_graph_schema(conn)
            conn.execute(
                """
                INSERT INTO graph_nodes (id, type, name)
                VALUES ('src:legacy', 'SourceDocument', 'legacy source')
                """
            )
            conn.execute(
                """
                INSERT INTO graph_nodes (id, type, name)
                VALUES ('page:legacy', 'WikiPage', 'legacy page')
                """
            )
            conn.execute(
                """
                INSERT INTO graph_edges (id, source_id, target_id, type, confidence)
                VALUES ('edge:legacy', 'src:legacy', 'page:legacy', 'SOURCE_OF', 'EXTRACTED')
                """
            )
            conn.commit()

            result = export_graph(conn, self.graph_dir)
        finally:
            conn.close()

        self.assertEqual(result["status"], "ok")
        edges = json.loads((self.graph_dir / "edges.json").read_text(encoding="utf-8"))
        legacy_edge = next(edge for edge in edges if edge["id"] == "edge:legacy")
        self.assertIsNone(legacy_edge["confidence"])


if __name__ == "__main__":
    unittest.main()
