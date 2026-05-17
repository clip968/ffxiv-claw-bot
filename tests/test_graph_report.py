from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


class GraphExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.graph_dir = Path(self._tmp_dir.name) / "graph"
        self.conn = sqlite3.connect(":memory:")
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        ensure_graph_schema(self.conn)
        upsert_node(
            self.conn,
            {
                "id": "job:gunbreaker",
                "type": "Job",
                "name": "Gunbreaker",
                "canonical_name": "Gunbreaker",
                "aliases": ["Gunbreaker", "GNB", "건브"],
                "properties": {"role": "Tank"},
            },
        )
        upsert_node(
            self.conn,
            {
                "id": "skill:no_mercy",
                "type": "Skill",
                "name": "No Mercy",
                "canonical_name": "No Mercy",
                "aliases": ["No Mercy"],
                "properties": {"job": "Gunbreaker"},
            },
        )
        upsert_edge(
            self.conn,
            {
                "id": "edge:has-skill",
                "source_node_id": "job:gunbreaker",
                "target_node_id": "skill:no_mercy",
                "relation_type": "HAS_SKILL",
                "confidence": 1.0,
                "properties": {"source": "registry"},
            },
        )

    def tearDown(self) -> None:
        self.conn.close()
        self._tmp_dir.cleanup()

    def _export(self) -> dict:
        from src.domain_graph.export import export_graph

        return export_graph(self.conn, self.graph_dir)

    def test_nodes_json_created(self) -> None:
        result = self._export()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.graph_dir / "nodes.json").exists())

    def test_edges_json_created(self) -> None:
        self._export()

        self.assertTrue((self.graph_dir / "edges.json").exists())

    def test_domain_graph_json_has_metadata(self) -> None:
        self._export()

        payload = json.loads((self.graph_dir / "domain_graph.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["metadata"]["schema_version"], "v08")
        self.assertEqual(payload["metadata"]["node_count"], 2)
        self.assertEqual(payload["metadata"]["edge_count"], 1)

    def test_entity_index_has_aliases(self) -> None:
        self._export()

        payload = json.loads((self.graph_dir / "entity_index.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["gnb"], "job:gunbreaker")
        self.assertEqual(payload["건브"], "job:gunbreaker")
        self.assertEqual(payload["no mercy"], "skill:no_mercy")

    def test_json_is_valid(self) -> None:
        self._export()

        for filename in ("nodes.json", "edges.json", "domain_graph.json", "entity_index.json"):
            json.loads((self.graph_dir / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
