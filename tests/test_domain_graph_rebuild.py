from __future__ import annotations

import sqlite3
import unittest


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


if __name__ == "__main__":
    unittest.main()
