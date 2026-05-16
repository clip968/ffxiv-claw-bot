from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.source_processing.models import ExtractedSource


def _stub_extracted_source(path: str | Path, extractor_name: str) -> ExtractedSource:
    source_path = Path(path)
    return ExtractedSource(
        title=source_path.stem,
        text="",
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": extractor_name,
        },
    )


def extract_text_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "text")


def extract_markdown_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "markdown")


def extract_html_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "html")


def extract_csv_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "csv")


def extract_xlsx_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "xlsx")
