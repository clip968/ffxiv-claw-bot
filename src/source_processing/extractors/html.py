from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

from src.source_processing.errors import SourceDecodingError
from src.source_processing.models import ExtractedSource

NOISE_TAGS = ("script", "style", "nav", "footer")


def extract_html_file(path: str | Path) -> ExtractedSource:
    source_path = Path(path)
    try:
        html = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise SourceDecodingError(
            f"Could not decode source as UTF-8: {source_path}",
            source_path=source_path,
        ) from exc

    soup = BeautifulSoup(html, "html.parser")
    removed_elements = _remove_noise(soup)
    html_title = _html_title(soup)
    text_root = soup.find("main") or soup.find("article") or soup.body or soup
    text = _normalize_text(text_root.get_text("\n", strip=True))

    return ExtractedSource(
        title=html_title or source_path.stem,
        text=text,
        metadata={
            "source_path": str(source_path),
            "extension": source_path.suffix.lower(),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "extractor_name": "html",
            "html_title": html_title,
            "removed_elements": removed_elements,
            "empty": text == "",
        },
    )


def _remove_noise(soup: BeautifulSoup) -> list[str]:
    removed: list[str] = []
    for tag_name in NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            removed.append(tag_name)
            tag.decompose()
    return removed


def _html_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find(["h1", "h2", "h3"])
    return heading.get_text(" ", strip=True) if heading else ""


def _normalize_text(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
