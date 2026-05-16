from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from src.source_processing.errors import UnsupportedSourceExtensionError
from src.source_processing.extractors import (
    extract_csv_file,
    extract_html_file,
    extract_markdown_file,
    extract_text_file,
    extract_xlsx_file,
)
from src.source_processing.models import ExtractedSource

Extractor = Callable[[str | Path], ExtractedSource]

EXTRACTORS: dict[str, Extractor] = {
    ".txt": extract_text_file,
    ".md": extract_markdown_file,
    ".html": extract_html_file,
    ".htm": extract_html_file,
    ".csv": extract_csv_file,
    ".xlsx": extract_xlsx_file,
}


def get_extractor_for_path(path: str | Path) -> Extractor:
    source_path = Path(path)
    extension = source_path.suffix.lower()
    try:
        return EXTRACTORS[extension]
    except KeyError as exc:
        raise UnsupportedSourceExtensionError(extension or "<none>", source_path) from exc


def extract_source_text(path: str | Path) -> ExtractedSource:
    extractor = get_extractor_for_path(path)
    return extractor(path)
