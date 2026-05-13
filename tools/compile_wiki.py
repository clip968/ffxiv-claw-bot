from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
SUMMARY_DIR = ROOT / "wiki" / "source_summaries"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_source(source_id: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, title, source_url, raw_path FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
    return dict(row) if row else None


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def read_raw_html(raw_path: str) -> str:
    return (ROOT / raw_path).read_text(encoding="utf-8")


def write_summary(source_id: str, title: str, body_text: str) -> str:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    content = f"""# {title}

> Source: `{source_id}`

---

{body_text}
"""
    out_path = SUMMARY_DIR / f"{source_id}.md"
    out_path.write_text(content, encoding="utf-8")
    return out_path.relative_to(ROOT).as_posix()


def upsert_wiki_page(source_id: str, title: str, md_path: str) -> str:
    page_id = f"wiki_{source_id.removeprefix('src_')}"
    timestamp = now_iso()
    source_ids = json.dumps([source_id], ensure_ascii=False)

    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id FROM wiki_pages WHERE id = ?", (page_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE wiki_pages
                   SET title = ?, path = ?, updated_at = ?
                 WHERE id = ?
                """,
                (title, md_path, timestamp, page_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO wiki_pages (id, type, title, path, source_ids, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (page_id, "summary", title, md_path, source_ids, "high", timestamp, timestamp),
            )
        conn.commit()

    return page_id


def upsert_wiki_fts(page_id: str, title: str, body_text: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM wiki_fts WHERE page_id = ?", (page_id,))
        conn.execute(
            "INSERT INTO wiki_fts (page_id, title, body) VALUES (?, ?, ?)",
            (page_id, title, body_text),
        )
        conn.commit()


def compile_for_source(source_id: str) -> dict:
    source = get_source(source_id)
    if not source:
        return {"status": "error", "message": f"Source not found: {source_id}"}

    html = read_raw_html(source["raw_path"])
    body_text = extract_text(html)
    md_path = write_summary(source["id"], source["title"], body_text)
    page_id = upsert_wiki_page(source["id"], source["title"], md_path)
    upsert_wiki_fts(page_id, source["title"], body_text)

    return {
        "status": "ok",
        "source_id": source["id"],
        "page_id": page_id,
        "title": source["title"],
        "summary_path": md_path,
        "char_count": len(body_text),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile raw HTML into wiki summary.")
    parser.add_argument("--source-id", required=True, help="Source ID to compile")
    args = parser.parse_args()

    result = compile_for_source(args.source_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
