from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.source_processing.errors import SourceDecodingError
from src.source_processing.models import ExtractedSource


def extract_markdown_file(path: str | Path) -> ExtractedSource:
    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SourceDecodingError(
            f"Could not decode source as UTF-8: {source_path}",
            source_path=source_path,
        ) from exc

    frontmatter = _parse_frontmatter(text)
    return ExtractedSource(
        title=_first_heading(text) or source_path.stem,
        text=text,
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": "markdown",
            "frontmatter": frontmatter,
            "empty": text == "",
        },
    )


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    closing = text.find("\n---", 4)
    if closing == -1:
        return {}

    metadata: dict[str, str] = {}
    for line in text[4:closing].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None
