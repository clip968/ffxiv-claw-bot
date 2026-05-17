from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path


class V08DerivedWikiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp_dir.name)
        self.wiki_root = self.root / "wiki"
        self.graph_dir = self.root / "graph"
        self.conn = sqlite3.connect(":memory:")
        self._seed_graph()

    def tearDown(self) -> None:
        self.conn.close()
        self._tmp_dir.cleanup()

    def _seed_graph(self) -> None:
        from src.domain_graph.storage import ensure_graph_schema, upsert_edge, upsert_node

        ensure_graph_schema(self.conn)
        upsert_node(
            self.conn,
            {
                "id": "src:local_v08",
                "type": "SourceDocument",
                "name": "local_v08",
                "properties": {"title": "Patch 7.5 Fixture", "path": "wiki/source_summaries/local_v08.md"},
            },
        )
        upsert_node(self.conn, {"id": "job:gunbreaker", "type": "Job", "name": "Gunbreaker"})
        upsert_node(self.conn, {"id": "patch:7_5", "type": "Patch", "name": "Patch 7.5"})
        upsert_node(self.conn, {"id": "skill:no_mercy", "type": "Skill", "name": "No Mercy"})
        upsert_node(
            self.conn,
            {
                "id": "fact:no_mercy_7_5",
                "type": "Fact",
                "name": "No Mercy duration was changed.",
                "properties": {"text": "No Mercy duration was changed."},
            },
        )
        for edge in (
            ("job:gunbreaker", "HAS_SKILL", "skill:no_mercy"),
            ("src:local_v08", "SUPPORTS", "fact:no_mercy_7_5"),
            ("fact:no_mercy_7_5", "VALID_IN_PATCH", "patch:7_5"),
            ("fact:no_mercy_7_5", "AFFECTS_JOB", "job:gunbreaker"),
            ("fact:no_mercy_7_5", "AFFECTS_SKILL", "skill:no_mercy"),
        ):
            upsert_edge(
                self.conn,
                {
                    "source_node_id": edge[0],
                    "relation_type": edge[1],
                    "target_node_id": edge[2],
                    "source_id": "local_v08",
                    "confidence": 0.9,
                },
            )

    def _generate(self) -> dict:
        from src.domain_graph.derived_wiki import generate_derived_wiki

        return generate_derived_wiki(self.conn, self.wiki_root, self.graph_dir)

    def test_job_wiki_created(self) -> None:
        result = self._generate()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.wiki_root / "jobs" / "gunbreaker.md").exists())

    def test_job_wiki_has_skills(self) -> None:
        self._generate()

        content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")
        self.assertIn("No Mercy", content)

    def test_job_wiki_has_patches(self) -> None:
        self._generate()

        content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")
        self.assertIn("Patch 7.5", content)

    def test_job_wiki_has_sources(self) -> None:
        self._generate()

        content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")
        self.assertIn("source_id: local_v08", content)

    def test_patch_wiki_created(self) -> None:
        self._generate()

        self.assertTrue((self.wiki_root / "patches" / "7_5.md").exists())

    def test_skill_wiki_created(self) -> None:
        self._generate()

        self.assertTrue((self.wiki_root / "skills" / "no_mercy.md").exists())

    def test_index_md_updated(self) -> None:
        self._generate()

        content = (self.wiki_root / "index.md").read_text(encoding="utf-8")
        self.assertIn("## Derived Wiki", content)
        self.assertIn("[Gunbreaker](jobs/gunbreaker.md)", content)

    def test_idempotent_generation(self) -> None:
        first = self._generate()
        first_content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")
        second = self._generate()
        second_content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")

        self.assertEqual(first["written"], second["written"])
        self.assertEqual(first_content, second_content)


if __name__ == "__main__":
    unittest.main()
