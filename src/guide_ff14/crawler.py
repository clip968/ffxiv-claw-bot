from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.guide_ff14.fetcher import FetchResult, GuideFetcher
from src.guide_ff14.item_extractor import extract_item_detail
from src.guide_ff14.models import GuideCrawlPage
from src.guide_ff14.storage import ensure_guide_ff14_schema, upsert_crawl_page, upsert_item


GUIDE_HOST = "guide.ff14.co.kr"


def discover_item_detail_urls(
    html: str,
    *,
    base_url: str,
    limit: int,
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        normalized = _normalize_detail_url(str(anchor["href"]), base_url)
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        urls.append(normalized)
        if len(urls) >= limit:
            break
    return urls


def crawl_item_pilot(
    *,
    category_url: str,
    limit: int,
    apply: bool,
    fetcher: Any | None = None,
    db_path: Path | str = Path("db/ffxiv.sqlite"),
    raw_dir: Path | str = Path("data/raw/guide_ff14"),
) -> dict[str, Any]:
    active_fetcher = fetcher or GuideFetcher()
    result = _base_result(category_url)
    category_fetch = active_fetcher.fetch(category_url)
    if category_fetch.status != "ok" or not category_fetch.body:
        result["status"] = "error"
        result["errors"].append(_fetch_error(category_url, category_fetch))
        result["next_action"] = "Check category URL, robots/access, and guide.ff14.co.kr availability."
        return result

    result["fetched"] = 1
    planned_urls = discover_item_detail_urls(category_fetch.body, base_url=category_url, limit=limit)
    result["planned_urls"] = planned_urls
    if not apply:
        result["status"] = "planned"
        result["next_action"] = "Run item-pilot with --apply after reviewing planned_urls."
        return result

    resolved_db_path = Path(db_path)
    resolved_raw_dir = Path(raw_dir)
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(resolved_db_path) as conn:
        ensure_guide_ff14_schema(conn)
        category_raw_path = _write_raw_snapshot(
            resolved_raw_dir,
            category_url,
            category_fetch.body,
            category_fetch.content_hash,
            kind="category",
        )
        upsert_crawl_page(
            conn,
            GuideCrawlPage(
                url=category_url,
                kind="category_page",
                status="parsed",
                http_status=category_fetch.http_status,
                content_hash=category_fetch.content_hash,
                raw_path=str(category_raw_path),
            ),
        )
        for detail_url in planned_urls:
            detail_fetch = active_fetcher.fetch(detail_url)
            if detail_fetch.status != "ok" or not detail_fetch.body:
                upsert_crawl_page(
                    conn,
                    GuideCrawlPage(
                        url=detail_url,
                        kind="detail_page",
                        status="error",
                        http_status=detail_fetch.http_status,
                        content_hash=detail_fetch.content_hash,
                        last_error=detail_fetch.error or "empty response body",
                    ),
                )
                result["errors"].append(_fetch_error(detail_url, detail_fetch))
                continue

            result["fetched"] += 1
            raw_path = _write_raw_snapshot(
                resolved_raw_dir,
                detail_url,
                detail_fetch.body,
                detail_fetch.content_hash,
                kind="item",
            )
            extraction = extract_item_detail(
                detail_fetch.body,
                url=detail_url,
                raw_path=str(raw_path),
            )
            upsert_item(conn, extraction.item)
            upsert_crawl_page(
                conn,
                GuideCrawlPage(
                    url=detail_url,
                    kind="detail_page",
                    status="parsed",
                    http_status=detail_fetch.http_status,
                    content_hash=detail_fetch.content_hash,
                    raw_path=str(raw_path),
                ),
            )
            result["parsed"] += 1

    result["status"] = "partial" if result["errors"] else "ok"
    result["next_action"] = (
        "Review errors and rerun item-pilot for failed URLs."
        if result["errors"]
        else "Run tools/generate_item_wiki.py after reviewing stored guide_items."
    )
    return result


def _base_result(category_url: str) -> dict[str, Any]:
    return {
        "status": "pending",
        "category_url": category_url,
        "planned_urls": [],
        "fetched": 0,
        "parsed": 0,
        "skipped": 0,
        "errors": [],
        "next_action": None,
    }


def _normalize_detail_url(raw_url: str, base_url: str) -> str | None:
    normalized = urljoin(base_url, raw_url)
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or parsed.netloc != GUIDE_HOST:
        return None
    if not parsed.path.startswith("/lodestone/db/item/"):
        return None
    return normalized


def _write_raw_snapshot(
    raw_dir: Path,
    url: str,
    body: str,
    content_hash: str | None,
    *,
    kind: str,
) -> Path:
    digest = (content_hash or hashlib.sha256(body.encode("utf-8")).hexdigest())[:12]
    if kind == "item":
        item_id = urlparse(url).path.rstrip("/").split("/")[-1]
        path = raw_dir / "items" / f"{item_id}-{digest}.html"
    else:
        url_digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        path = raw_dir / "categories" / f"{url_digest}-{digest}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _fetch_error(url: str, fetch: FetchResult) -> dict[str, Any]:
    return {
        "url": url,
        "http_status": fetch.http_status,
        "error": fetch.error or "empty response body",
    }
