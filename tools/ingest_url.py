from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
RAW_URLS_DIR = ROOT / "raw" / "urls"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/")

    base = f"{host}_{path}" if path else host
    base = re.sub(r"[^a-zA-Z0-9가-힣._-]+", "_", base)
    base = base.strip("_")

    if not base:
        base = "url"

    return base[:120]


def fetch_url(url: str) -> tuple[str, str]:
    headers = {
        "User-Agent": "ffxiv-claw-bot/0.1"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "text" not in content_type and "html" not in content_type and "json" not in content_type:
        raise ValueError(f"unsupported content-type: {content_type}")

    return response.text, content_type


def extract_title(html: str, fallback_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        if title:
            return title

    parsed = urlparse(fallback_url)
    return parsed.netloc or fallback_url


def insert_source(
    *,
    source_id: str,
    title: str,
    source_url: str,
    raw_path: str,
    content_hash: str,
) -> None:
    timestamp = now_iso()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO sources (
                id,
                source_type,
                title,
                source_url,
                raw_path,
                content_hash,
                language,
                patch,
                job,
                raid,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                "url",
                title,
                source_url,
                raw_path,
                content_hash,
                None,
                None,
                None,
                None,
                timestamp,
                timestamp,
            ),
        )
        conn.commit()


def find_existing_by_hash(content_hash: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, title, source_url, raw_path, content_hash
            FROM sources
            WHERE content_hash = ?
            LIMIT 1
            """,
            (content_hash,),
        ).fetchone()

    return dict(row) if row else None


def ingest_url(url: str) -> dict:
    RAW_URLS_DIR.mkdir(parents=True, exist_ok=True)

    html, content_type = fetch_url(url)
    content_hash = sha256_text(html)

    existing = find_existing_by_hash(content_hash)
    if existing:
        return {
            "status": "ok",
            "deduplicated": True,
            "existing_source": existing,
        }

    title = extract_title(html, url)
    source_id = f"src_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    filename_base = safe_filename_from_url(url)
    raw_file = RAW_URLS_DIR / f"{filename_base}_{source_id}.html"
    raw_file.write_text(html, encoding="utf-8")

    relative_raw_path = raw_file.relative_to(ROOT).as_posix()

    insert_source(
        source_id=source_id,
        title=title,
        source_url=url,
        raw_path=relative_raw_path,
        content_hash=content_hash,
    )

    return {
        "status": "ok",
        "deduplicated": False,
        "source_id": source_id,
        "title": title,
        "source_url": url,
        "content_type": content_type,
        "raw_path": relative_raw_path,
        "content_hash": content_hash,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest URL into FFXIV knowledge base.")
    parser.add_argument("url", help="URL to ingest")
    args = parser.parse_args()

    result = ingest_url(args.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
