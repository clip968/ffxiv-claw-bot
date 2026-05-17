from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.guide_ff14.models import GuideItem
from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_item


class GuideFF14ItemGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.db_path = self.root / "ffxiv.sqlite"
        self.wiki_root = self.root / "wiki"
        self.entities_dir = self.root / "data" / "ffxiv_entities"
        self.graph_dir = self.root / "graph"
        self.entities_dir.mkdir(parents=True)
        self.wiki_root.mkdir(parents=True)
        self._write_empty_registry()
        self._seed_item()

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_rebuild_creates_item_node(self) -> None:
        self._rebuild(reset_domain_graph=True)

        self.assertEqual(self._node_count("Item"), 1)
        self.assertEqual(self._node_name("item:5398978e726"), "영웅의 건블레이드")

    def test_category_job_source_level_and_provenance_edges_are_created(self) -> None:
        self._rebuild(reset_domain_graph=True)

        self.assertEqual(self._node_count("ItemCategory"), 1)
        self.assertEqual(self._node_count("EquipmentJob"), 2)
        self.assertEqual(self._node_count("ItemSource"), 1)
        self.assertEqual(self._edge_count("ITEM_IN_CATEGORY"), 1)
        self.assertEqual(self._edge_count("EQUIPPABLE_BY_JOB"), 2)
        self.assertEqual(self._edge_count("HAS_ITEM_LEVEL"), 1)
        self.assertEqual(self._edge_count("HAS_EQUIP_LEVEL"), 1)
        self.assertEqual(self._edge_count("OBTAINED_FROM"), 1)
        self.assertEqual(self._edge_count("DERIVED_FROM"), 1)

    def test_graph_report_includes_item_count(self) -> None:
        self._rebuild(reset_domain_graph=True)

        report = (self.graph_dir / "GRAPH_REPORT.md").read_text(encoding="utf-8")

        self.assertIn("- Item: 1", report)
        self.assertIn("- ITEM_IN_CATEGORY: 1", report)

    def test_rebuild_is_idempotent_for_item_graph(self) -> None:
        self._rebuild(reset_domain_graph=True)
        first_counts = self._counts()
        self._rebuild(reset_domain_graph=True)
        second_counts = self._counts()

        self.assertEqual(first_counts, second_counts)

    def _write_empty_registry(self) -> None:
        for filename in ("jobs.json", "skills.json", "patches.json"):
            (self.entities_dir / filename).write_text("[]", encoding="utf-8")

    def _seed_item(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            ensure_guide_ff14_schema(conn)
            upsert_item(
                conn,
                GuideItem(
                    id="5398978e726",
                    name="영웅의 건블레이드",
                    name_ko="영웅의 건블레이드",
                    url="https://guide.ff14.co.kr/lodestone/db/item/5398978e726",
                    category="무기",
                    subcategory="건블레이드",
                    item_level=700,
                    equip_level=100,
                    jobs=["건브레이커", "Gunbreaker"],
                    stats={"힘": 123},
                    source={"text": "토벌전 보상", "type": "duty"},
                    description="건브레이커 무기입니다.",
                    content_hash="hash-a",
                    raw_path="data/raw/guide_ff14/items/5398978e726.html",
                ),
                now="2026-05-17T00:00:00+00:00",
            )
        finally:
            conn.close()

    def _rebuild(self, **kwargs: object) -> dict:
        from tools.rebuild_domain_graph import rebuild_domain_graph

        return rebuild_domain_graph(
            db_path=self.db_path,
            wiki_root=self.wiki_root,
            entities_dir=self.entities_dir,
            graph_dir=self.graph_dir,
            **kwargs,
        )

    def _node_count(self, node_type: str) -> int:
        return self._count("graph_nodes", "type = ?", (node_type,))

    def _edge_count(self, edge_type: str) -> int:
        return self._count("graph_edges", "type = ?", (edge_type,))

    def _node_name(self, node_id: str) -> str:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(
                "SELECT name FROM graph_nodes WHERE id = ?",
                (node_id,),
            ).fetchone()[0]
        finally:
            conn.close()

    def _count(self, table: str, where: str, params: tuple[object, ...] = ()) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
        finally:
            conn.close()

    def _counts(self) -> dict[str, dict[str, int]]:
        conn = sqlite3.connect(self.db_path)
        try:
            return {
                "nodes": {
                    row[0]: row[1]
                    for row in conn.execute(
                        "SELECT type, COUNT(*) FROM graph_nodes GROUP BY type ORDER BY type"
                    ).fetchall()
                },
                "edges": {
                    row[0]: row[1]
                    for row in conn.execute(
                        "SELECT type, COUNT(*) FROM graph_edges GROUP BY type ORDER BY type"
                    ).fetchall()
                },
            }
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
