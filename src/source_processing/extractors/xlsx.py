from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from src.source_processing.errors import SourceParseError
from src.source_processing.models import ExtractedSource

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def extract_xlsx_file(path: str | Path) -> ExtractedSource:
    source_path = Path(path)
    try:
        with zipfile.ZipFile(source_path) as archive:
            shared_strings = _read_shared_strings(archive)
            sheets = _workbook_sheets(archive)
            sections: list[str] = []
            empty_sheets: list[str] = []
            total_row_count = 0

            for sheet_name, sheet_path in sheets:
                rows = _read_sheet_rows(archive, sheet_path, shared_strings)
                if not rows:
                    empty_sheets.append(sheet_name)
                    continue
                total_row_count += len(rows)
                sections.append(
                    f"## Sheet: {sheet_name}\n\n{_markdown_table(rows[0], rows[1:])}"
                )
    except (KeyError, ElementTree.ParseError, zipfile.BadZipFile) as exc:
        raise SourceParseError(f"Could not parse XLSX source: {source_path}", source_path=source_path) from exc

    text = f"# Source: {source_path.name}\n\n" + "\n\n".join(sections)
    if sections:
        text += "\n"

    return ExtractedSource(
        title=source_path.stem,
        text=text,
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": "xlsx",
            "sheet_count": len(sheets),
            "sheet_names": [name for name, _ in sheets],
            "total_row_count": total_row_count,
            "empty_sheets": empty_sheets,
            "empty": not sections,
        },
    )


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall(f"{{{MAIN_NS}}}si"):
        parts = [node.text or "" for node in item.findall(f".//{{{MAIN_NS}}}t")]
        strings.append("".join(parts))
    return strings


def _workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    relationships = _workbook_relationships(archive)
    sheets: list[tuple[str, str]] = []
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        name = sheet.attrib["name"]
        rel_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
        target = relationships[rel_id]
        sheets.append((name, _normalize_workbook_target(target)))
    return sheets


def _workbook_relationships(archive: zipfile.ZipFile) -> dict[str, str]:
    root = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationships: dict[str, str] = {}
    for relationship in root.findall(f"{{{REL_NS}}}Relationship"):
        relationships[relationship.attrib["Id"]] = relationship.attrib["Target"]
    return relationships


def _normalize_workbook_target(target: str) -> str:
    normalized = target.lstrip("/")
    if normalized.startswith("xl/"):
        return normalized
    return f"xl/{normalized}"


def _read_sheet_rows(
    archive: zipfile.ZipFile,
    sheet_path: str,
    shared_strings: list[str],
) -> list[list[str]]:
    root = ElementTree.fromstring(archive.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.findall(f".//{{{MAIN_NS}}}row"):
        values_by_column: dict[int, str] = {}
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            column_index = _column_index(cell.attrib.get("r", ""))
            values_by_column[column_index] = _cell_text(cell, shared_strings)
        if not values_by_column:
            continue
        max_column = max(values_by_column)
        values = [values_by_column.get(index, "") for index in range(1, max_column + 1)]
        if any(value != "" for value in values):
            rows.append(values)
    return rows


def _cell_text(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(f".//{{{MAIN_NS}}}t")).strip()

    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return ""

    if cell_type == "s":
        index = int(value_node.text)
        return shared_strings[index] if index < len(shared_strings) else ""

    return value_node.text.strip()


def _column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference.upper())
    if not match:
        return 1
    index = 0
    for character in match.group(1):
        index = index * 26 + (ord(character) - ord("A") + 1)
    return index


def _markdown_table(header: list[str], rows: list[list[str]]) -> str:
    column_count = len(header)
    lines = [
        "| " + " | ".join(_escape_cell(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in rows:
        normalized = row[:column_count] + [""] * (column_count - len(row))
        lines.append("| " + " | ".join(_escape_cell(cell) for cell in normalized) + " |")
    return "\n".join(lines)


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").strip()
