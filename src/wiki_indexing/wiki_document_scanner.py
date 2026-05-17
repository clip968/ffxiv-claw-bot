from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WikiDocument:
    page_id: str
    path: Path
    wiki_type: str
    topic: str | None
    title: str
    text: str


def scan_wiki_documents(root_path: Path | str) -> list[WikiDocument]:
    root = Path(root_path)
    documents: list[WikiDocument] = []
    documents.extend(_scan_source_summaries(root))
    documents.extend(_scan_job_wikis(root))
    documents.extend(_scan_patch_wikis(root))
    documents.extend(_scan_skill_wikis(root))
    return sorted(documents, key=lambda doc: doc.path.as_posix())


def _scan_source_summaries(root: Path) -> list[WikiDocument]:
    return [
        _build_document(
            path,
            wiki_type="source_summary",
            topic=path.stem,
            page_id=f"wiki_{path.stem}",
        )
        for path in sorted((root / "wiki" / "source_summaries").glob("*.md"))
    ]


def _scan_job_wikis(root: Path) -> list[WikiDocument]:
    return _scan_topic_wikis(root, directory="jobs", wiki_type="job", page_prefix="job")


def _scan_patch_wikis(root: Path) -> list[WikiDocument]:
    return _scan_topic_wikis(root, directory="patches", wiki_type="patch", page_prefix="patch")


def _scan_skill_wikis(root: Path) -> list[WikiDocument]:
    return _scan_topic_wikis(root, directory="skills", wiki_type="skill", page_prefix="skill")


def _scan_topic_wikis(
    root: Path,
    *,
    directory: str,
    wiki_type: str,
    page_prefix: str,
) -> list[WikiDocument]:
    return [
        _build_document(
            path,
            wiki_type=wiki_type,
            topic=path.stem,
            page_id=f"{page_prefix}_{path.stem}",
        )
        for path in sorted((root / "wiki" / directory).glob("*.md"))
    ]


def _build_document(
    path: Path,
    *,
    wiki_type: str,
    topic: str | None,
    page_id: str,
) -> WikiDocument:
    text = path.read_text(encoding="utf-8")
    return WikiDocument(
        page_id=page_id,
        path=path,
        wiki_type=wiki_type,
        topic=topic,
        title=_extract_title(text) or path.stem,
        text=text,
    )


def _extract_title(text: str) -> str | None:
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()
