from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class RelationExtractorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.entities_dir = Path(self._tmp_dir.name) / "ffxiv_entities"
        self.entities_dir.mkdir()
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

        from src.domain_graph.entity_extractor import extract_entities
        from src.domain_graph.entity_registry import load_entity_registry

        self.registry = load_entity_registry(self.entities_dir)
        self.text = "Patch 7.5 includes adjustments to Gunbreaker. No Mercy duration was changed."
        self.entities = extract_entities(self.text, self.registry)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _result(self, text: str | None = None):
        from src.domain_graph.entity_extractor import extract_entities
        from src.domain_graph.relation_extractor import extract_relations

        body = text or self.text
        entities = extract_entities(body, self.registry)
        return extract_relations(
            body,
            entities,
            self.registry,
            source_id="local_v08_fixture",
            wiki_page_id="wiki_local_v08_fixture",
        )

    def test_mentions_edge_for_job(self) -> None:
        result = self._result()

        self.assertTrue(
            any(
                edge.source_node_id == "src:local_v08_fixture"
                and edge.target_node_id == "job:gunbreaker"
                and edge.relation_type == "MENTIONS"
                for edge in result.edges
            )
        )

    def test_mentions_edge_for_skill(self) -> None:
        result = self._result()

        self.assertTrue(
            any(
                edge.source_node_id == "src:local_v08_fixture"
                and edge.target_node_id == "skill:no_mercy"
                and edge.relation_type == "MENTIONS"
                for edge in result.edges
            )
        )

    def test_mentions_edge_for_patch(self) -> None:
        result = self._result()

        self.assertTrue(
            any(
                edge.source_node_id == "src:local_v08_fixture"
                and edge.target_node_id == "patch:7_5"
                and edge.relation_type == "MENTIONS"
                for edge in result.edges
            )
        )

    def test_has_skill_from_registry(self) -> None:
        result = self._result()

        self.assertTrue(
            any(
                edge.source_node_id == "job:gunbreaker"
                and edge.target_node_id == "skill:no_mercy"
                and edge.relation_type == "HAS_SKILL"
                for edge in result.edges
            )
        )

    def test_fact_created_with_trigger(self) -> None:
        result = self._result()

        self.assertEqual(len(result.facts), 1)
        self.assertEqual(result.facts[0].node_id[:5], "fact:")
        self.assertEqual(result.facts[0].subject_node_id, "skill:no_mercy")
        self.assertEqual(result.facts[0].object_node_id, "patch:7_5")

    def test_no_fact_without_trigger(self) -> None:
        result = self._result("Patch 7.5 mentions Gunbreaker and No Mercy.")

        self.assertEqual(result.facts, ())

    def test_fact_edges_complete(self) -> None:
        result = self._result()
        fact_id = result.facts[0].node_id
        relation_pairs = {
            (edge.source_node_id, edge.relation_type, edge.target_node_id)
            for edge in result.edges
        }

        self.assertIn(("src:local_v08_fixture", "SUPPORTS", fact_id), relation_pairs)
        self.assertIn((fact_id, "VALID_IN_PATCH", "patch:7_5"), relation_pairs)
        self.assertIn((fact_id, "AFFECTS_JOB", "job:gunbreaker"), relation_pairs)
        self.assertIn((fact_id, "AFFECTS_SKILL", "skill:no_mercy"), relation_pairs)


if __name__ == "__main__":
    unittest.main()
