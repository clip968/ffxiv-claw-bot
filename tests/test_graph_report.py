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


class GraphReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.graph_dir = Path(self._tmp_dir.name) / "graph"
        self.conn = sqlite3.connect(":memory:")
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        ensure_graph_schema(self.conn)
        upsert_node(self.conn, {"id": "src:local_v08", "type": "SourceDocument", "name": "local_v08"})
        upsert_node(self.conn, {"id": "job:gunbreaker", "type": "Job", "name": "Gunbreaker"})
        upsert_node(self.conn, {"id": "patch:7_5", "type": "Patch", "name": "Patch 7.5"})
        upsert_node(self.conn, {"id": "skill:no_mercy", "type": "Skill", "name": "No Mercy"})
        upsert_node(
            self.conn,
            {
                "id": "fact:test",
                "type": "Fact",
                "name": "No Mercy duration was changed.",
                "properties": {"text": "No Mercy duration was changed."},
            },
        )
        upsert_edge(
            self.conn,
            {
                "source_node_id": "src:local_v08",
                "target_node_id": "job:gunbreaker",
                "relation_type": "MENTIONS",
                "source_id": "local_v08",
                "confidence": 0.9,
            },
        )
        upsert_edge(
            self.conn,
            {
                "source_node_id": "fact:test",
                "target_node_id": "patch:7_5",
                "relation_type": "VALID_IN_PATCH",
                "source_id": "local_v08",
                "confidence": 0.85,
            },
        )

    def tearDown(self) -> None:
        self.conn.close()
        self._tmp_dir.cleanup()

    def _report_text(self) -> str:
        from src.domain_graph.report import generate_graph_report

        generate_graph_report(self.conn, self.graph_dir)
        return (self.graph_dir / "GRAPH_REPORT.md").read_text(encoding="utf-8")

    def test_report_file_created(self) -> None:
        from src.domain_graph.report import generate_graph_report

        result = generate_graph_report(self.conn, self.graph_dir)

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.graph_dir / "GRAPH_REPORT.md").exists())

    def test_report_has_summary_section(self) -> None:
        self.assertIn("## Summary", self._report_text())

    def test_report_has_node_counts(self) -> None:
        text = self._report_text()

        self.assertIn("## Node Counts", text)
        self.assertIn("- Job: 1", text)

    def test_report_has_edge_counts(self) -> None:
        text = self._report_text()

        self.assertIn("## Edge Counts", text)
        self.assertIn("- MENTIONS: 1", text)

    def test_report_has_top_mentioned_jobs(self) -> None:
        text = self._report_text()

        self.assertIn("## Top Mentioned Jobs", text)
        self.assertIn("Gunbreaker", text)

    def test_report_has_quality_warnings(self) -> None:
        self.assertIn("## Quality Warnings", self._report_text())


if __name__ == "__main__":
    unittest.main()
