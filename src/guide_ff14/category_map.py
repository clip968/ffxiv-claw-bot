from __future__ import annotations

import hashlib
import html as html_lib
import re
from urllib.parse import parse_qs, urljoin, urlparse

from src.guide_ff14.models import GuideCategory


GUIDE_BASE_URL = "https://guide.ff14.co.kr"
ALLOWED_HOST = "guide.ff14.co.kr"
SUPPORTED_DB_TYPES = {
    "item",
    "quest",
    "duty",
    "achievement",
    "recipe",
    "gathering",
    "shop",
    "text_command",
}

ANCHOR_PATTERN = re.compile(r"<a\b(?P<attrs>[^>]*)>(?P<label>.*?)</a>", re.IGNORECASE | re.DOTALL)
FN_OPEN_PATTERN = re.compile(r"fnOpenLeftMenu\s*\((?P<args>.*?)\)", re.IGNORECASE | re.DOTALL)
QUOTED_ARG_PATTERN = re.compile(r"(['\"])(?P<value>.*?)\1", re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_category_map(html: str, *, base_url: str = GUIDE_BASE_URL) -> list[GuideCategory]:
    categories: list[GuideCategory] = []
    seen_urls: set[str] = set()

    for label, raw_url in _extract_labeled_urls(html):
        category = _build_category(label, raw_url, base_url)
        if category is None or category.url in seen_urls:
            continue
        seen_urls.add(category.url)
        categories.append(category)

    return categories


def _extract_labeled_urls(html: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for match in ANCHOR_PATTERN.finditer(html):
        attrs = match.group("attrs")
        fn_match = FN_OPEN_PATTERN.search(attrs)
        if not fn_match:
            continue
        raw_url = _url_from_fn_args(fn_match.group("args"))
        if raw_url is None:
            continue
        label = _clean_label(match.group("label"))
        results.append((label, raw_url))
    return results


def _url_from_fn_args(args: str) -> str | None:
    quoted_values = [
        html_lib.unescape(match.group("value")).strip()
        for match in QUOTED_ARG_PATTERN.finditer(args)
    ]
    for value in reversed(quoted_values):
        lower = value.casefold()
        if lower.startswith("javascript:"):
            return None
        if "/lodestone/db/" in value:
            return value
    return None


def _build_category(label: str, raw_url: str, base_url: str) -> GuideCategory | None:
    normalized_url = _normalize_url(raw_url, base_url)
    if normalized_url is None:
        return None

    parsed = urlparse(normalized_url)
    db_type_match = re.search(r"/lodestone/db/([^/?#]+)", parsed.path)
    if not db_type_match:
        return None
    db_type = db_type_match.group(1)
    if db_type not in SUPPORTED_DB_TYPES:
        return None

    query = {
        key: values[-1]
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
        if values
    }
    category2 = query.pop("category2", None)
    category3 = query.pop("category3", None)
    category_id = _category_id(db_type, category2, category3, normalized_url)
    return GuideCategory(
        id=category_id,
        db_type=db_type,
        label=label,
        url=normalized_url,
        category2=category2,
        category3=category3,
        filters=query,
    )


def _normalize_url(raw_url: str, base_url: str) -> str | None:
    unescaped = html_lib.unescape(raw_url).strip()
    if not unescaped or unescaped.casefold().startswith("javascript:"):
        return None
    normalized = urljoin(base_url, unescaped)
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST:
        return None
    if not parsed.path.startswith("/lodestone/db/"):
        return None
    return normalized


def _category_id(
    db_type: str,
    category2: str | None,
    category3: str | None,
    url: str,
) -> str:
    if category2 or category3:
        return f"guide:{db_type}:{category2 or '_'}:{category3 or '_'}"
    parsed = urlparse(url)
    if parsed.query:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        return f"guide:{db_type}:{digest}"
    return f"guide:{db_type}:root"


def _clean_label(raw_label: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_label)
    return " ".join(html_lib.unescape(without_tags).split())
