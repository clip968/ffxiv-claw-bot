from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


class DomainGraphStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        from src.domain_graph.storage import ensure_graph_schema

        ensure_graph_schema(self.conn)

    def tearDown(self) -> None:
        self.conn.close()

    def test_upsert_node_idempotent(self) -> None:
        from src.domain_graph.storage import upsert_node

        node = {
            "id": "job:gunbreaker",
            "type": "Job",
            "name": "Gunbreaker",
            "canonical_name": "Gunbreaker",
            "aliases": ["Gunbreaker", "GNB"],
            "properties": {"role": "Tank"},
        }

        upsert_node(self.conn, node)
        upsert_node(self.conn, node)

        count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_nodes WHERE id = ?",
            ("job:gunbreaker",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_upsert_edge_idempotent(self) -> None:
        from src.domain_graph.storage import upsert_edge

        edge = {
            "id": "edge:test",
            "source_node_id": "job:gunbreaker",
            "target_node_id": "skill:no_mercy",
            "relation_type": "HAS_SKILL",
            "source_id": None,
            "confidence": 1.0,
            "properties": {"source": "registry"},
        }

        upsert_edge(self.conn, edge)
        upsert_edge(self.conn, edge)

        count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_edges WHERE id = ?",
            ("edge:test",),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_fact_id_deterministic(self) -> None:
        from src.domain_graph.storage import make_fact_id

        first = make_fact_id(
            "local_v08_fixture",
            "skill:no_mercy",
            "CHANGED_IN",
            "patch:7_5",
            "No Mercy duration was changed.",
        )
        second = make_fact_id(
            "local_v08_fixture",
            "skill:no_mercy",
            "CHANGED_IN",
            "patch:7_5",
            "No Mercy duration was changed.",
        )

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("fact:"))

    def test_provenance_graph_preserved(self) -> None:
        from src.domain_graph.storage import reset_domain_graph, upsert_edge, upsert_node

        upsert_node(
            self.conn,
            {
                "id": "src:local_v08_fixture",
                "type": "SourceDocument",
                "name": "local_v08_fixture",
            },
        )
        upsert_node(
            self.conn,
            {
                "id": "page:wiki_local_v08_fixture",
                "type": "WikiPage",
                "name": "Fixture Summary",
            },
        )
        upsert_node(
            self.conn,
            {
                "id": "job:gunbreaker",
                "type": "Job",
                "name": "Gunbreaker",
            },
        )
        upsert_edge(
            self.conn,
            {
                "id": "edge:source-of",
                "source_node_id": "src:local_v08_fixture",
                "target_node_id": "page:wiki_local_v08_fixture",
                "relation_type": "SOURCE_OF",
                "confidence": 1.0,
            },
        )
        upsert_edge(
            self.conn,
            {
                "id": "edge:mentions",
                "source_node_id": "src:local_v08_fixture",
                "target_node_id": "job:gunbreaker",
                "relation_type": "MENTIONS",
                "confidence": 0.9,
            },
        )

        reset_domain_graph(self.conn)

        provenance_node_count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_nodes WHERE type IN ('SourceDocument', 'WikiPage')"
        ).fetchone()[0]
        domain_node_count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_nodes WHERE type = 'Job'"
        ).fetchone()[0]
        provenance_edge_count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_edges WHERE type = 'SOURCE_OF'"
        ).fetchone()[0]
        domain_edge_count = self.conn.execute(
            "SELECT COUNT(*) FROM graph_edges WHERE type = 'MENTIONS'"
        ).fetchone()[0]

        self.assertEqual(provenance_node_count, 2)
        self.assertEqual(domain_node_count, 0)
        self.assertEqual(provenance_edge_count, 1)
        self.assertEqual(domain_edge_count, 0)


class DomainGraphRebuildCliTests(unittest.TestCase):
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
        self._write_summary(
            "local_v08_a",
            "Patch 7.5 includes adjustments to Gunbreaker. No Mercy duration was changed.",
        )

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
                        "aliases": ["No Mercy"],
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

    def _rebuild(self, **kwargs):
        from tools.rebuild_domain_graph import rebuild_domain_graph

        return rebuild_domain_graph(
            db_path=self.db_path,
            wiki_root=self.wiki_root,
            entities_dir=self.entities_dir,
            graph_dir=self.graph_dir,
            **kwargs,
        )

    def _count(self, table: str, where: str, params: tuple[object, ...] = ()) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
        finally:
            conn.close()

    def test_rebuild_creates_domain_nodes(self) -> None:
        result = self._rebuild()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(self._count("graph_nodes", "type = 'Job'"), 1)
        self.assertEqual(self._count("graph_nodes", "type = 'Patch'"), 1)
        self.assertEqual(self._count("graph_nodes", "type = 'Skill'"), 1)

    def test_rebuild_creates_mentions_edges(self) -> None:
        self._rebuild()

        self.assertGreaterEqual(self._count("graph_edges", "type = 'MENTIONS'"), 3)

    def test_rebuild_creates_fact_with_trigger(self) -> None:
        self._rebuild()

        self.assertEqual(self._count("graph_nodes", "type = 'Fact'"), 1)
        self.assertEqual(self._count("graph_edges", "type = 'SUPPORTS'"), 1)

    def test_rebuild_idempotent(self) -> None:
        self._rebuild()
        first_counts = (
            self._count("graph_nodes", "1 = 1"),
            self._count("graph_edges", "1 = 1"),
        )
        self._rebuild()
        second_counts = (
            self._count("graph_nodes", "1 = 1"),
            self._count("graph_edges", "1 = 1"),
        )

        self.assertEqual(first_counts, second_counts)

    def test_dry_run_no_db_change(self) -> None:
        result = self._rebuild(dry_run=True)

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["dry_run"])
        self.assertFalse(self.db_path.exists())

    def test_source_id_filter(self) -> None:
        self._write_summary(
            "local_v08_b",
            "Patch 7.5 mentions Gunbreaker without a change trigger.",
        )

        self._rebuild(source_id="local_v08_b")

        self.assertEqual(self._count("graph_nodes", "id = 'src:local_v08_b'"), 1)
        self.assertEqual(self._count("graph_nodes", "id = 'src:local_v08_a'"), 0)

    def test_reset_preserves_provenance(self) -> None:
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        conn = sqlite3.connect(self.db_path)
        try:
            ensure_graph_schema(conn)
            upsert_node(conn, {"id": "src:manual", "type": "SourceDocument", "name": "manual"})
            upsert_node(conn, {"id": "page:manual", "type": "WikiPage", "name": "Manual"})
            upsert_edge(
                conn,
                {
                    "id": "edge:manual",
                    "source_node_id": "src:manual",
                    "target_node_id": "page:manual",
                    "relation_type": "SOURCE_OF",
                    "confidence": 1.0,
                },
            )
        finally:
            conn.close()

        self._rebuild(reset_domain_graph=True)

        self.assertEqual(self._count("graph_edges", "id = 'edge:manual'"), 1)


if __name__ == "__main__":
    unittest.main()
