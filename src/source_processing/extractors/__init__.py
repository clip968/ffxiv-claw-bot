from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.source_processing.models import ExtractedSource
from src.source_processing.extractors.csv import extract_csv_file
from src.source_processing.extractors.html import extract_html_file
from src.source_processing.extractors.markdown import extract_markdown_file
from src.source_processing.extractors.text import extract_text_file


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


def extract_xlsx_file(path: str | Path) -> ExtractedSource:
    return _stub_extracted_source(path, "xlsx")
