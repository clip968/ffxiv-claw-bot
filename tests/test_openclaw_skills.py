from __future__ import annotations

import json
import unittest
from pathlib import Path


SKILL_ROOT = Path("docs/skills")


def read_skill(name: str) -> str:
    path = SKILL_ROOT / name
    if not path.exists():
        raise AssertionError(f"Expected OpenClaw skill document: {path}")
    return path.read_text(encoding="utf-8")


class OpenClawUseCaseSkillSetTests(unittest.TestCase):
    def test_usecase_router_defines_skill_selection_table(self) -> None:
        text = read_skill("ffxiv-openclaw-router.md")

        required = [
            "ffxiv-source-processing",
            "ffxiv-ask-kb",
            "ffxiv-kb-refresh",
            "ffxiv-notion-status",
            "save / ingest / index",
            "ask / search / answer",
            "refresh / rebuild / regenerate",
            "Notion status",
            "latest info",
            "ask for a source",
        ]
        for fragment in required:
            self.assertIn(fragment, text)

    def test_source_processing_skill_keeps_single_entrypoint_contract(self) -> None:
        text = read_skill("ffxiv-source-processing.md")

        required = [
            "python tools/process_source.py",
            "source_type=url",
            "source_type=text_note",
            "source_type=markdown_file",
            "source_type=plain_text_file",
            "source_type=binary_attachment",
            "Do not use this skill for KB questions",
            "Do not call tools/ingest_local.py directly",
        ]
        for fragment in required:
            self.assertIn(fragment, text)

    def test_ask_skill_forces_grounded_json_path(self) -> None:
        text = read_skill("ffxiv-ask-kb.md")

        required = [
            "python tools/ask.py",
            "--format json",
            "contexts",
            "answer.body",
            "source_ids",
            "Do not answer from memory",
            "Do not call an LLM API",
            "If contexts is empty",
        ]
        for fragment in required:
            self.assertIn(fragment, text)

    def test_refresh_skill_defines_full_refresh_sequence_and_commit_boundary(self) -> None:
        text = read_skill("ffxiv-kb-refresh.md")

        required = [
            "python tools/rebuild_domain_graph.py --dry-run --verbose",
            "python tools/rebuild_domain_graph.py --reset-domain-graph --verbose",
            "python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph",
            "python tools/generate_derived_wiki.py --dry-run --verbose",
            "python tools/generate_derived_wiki.py --verbose",
            "index_wiki_documents",
            "ask smoke",
            "Do not commit generated graph/wiki outputs",
        ]
        for fragment in required:
            self.assertIn(fragment, text)

    def test_notion_status_skill_blocks_payload_leaks_and_direct_source_storage(self) -> None:
        text = read_skill("ffxiv-notion-status.md")

        required = [
            "notion_update",
            "build_notion_status_update",
            "build_notion_update",
            "Status",
            "Graph Status",
            "body",
            "attachments",
            "raw_html",
            "Never upload source content to Notion",
        ]
        for fragment in required:
            self.assertIn(fragment, text)

    def test_machine_readable_routing_manifest_matches_skill_docs(self) -> None:
        manifest_path = SKILL_ROOT / "openclaw-usecase-routing.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], 1)
        skills = {route["skill"] for route in manifest["routes"]}
        self.assertEqual(
            skills,
            {
                "ffxiv-source-processing",
                "ffxiv-ask-kb",
                "ffxiv-kb-refresh",
                "ffxiv-notion-status",
                "unsupported-latest-info",
            },
        )
        for route in manifest["routes"]:
            self.assertIn("use_case", route)
            self.assertIn("triggers", route)
            self.assertIn("entrypoint", route)
            self.assertIn("forbidden", route)


if __name__ == "__main__":
    unittest.main()
