from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from src.guide_ff14.models import (
    GuideCategory,
    GuideCrawlPage,
    GuideItem,
    GuideItemSource,
)


def ensure_guide_ff14_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS guide_crawl_pages (
          url TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          domain TEXT NOT NULL DEFAULT 'guide.ff14.co.kr',
          status TEXT NOT NULL,
          http_status INTEGER,
          content_hash TEXT,
          raw_path TEXT,
          last_error TEXT,
          fetched_at TEXT,
          parsed_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS guide_categories (
          id TEXT PRIMARY KEY,
          db_type TEXT NOT NULL,
          label TEXT NOT NULL,
          url TEXT NOT NULL UNIQUE,
          parent_id TEXT,
          category2 TEXT,
          category3 TEXT,
          filters_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS guide_items (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          name_ko TEXT,
          url TEXT NOT NULL UNIQUE,
          category TEXT,
          subcategory TEXT,
          item_level INTEGER,
          equip_level INTEGER,
          rarity TEXT,
          is_unique INTEGER NOT NULL DEFAULT 0,
          is_untradable INTEGER NOT NULL DEFAULT 0,
          jobs_json TEXT NOT NULL DEFAULT '[]',
          stats_json TEXT NOT NULL DEFAULT '{}',
          source_json TEXT NOT NULL DEFAULT '{}',
          description TEXT,
          patch TEXT,
          content_hash TEXT NOT NULL,
          raw_path TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS guide_item_sources (
          id TEXT PRIMARY KEY,
          item_id TEXT NOT NULL,
          source_type TEXT NOT NULL,
          source_name TEXT,
          source_url TEXT,
          properties_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_guide_crawl_pages_kind
          ON guide_crawl_pages(kind);
        CREATE INDEX IF NOT EXISTS idx_guide_categories_db_type
          ON guide_categories(db_type);
        CREATE INDEX IF NOT EXISTS idx_guide_items_category
          ON guide_items(category, subcategory);
        CREATE INDEX IF NOT EXISTS idx_guide_item_sources_item_id
          ON guide_item_sources(item_id);
        """
    )
    conn.commit()


def upsert_crawl_page(
    conn: sqlite3.Connection,
    page: GuideCrawlPage,
    *,
    now: str | None = None,
) -> None:
    ensure_guide_ff14_schema(conn)
    timestamp = now or _now_iso()
    conn.execute(
        """
        INSERT INTO guide_crawl_pages (
            url, kind, domain, status, http_status, content_hash, raw_path,
            last_error, fetched_at, parsed_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
          kind = excluded.kind,
          domain = excluded.domain,
          status = excluded.status,
          http_status = excluded.http_status,
          content_hash = excluded.content_hash,
          raw_path = excluded.raw_path,
          last_error = excluded.last_error,
          fetched_at = excluded.fetched_at,
          parsed_at = excluded.parsed_at,
          updated_at = excluded.updated_at
        """,
        (
            page.url,
            page.kind,
            page.domain,
            page.status,
            page.http_status,
            page.content_hash,
            page.raw_path,
            page.last_error,
            page.fetched_at,
            page.parsed_at,
            timestamp,
            timestamp,
        ),
    )
    conn.commit()


def upsert_category(
    conn: sqlite3.Connection,
    category: GuideCategory,
    *,
    now: str | None = None,
) -> str:
    ensure_guide_ff14_schema(conn)
    timestamp = now or _now_iso()
    existing_id = _existing_id_by_id_or_url(
        conn,
        table="guide_categories",
        id_value=category.id,
        url=category.url,
    )
    row = (
        category.id,
        category.db_type,
        category.label,
        category.url,
        category.parent_id,
        category.category2,
        category.category3,
        _json_dumps(category.filters),
        timestamp,
        timestamp,
    )
    if existing_id is None:
        conn.execute(
            """
            INSERT INTO guide_categories (
                id, db_type, label, url, parent_id, category2, category3,
                filters_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
        stored_id = category.id
    else:
        conn.execute(
            """
            UPDATE guide_categories
               SET db_type = ?, label = ?, url = ?, parent_id = ?,
                   category2 = ?, category3 = ?, filters_json = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                category.db_type,
                category.label,
                category.url,
                category.parent_id,
                category.category2,
                category.category3,
                _json_dumps(category.filters),
                timestamp,
                existing_id,
            ),
        )
        stored_id = existing_id
    conn.commit()
    return stored_id


def upsert_item(
    conn: sqlite3.Connection,
    item: GuideItem,
    *,
    now: str | None = None,
) -> str:
    ensure_guide_ff14_schema(conn)
    timestamp = now or _now_iso()
    existing_id = _existing_id_by_id_or_url(
        conn,
        table="guide_items",
        id_value=item.id,
        url=item.url,
    )
    if existing_id is None:
        conn.execute(
            """
            INSERT INTO guide_items (
                id, name, name_ko, url, category, subcategory, item_level,
                equip_level, rarity, is_unique, is_untradable, jobs_json,
                stats_json, source_json, description, patch, content_hash,
                raw_path, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            _item_values(item, timestamp, timestamp),
        )
        stored_id = item.id
    else:
        conn.execute(
            """
            UPDATE guide_items
               SET name = ?, name_ko = ?, url = ?, category = ?,
                   subcategory = ?, item_level = ?, equip_level = ?,
                   rarity = ?, is_unique = ?, is_untradable = ?,
                   jobs_json = ?, stats_json = ?, source_json = ?,
                   description = ?, patch = ?, content_hash = ?,
                   raw_path = ?, updated_at = ?
             WHERE id = ?
            """,
            (
                item.name,
                item.name_ko,
                item.url,
                item.category,
                item.subcategory,
                item.item_level,
                item.equip_level,
                item.rarity,
                int(item.is_unique),
                int(item.is_untradable),
                _json_dumps(item.jobs),
                _json_dumps(item.stats),
                _json_dumps(item.source),
                item.description,
                item.patch,
                item.content_hash,
                item.raw_path,
                timestamp,
                existing_id,
            ),
        )
        stored_id = existing_id
    conn.commit()
    return stored_id


def upsert_item_source(
    conn: sqlite3.Connection,
    source: GuideItemSource,
    *,
    now: str | None = None,
) -> None:
    ensure_guide_ff14_schema(conn)
    timestamp = now or _now_iso()
    conn.execute(
        """
        INSERT INTO guide_item_sources (
            id, item_id, source_type, source_name, source_url, properties_json,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          item_id = excluded.item_id,
          source_type = excluded.source_type,
          source_name = excluded.source_name,
          source_url = excluded.source_url,
          properties_json = excluded.properties_json,
          updated_at = excluded.updated_at
        """,
        (
            source.id,
            source.item_id,
            source.source_type,
            source.source_name,
            source.source_url,
            _json_dumps(source.properties),
            timestamp,
            timestamp,
        ),
    )
    conn.commit()


def _item_values(
    item: GuideItem,
    created_at: str,
    updated_at: str,
) -> tuple[Any, ...]:
    return (
        item.id,
        item.name,
        item.name_ko,
        item.url,
        item.category,
        item.subcategory,
        item.item_level,
        item.equip_level,
        item.rarity,
        int(item.is_unique),
        int(item.is_untradable),
        _json_dumps(item.jobs),
        _json_dumps(item.stats),
        _json_dumps(item.source),
        item.description,
        item.patch,
        item.content_hash,
        item.raw_path,
        created_at,
        updated_at,
    )


def _existing_id_by_id_or_url(
    conn: sqlite3.Connection,
    *,
    table: str,
    id_value: str,
    url: str,
) -> str | None:
    row = conn.execute(
        f"SELECT id FROM {table} WHERE id = ? OR url = ? ORDER BY id = ? DESC LIMIT 1",
        (id_value, url, id_value),
    ).fetchone()
    if row is None:
        return None
    return str(row["id"] if isinstance(row, sqlite3.Row) else row[0])


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
