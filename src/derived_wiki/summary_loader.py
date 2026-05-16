from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PATCH_RE = re.compile(r"(?:patch[_\s-]*)?(\d+)[._](\d+)", re.IGNORECASE)
HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class SourceSummary:
    source_id: str
    patch_version: str | None
    title: str
    text: str
    path: Path
    metadata: dict[str, Any] = field(default_factory=dict)


def load_summaries(root: Path | str) -> list[SourceSummary]:
    root_path = Path(root)
    if not root_path.exists():
        return []

    summaries: list[SourceSummary] = []
    for path in sorted(root_path.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata = _extract_metadata(text)
        title = _extract_title(text) or metadata.get("title") or path.stem
        source_id = str(metadata.get("source_id") or path.stem)
        patch_version = (
            _patch_from_filename(path)
            or _patch_from_heading(title)
            or _patch_from_metadata(metadata)
        )
        summaries.append(
            SourceSummary(
                source_id=source_id,
                patch_version=patch_version,
                title=title,
                text=text,
                path=path,
                metadata=metadata,
            )
        )
    return summaries


def _extract_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    lines = text.splitlines()
    for line in _frontmatter_lines(lines):
        _add_metadata_line(metadata, line)

    for line in lines[:20]:
        _add_metadata_line(metadata, line)
    return metadata


def _frontmatter_lines(lines: list[str]) -> list[str]:
    if len(lines) < 3 or lines[0].strip() != "---":
        return []
    collected: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        collected.append(line)
    return collected


def _add_metadata_line(metadata: dict[str, str], line: str) -> None:
    if ":" not in line:
        return
    key, value = line.split(":", 1)
    key = key.strip().lower().replace("-", "_")
    value = value.strip()
    if key and value and re.match(r"^[a-z_][a-z0-9_]*$", key):
        metadata.setdefault(key, value)


def _extract_title(text: str) -> str | None:
    match = HEADING_RE.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _patch_from_filename(path: Path) -> str | None:
    return _patch_from_text(path.stem)


def _patch_from_heading(heading: str | None) -> str | None:
    if not heading:
        return None
    return _patch_from_text(heading)


def _patch_from_metadata(metadata: dict[str, Any]) -> str | None:
    for key in ("patch_version", "patch"):
        value = metadata.get(key)
        if value:
            return _patch_from_text(str(value)) or str(value)
    return None


def _patch_from_text(text: str) -> str | None:
    match = PATCH_RE.search(text)
    if not match:
        return None
    return f"{int(match.group(1))}.{int(match.group(2))}"
