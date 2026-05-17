from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class EntityRegistryTests(unittest.TestCase):
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
                        "role": "Tank",
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

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_job_alias_to_canonical_node_id(self) -> None:
        from src.domain_graph.entity_registry import load_entity_registry

        registry = load_entity_registry(self.entities_dir)

        self.assertEqual(registry.resolve_alias("Gunbreaker").node_id, "job:gunbreaker")
        self.assertEqual(registry.resolve_alias("GNB").node_id, "job:gunbreaker")
        self.assertEqual(registry.resolve_alias("건브").node_id, "job:gunbreaker")
        self.assertEqual(registry.resolve_alias("건브레이커").node_id, "job:gunbreaker")

    def test_skill_alias_to_canonical_node_id(self) -> None:
        from src.domain_graph.entity_registry import load_entity_registry

        registry = load_entity_registry(self.entities_dir)

        self.assertEqual(registry.resolve_alias("No Mercy").node_id, "skill:no_mercy")

    def test_patch_alias_to_canonical_node_id(self) -> None:
        from src.domain_graph.entity_registry import load_entity_registry

        registry = load_entity_registry(self.entities_dir)

        self.assertEqual(registry.resolve_alias("7.5").node_id, "patch:7_5")
        self.assertEqual(registry.resolve_alias("Patch 7.5").node_id, "patch:7_5")
        self.assertEqual(registry.resolve_alias("패치 7.5").node_id, "patch:7_5")

    def test_duplicate_alias_warning(self) -> None:
        from src.domain_graph.entity_registry import load_entity_registry

        duplicate_jobs = [
            {
                "type": "Job",
                "canonical": "Gunbreaker",
                "slug": "gunbreaker",
                "aliases": ["GNB"],
            },
            {
                "type": "Job",
                "canonical": "Gunblade",
                "slug": "gunblade",
                "aliases": ["GNB"],
            },
        ]
        (self.entities_dir / "jobs.json").write_text(
            json.dumps(duplicate_jobs, ensure_ascii=False),
            encoding="utf-8",
        )

        registry = load_entity_registry(self.entities_dir)

        self.assertEqual(
            registry.duplicate_alias_warnings,
            ("duplicate alias 'GNB' maps to job:gunbreaker and job:gunblade",),
        )


class EntityExtractorTests(unittest.TestCase):
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
                    },
                    {
                        "type": "Job",
                        "canonical": "Warrior",
                        "slug": "warrior",
                        "aliases": ["Warrior", "WAR", "전사"],
                    },
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

        from src.domain_graph.entity_registry import load_entity_registry

        self.registry = load_entity_registry(self.entities_dir)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_extract_korean_alias_and_patch(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities

        entities = extract_entities("건브 7.5 변경점", self.registry)

        self.assertEqual(
            [entity.node_id for entity in entities],
            ["patch:7_5", "job:gunbreaker"],
        )

    def test_extract_english_alias(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities

        entities = extract_entities("GNB No Mercy", self.registry)

        self.assertEqual(
            [entity.node_id for entity in entities],
            ["job:gunbreaker", "skill:no_mercy"],
        )
        self.assertEqual(entities[0].matched_alias, "GNB")
        self.assertEqual(entities[1].matched_alias, "No Mercy")

    def test_dedup_same_entity(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities

        entities = extract_entities("Gunbreaker Gunbreaker GNB", self.registry)

        self.assertEqual([entity.node_id for entity in entities], ["job:gunbreaker"])

    def test_extract_skill_and_patch(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities

        entities = extract_entities("No Mercy duration changed in Patch 7.5", self.registry)

        self.assertEqual(
            [entity.node_id for entity in entities],
            ["patch:7_5", "skill:no_mercy"],
        )

    def test_short_alias_no_false_positive(self) -> None:
        from src.domain_graph.entity_extractor import extract_entities

        entities = extract_entities("The award text mentions no job.", self.registry)

        self.assertNotIn("job:warrior", [entity.node_id for entity in entities])


if __name__ == "__main__":
    unittest.main()
