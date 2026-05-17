from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuideCrawlPage:
    url: str
    kind: str
    status: str
    domain: str = "guide.ff14.co.kr"
    http_status: int | None = None
    content_hash: str | None = None
    raw_path: str | None = None
    last_error: str | None = None
    fetched_at: str | None = None
    parsed_at: str | None = None


@dataclass
class GuideCategory:
    id: str
    db_type: str
    label: str
    url: str
    parent_id: str | None = None
    category2: str | None = None
    category3: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class GuideItem:
    id: str
    name: str
    url: str
    content_hash: str
    raw_path: str
    name_ko: str | None = None
    category: str | None = None
    subcategory: str | None = None
    item_level: int | None = None
    equip_level: int | None = None
    rarity: str | None = None
    is_unique: bool = False
    is_untradable: bool = False
    jobs: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    patch: str | None = None


@dataclass
class GuideItemSource:
    id: str
    item_id: str
    source_type: str
    source_name: str | None = None
    source_url: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
