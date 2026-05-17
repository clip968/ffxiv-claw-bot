from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from tests.test_compile_wiki import ensure_wiki_tables


def _context(
    *,
    page_id: str,
    wiki_type: str,
    title: str,
    path: str,
    content: str,
    source_ids: tuple[str, ...] = (),
) -> object:
    from src.retrieval import ContextDocument

    return ContextDocument(
        page_id=page_id,
        wiki_type=wiki_type,
        title=title,
        path=path,
        score=1.0,
        snippet=content[:160],
        content_excerpt=content,
        source_ids=source_ids,
    )


def _context_pack(contexts: tuple[object, ...], question: str = "건브 7.5 변경점 알려줘") -> object:
    from src.query import parse_query
    from src.retrieval import AskContextPack, build_retrieval_plan

    parsed = parse_query(question)
    return AskContextPack(
        question=question,
        parsed_query=parsed,
        retrieval_plan=build_retrieval_plan(parsed),
        contexts=contexts,
        confidence="source_grounded" if contexts else "N/A",
    )


def _rich_contexts() -> tuple[object, ...]:
    return (
        _context(
            page_id="job_gunbreaker",
            wiki_type="job",
            title="Gunbreaker",
            path="wiki/jobs/gunbreaker.md",
            content=(
                "# Gunbreaker\n\n"
                "## Summary\nCurrent KB-level summary for Gunbreaker.\n\n"
                "## Recent Facts\n"
                "- Patch 7.5 includes adjustments to Gunbreaker.\n"
                "- No Mercy duration was changed.\n\n"
                "Playable Content\nHousing\nThe Manderville Gold Saucer\n"
            ),
            source_ids=("local_patch_75",),
        ),
        _context(
            page_id="patch_7_5",
            wiki_type="patch",
            title="Patch 7.5",
            path="wiki/patches/7_5.md",
            content="# Patch 7.5\n\n## Affected Jobs\n- Gunbreaker\n",
            source_ids=("local_patch_75",),
        ),
        _context(
            page_id="skill_no_mercy",
            wiki_type="skill",
            title="No Mercy",
            path="wiki/skills/no_mercy.md",
            content="# No Mercy\n\n## Job\n- Gunbreaker\n",
        ),
    )


class V085AnswerQualityTests(unittest.TestCase):
    def test_answer_not_raw_source_dump(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack(_rich_contexts()))

        self.assertIn("No Mercy duration was changed.", answer.body)
        self.assertNotIn("# Gunbreaker", answer.body)
        self.assertNotIn("The Manderville Gold Saucer", answer.body)

    def test_answer_has_summary_section(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack(_rich_contexts()))

        self.assertIn("요약", answer.body)
        self.assertIn("건브 7.5", answer.body)

    def test_answer_has_related_entities(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack(_rich_contexts()))

        self.assertIn("관련 항목", answer.body)
        self.assertIn("- Job: Gunbreaker", answer.body)
        self.assertIn("- Patch: Patch 7.5", answer.body)
        self.assertIn("- Skill: No Mercy", answer.body)

    def test_answer_has_confirmed_content_and_sources_sections(self) -> None:
        from src.answering.composer import compose_answer

        answer = compose_answer(_context_pack(_rich_contexts()))

        self.assertIn("확인된 내용", answer.body)
        self.assertIn("근거", answer.body)
        self.assertIn("wiki/jobs/gunbreaker.md", answer.body)
        self.assertIn("local_patch_75", answer.sources)

    def test_answer_has_uncertainty_when_sparse(self) -> None:
        from src.answering.composer import compose_answer

        sparse_context = _context(
            page_id="skill_no_mercy",
            wiki_type="skill",
            title="No Mercy",
            path="wiki/skills/no_mercy.md",
            content="# No Mercy\n\n## Related Sources\n- None\n",
        )
        answer = compose_answer(_context_pack((sparse_context,), question="No Mercy 관련 변경 있어?"))

        self.assertIn("주의", answer.body)
        self.assertIn("근거가 제한적", answer.body)

    def test_format_text_outputs_body_only(self) -> None:
        from tools.ask import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "ffxiv.sqlite"
            ensure_wiki_tables(db_path)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "알 수 없는 질문",
                        "--format",
                        "text",
                        "--db-path",
                        str(db_path),
                        "--root-path",
                        str(root),
                        "--graph-dir",
                        str(root / "graph"),
                    ]
                )

        output = stdout.getvalue()
        self.assertIn("관련 KB 문서를 찾지 못했습니다", output)
        self.assertNotIn('"status"', output)
        self.assertNotIn("{", output)


if __name__ == "__main__":
    unittest.main()
