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


if __name__ == "__main__":
    unittest.main()
