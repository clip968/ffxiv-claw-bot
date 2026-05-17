from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from src.guide_ff14.models import GuideItem


NOISE_SELECTORS = ("script", "style", "nav", "footer", "header", "form")
OPTIONAL_FIELDS = (
    "category",
    "subcategory",
    "item_level",
    "equip_level",
    "jobs",
    "stats",
    "source",
    "description",
)


@dataclass(frozen=True)
class ItemExtractionResult:
    item: GuideItem
    missing_optional_fields: tuple[str, ...]


def extract_item_detail(html: str, *, url: str, raw_path: str) -> ItemExtractionResult:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select(",".join(NOISE_SELECTORS)):
        node.decompose()

    root = soup.select_one("main") or soup.body or soup
    metadata = _metadata_from_definition_list(root)
    name = _extract_name(root, soup)
    description = _section_text(root, "item-description")
    source_text = _section_text(root, "item-source")
    item = GuideItem(
        id=_detail_id_from_url(url),
        name=name,
        name_ko=name,
        url=url,
        category=metadata.get("분류"),
        subcategory=metadata.get("하위 분류"),
        item_level=_parse_int(metadata.get("아이템 레벨")),
        equip_level=_parse_int(metadata.get("장비 레벨")),
        jobs=_split_jobs(metadata.get("착용 가능 직업")),
        stats=_extract_stats(root),
        source={"text": source_text} if source_text else {},
        description=description,
        content_hash=_content_hash(html),
        raw_path=raw_path,
    )
    return ItemExtractionResult(
        item=item,
        missing_optional_fields=_missing_optional_fields(item),
    )


def _detail_id_from_url(url: str) -> str:
    path = urlparse(url).path
    match = re.search(r"/lodestone/db/item/([^/?#]+)", path)
    if not match:
        raise ValueError(f"guide item URL does not contain detail id: {url}")
    return match.group(1)


def _extract_name(root: Tag | BeautifulSoup, soup: BeautifulSoup) -> str:
    name_node = root.select_one(".item__name") or root.find("h1")
    if name_node is not None:
        name = _normalize_text(name_node.get_text(" ", strip=True))
        if name:
            return name
    if soup.title is not None:
        title = _normalize_text(soup.title.get_text(" ", strip=True))
        if title:
            return title.split(" - ", 1)[0].strip()
    raise ValueError("guide item detail HTML does not contain an item name")


def _metadata_from_definition_list(root: Tag | BeautifulSoup) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for dt in root.find_all("dt"):
        key = _normalize_text(dt.get_text(" ", strip=True))
        dd = dt.find_next_sibling("dd")
        if not key or dd is None:
            continue
        metadata[key] = _normalize_text(dd.get_text(" ", strip=True))
    return metadata


def _extract_stats(root: Tag | BeautifulSoup) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for row in root.select("table.item-stats tr"):
        header = row.find(["th", "dt"])
        value = row.find(["td", "dd"])
        if header is None or value is None:
            continue
        key = _normalize_text(header.get_text(" ", strip=True))
        raw_value = _normalize_text(value.get_text(" ", strip=True))
        if not key or not raw_value:
            continue
        stats[key] = _parse_int(raw_value) if _parse_int(raw_value) is not None else raw_value
    return stats


def _section_text(root: Tag | BeautifulSoup, class_name: str) -> str | None:
    section = root.select_one(f".{class_name}")
    if section is None:
        return None
    for heading in section.find_all(re.compile("^h[1-6]$")):
        heading.decompose()
    text = _normalize_text(section.get_text("\n", strip=True))
    return text or None


def _split_jobs(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        part.strip()
        for part in re.split(r"[/,\n]+", value)
        if part.strip()
    ]


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value.replace(",", ""))
    if not match:
        return None
    return int(match.group(0))


def _missing_optional_fields(item: GuideItem) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in OPTIONAL_FIELDS:
        value = getattr(item, field_name)
        if value in (None, "", [], {}):
            missing.append(field_name)
    return tuple(missing)


def _content_hash(html: str) -> str:
    return hashlib.sha256(html.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
    return " ".join(value.split())
