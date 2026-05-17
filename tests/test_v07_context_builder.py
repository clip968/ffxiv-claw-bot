from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


def _context_inputs() -> tuple[object, object, object]:
    from src.query import parse_query
    from src.retrieval import SearchResult, build_retrieval_plan

    parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
    plan = build_retrieval_plan(parsed)
    result = SearchResult(
        page_id="job_gunbreaker",
        title="Gunbreaker Changes",
        wiki_type="job",
        path="wiki/jobs/gunbreaker.md",
        score=1.0,
        snippet="Gunbreaker changed",
        topic="gunbreaker",
    )
    return parsed, plan, result


class V07ContextPackBuilderTests(unittest.TestCase):
    def test_context_pack_includes_job_wiki_path(self) -> None:
        from src.retrieval.context_builder import build_context_pack

        parsed, plan, result = _context_inputs()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            path = root / result.path
            path.parent.mkdir(parents=True)
            path.write_text("# Gunbreaker\n\nsource_id: patch_7_0\n", encoding="utf-8")

            pack = build_context_pack(
                "7.x 건브레이커 변경 이력 알려줘",
                parsed,
                plan,
                (result,),
                root_path=root,
            )

        self.assertEqual(pack.contexts[0].path, "wiki/jobs/gunbreaker.md")
        self.assertEqual(pack.confidence, "source_grounded")

    def test_context_pack_includes_source_ids_from_content(self) -> None:
        from src.retrieval.context_builder import build_context_pack

        parsed, plan, result = _context_inputs()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            path = root / result.path
            path.parent.mkdir(parents=True)
            path.write_text(
                "# Gunbreaker\n\nsource_id: patch_7_0\n> Source: `patch_7_1`\n",
                encoding="utf-8",
            )

            pack = build_context_pack(
                "7.x 건브레이커 변경 이력 알려줘",
                parsed,
                plan,
                (result,),
                root_path=root,
            )

        self.assertEqual(pack.contexts[0].source_ids, ("patch_7_0", "patch_7_1"))

    def test_context_pack_limits_excerpt_length(self) -> None:
        from src.retrieval.context_builder import build_context_pack

        parsed, plan, result = _context_inputs()
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            path = root / result.path
            path.parent.mkdir(parents=True)
            path.write_text("A" * 100, encoding="utf-8")

            pack = build_context_pack(
                "7.x 건브레이커 변경 이력 알려줘",
                parsed,
                plan,
                (result,),
                root_path=root,
                max_chars=12,
            )

        self.assertEqual(len(pack.contexts[0].content_excerpt), 12)

    def test_context_pack_empty_when_no_results(self) -> None:
        from src.retrieval.context_builder import build_context_pack

        parsed, plan, _result = _context_inputs()

        pack = build_context_pack(
            "7.x 건브레이커 변경 이력 알려줘",
            parsed,
            plan,
            (),
        )

        self.assertEqual(pack.contexts, ())
        self.assertEqual(pack.confidence, "N/A")

    def test_context_pack_missing_file_uses_empty_excerpt(self) -> None:
        from src.retrieval.context_builder import build_context_pack

        parsed, plan, result = _context_inputs()
        with tempfile.TemporaryDirectory() as tmp_dir:
            pack = build_context_pack(
                "7.x 건브레이커 변경 이력 알려줘",
                parsed,
                plan,
                (result,),
                root_path=Path(tmp_dir),
            )

        self.assertEqual(pack.contexts[0].content_excerpt, "")
        self.assertEqual(pack.contexts[0].source_ids, ())


if __name__ == "__main__":
    unittest.main()
