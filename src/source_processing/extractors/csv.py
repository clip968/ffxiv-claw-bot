from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from src.source_processing.errors import SourceDecodingError, SourceParseError
from src.source_processing.models import ExtractedSource


def extract_csv_file(path: str | Path) -> ExtractedSource:
    source_path = Path(path)
    try:
        raw_text = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SourceDecodingError(
            f"Could not decode source as UTF-8: {source_path}",
            source_path=source_path,
        ) from exc

    rows = list(csv.reader(raw_text.splitlines()))
    if not rows or not rows[0]:
        raise SourceParseError(f"CSV has no header row: {source_path}", source_path=source_path)

    columns = [cell.strip() for cell in rows[0]]
    data_rows = rows[1:]
    table = _markdown_table(columns, data_rows)
    text = f"# Source: {source_path.name}\n\n{table}\n"

    return ExtractedSource(
        title=source_path.stem,
        text=text,
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": "csv",
            "row_count": len(data_rows),
            "column_count": len(columns),
            "columns": columns,
            "empty": raw_text == "",
        },
    )


def _markdown_table(columns: list[str], rows: list[list[str]]) -> str:
    header = "| " + " | ".join(_escape_cell(cell) for cell in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape_cell(cell) for cell in _normalize_row(row, len(columns))) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _normalize_row(row: list[str], column_count: int) -> list[str]:
    normalized = [cell.strip() for cell in row[:column_count]]
    return normalized + [""] * (column_count - len(normalized))


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").strip()
