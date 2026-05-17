from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path


class V085RealDerivedWikiTests(unittest.TestCase):
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
        nodes = [
            {
                "id": "src:local_v08_5_derived",
                "type": "SourceDocument",
                "name": "local_v08_5_derived",
                "properties": {
                    "title": "Fixture Patch Note",
                    "path": "wiki/source_summaries/local_v08_5_derived.md",
                },
            },
            {"id": "job:gunbreaker", "type": "Job", "name": "Gunbreaker"},
            {"id": "patch:7_5", "type": "Patch", "name": "Patch 7.5"},
            {"id": "skill:no_mercy", "type": "Skill", "name": "No Mercy"},
            {
                "id": "fact:no_mercy_7_5",
                "type": "Fact",
                "name": "No Mercy duration was changed.",
                "properties": {"text": "No Mercy duration was changed."},
            },
        ]
        for node in nodes:
            upsert_node(self.conn, node)
        for source, relation, target in (
            ("job:gunbreaker", "HAS_SKILL", "skill:no_mercy"),
            ("src:local_v08_5_derived", "SUPPORTS", "fact:no_mercy_7_5"),
            ("fact:no_mercy_7_5", "VALID_IN_PATCH", "patch:7_5"),
            ("fact:no_mercy_7_5", "AFFECTS_JOB", "job:gunbreaker"),
            ("fact:no_mercy_7_5", "AFFECTS_SKILL", "skill:no_mercy"),
        ):
            upsert_edge(
                self.conn,
                {
                    "source_node_id": source,
                    "relation_type": relation,
                    "target_node_id": target,
                    "source_id": "local_v08_5_derived",
                    "confidence": 0.9,
                },
            )

    def _generate(self) -> dict[str, object]:
        from src.domain_graph.derived_wiki import generate_derived_wiki

        return generate_derived_wiki(
            self.conn,
            self.wiki_root,
            self.graph_dir,
            verbose=True,
        )

    def test_generates_job_wiki(self) -> None:
        result = self._generate()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.wiki_root / "jobs" / "gunbreaker.md").exists())

    def test_generates_patch_wiki(self) -> None:
        self._generate()

        self.assertTrue((self.wiki_root / "patches" / "7_5.md").exists())

    def test_generates_skill_wiki(self) -> None:
        self._generate()

        self.assertTrue((self.wiki_root / "skills" / "no_mercy.md").exists())

    def test_generated_page_includes_source(self) -> None:
        self._generate()

        content = (self.wiki_root / "jobs" / "gunbreaker.md").read_text(encoding="utf-8")
        self.assertIn("source_id: local_v08_5_derived", content)
        self.assertIn("path: wiki/source_summaries/local_v08_5_derived.md", content)

    def test_index_links_generated_pages(self) -> None:
        self._generate()

        content = (self.wiki_root / "index.md").read_text(encoding="utf-8")
        self.assertIn("[Gunbreaker](jobs/gunbreaker.md)", content)
        self.assertIn("[Patch 7.5](patches/7_5.md)", content)
        self.assertIn("[No Mercy](skills/no_mercy.md)", content)

    def test_idempotent_generation(self) -> None:
        self._generate()
        first = {
            path.relative_to(self.wiki_root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(self.wiki_root.rglob("*.md"))
        }

        self._generate()
        second = {
            path.relative_to(self.wiki_root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(self.wiki_root.rglob("*.md"))
        }

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
