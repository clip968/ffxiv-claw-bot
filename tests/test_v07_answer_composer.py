from __future__ import annotations

import unittest


def _context(path: str = "wiki/jobs/gunbreaker.md", source_ids: tuple[str, ...] = ("patch_7_0",)) -> object:
    from src.retrieval import ContextDocument

    return ContextDocument(
        page_id="job_gunbreaker",
        wiki_type="job",
        title="Gunbreaker Changes",
        path=path,
        score=1.0,
        snippet="Gunbreaker changed",
        content_excerpt="Gunbreaker changed.",
        source_ids=source_ids,
    )


def _context_pack(contexts: tuple[object, ...]) -> object:
    from src.query import parse_query
    from src.retrieval import AskContextPack, build_retrieval_plan

    parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
    return AskContextPack(
        question="7.x 건브레이커 변경 이력 알려줘",
        parsed_query=parsed,
        retrieval_plan=build_retrieval_plan(parsed),
        contexts=contexts,
        confidence="source_grounded" if contexts else "N/A",
    )


class V07CitationAndConfidenceTests(unittest.TestCase):
    def test_collect_sources_includes_paths(self) -> None:
        from src.answering.citations import collect_sources

        self.assertEqual(
            collect_sources((_context(),)),
            ("wiki/jobs/gunbreaker.md", "patch_7_0"),
        )

    def test_collect_sources_includes_source_ids(self) -> None:
        from src.answering.citations import collect_sources

        sources = collect_sources((_context(source_ids=("patch_7_0", "patch_7_1")),))

        self.assertIn("patch_7_0", sources)
        self.assertIn("patch_7_1", sources)

    def test_collect_sources_deduplicates_preserving_order(self) -> None:
        from src.answering.citations import collect_sources

        sources = collect_sources(
            (
                _context("wiki/jobs/gunbreaker.md", ("patch_7_0",)),
                _context("wiki/jobs/gunbreaker.md", ("patch_7_0", "patch_7_1")),
            )
        )

        self.assertEqual(sources, ("wiki/jobs/gunbreaker.md", "patch_7_0", "patch_7_1"))

    def test_confidence_no_context_returns_na(self) -> None:
        from src.answering.confidence import confidence_for_context_count

        self.assertEqual(confidence_for_context_count(0), "N/A")

    def test_confidence_with_context_returns_source_grounded(self) -> None:
        from src.answering.confidence import confidence_for_context_count

        self.assertEqual(confidence_for_context_count(1), "source_grounded")


class V07GroundedAnswerComposerTests(unittest.TestCase):
    def test_answer_includes_source_path(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack((_context(),)))

        self.assertIn("wiki/jobs/gunbreaker.md", answer.body)
        self.assertIn("wiki/jobs/gunbreaker.md", answer.sources)

    def test_answer_includes_source_id(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack((_context(source_ids=("patch_7_0",)),)))

        self.assertIn("patch_7_0", answer.body)
        self.assertIn("patch_7_0", answer.sources)

    def test_answer_no_context_no_hallucination(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack(()))

        self.assertIn("관련 KB 문서를 찾지 못했습니다", answer.body)
        self.assertIn("context에 없는 내용은 추정하지 않았습니다", answer.body)
        self.assertEqual(answer.sources, ())
        self.assertEqual(answer.confidence, "N/A")

    def test_answer_uses_source_grounded_confidence(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack((_context(),)))

        self.assertEqual(answer.confidence, "source_grounded")
        self.assertIn("source_grounded", answer.body)

    def test_answer_text_format_contains_required_sections(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack((_context(),)))

        self.assertIn("핵심 답변", answer.body)
        self.assertIn("근거 문서", answer.body)
        self.assertIn("확실도", answer.body)
        self.assertIn("주의", answer.body)


if __name__ == "__main__":
    unittest.main()
