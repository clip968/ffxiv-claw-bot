from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.source_processing.errors import SourceDecodingError
from src.source_processing.models import ExtractedSource


def extract_text_file(path: str | Path) -> ExtractedSource:
    source_path = Path(path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SourceDecodingError(
            f"Could not decode source as UTF-8: {source_path}",
            source_path=source_path,
        ) from exc

    return ExtractedSource(
        title=source_path.stem,
        text=text,
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": "text",
            "empty": text == "",
        },
    )
