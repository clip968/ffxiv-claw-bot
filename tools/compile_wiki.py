from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.wiki_indexing import WikiDocument, scan_wiki_documents
from tools.html_utils import extract_text_from_html


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
SUMMARY_DIR = ROOT / "wiki" / "source_summaries"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_source(source_id: str, db_path: Path | None = None) -> dict | None:
    resolved_db_path = db_path or DB_PATH
    conn = sqlite3.connect(resolved_db_path)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, title, source_url, raw_path, source_type FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def extract_text(html: str) -> str:
    return extract_text_from_html(html)


def read_raw_content(raw_path: str, root_path: Path | None = None) -> str:
    resolved_root = root_path or ROOT
    path = Path(raw_path)
    if not path.is_absolute():
        path = resolved_root / path
    return path.read_text(encoding="utf-8")


def write_summary(
    source_id: str,
    title: str,
    body_text: str,
    *,
    root_path: Path | None = None,
    summary_dir: Path | None = None,
) -> str:
    resolved_root = root_path or ROOT
    resolved_summary_dir = summary_dir or SUMMARY_DIR
    resolved_summary_dir.mkdir(parents=True, exist_ok=True)

    content = f"""# {title}

> Source: `{source_id}`

---

{body_text}
"""
    out_path = resolved_summary_dir / f"{source_id}.md"
    out_path.write_text(content, encoding="utf-8")
    try:
        return out_path.relative_to(resolved_root).as_posix()
    except ValueError:
        return out_path.as_posix()


def upsert_wiki_page(
    source_id: str,
    title: str,
    md_path: str,
    db_path: Path | None = None,
) -> str:
    resolved_db_path = db_path or DB_PATH
    page_id = f"wiki_{source_id.removeprefix('src_')}"
    timestamp = now_iso()
    source_ids = json.dumps([source_id], ensure_ascii=False)

    conn = sqlite3.connect(resolved_db_path)
    try:
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
    finally:
        conn.close()

    return page_id


def upsert_wiki_fts(
    page_id: str,
    title: str,
    body_text: str,
    db_path: Path | None = None,
) -> None:
    resolved_db_path = db_path or DB_PATH
    conn = sqlite3.connect(resolved_db_path)
    try:
        conn.execute("DELETE FROM wiki_fts WHERE page_id = ?", (page_id,))
        conn.execute(
            "INSERT INTO wiki_fts (page_id, title, body) VALUES (?, ?, ?)",
            (page_id, title, body_text),
        )
        conn.commit()
    finally:
        conn.close()


def index_wiki_documents(
    *,
    root_path: Path | None = None,
    db_path: Path | None = None,
) -> dict:
    resolved_root = root_path or ROOT
    resolved_db_path = db_path or DB_PATH
    documents = scan_wiki_documents(resolved_root)
    for document in documents:
        _upsert_scanned_wiki_page(document, resolved_root, resolved_db_path)
        upsert_wiki_fts(document.page_id, document.title, document.text, resolved_db_path)
    return {
        "status": "ok",
        "root_path": str(resolved_root),
        "actions": [
            {
                "name": "index_wiki_document",
                "status": "ok",
                "page_id": document.page_id,
                "wiki_type": document.wiki_type,
                "topic": document.topic,
            }
            for document in documents
        ],
        "summary": {
            "indexed": len(documents),
            "source_summary": sum(1 for doc in documents if doc.wiki_type == "source_summary"),
            "job": sum(1 for doc in documents if doc.wiki_type == "job"),
        },
    }


def _upsert_scanned_wiki_page(
    document: WikiDocument,
    root_path: Path,
    db_path: Path,
) -> None:
    timestamp = now_iso()
    rel_path = _relative_path(document.path, root_path)
    conn = sqlite3.connect(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM wiki_pages WHERE id = ?", (document.page_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE wiki_pages
                   SET type = ?, title = ?, path = ?, job = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    document.wiki_type,
                    document.title,
                    rel_path,
                    document.topic if document.wiki_type == "job" else None,
                    timestamp,
                    document.page_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO wiki_pages (
                    id, type, title, path, job, source_ids, confidence,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.page_id,
                    document.wiki_type,
                    document.title,
                    rel_path,
                    document.topic if document.wiki_type == "job" else None,
                    json.dumps([], ensure_ascii=False),
                    "high",
                    timestamp,
                    timestamp,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _relative_path(path: Path, root_path: Path) -> str:
    try:
        return path.relative_to(root_path).as_posix()
    except ValueError:
        return path.as_posix()


def compile_for_source(
    source_id: str,
    *,
    db_path: Path | None = None,
    root_path: Path | None = None,
    summary_dir: Path | None = None,
) -> dict:
    resolved_db_path = db_path or DB_PATH
    resolved_root = root_path or ROOT
    resolved_summary_dir = summary_dir or SUMMARY_DIR
    source = get_source(source_id, resolved_db_path)
    if not source:
        return {"status": "error", "message": f"Source not found: {source_id}"}

    raw_content = read_raw_content(source["raw_path"], resolved_root)
    source_type = source.get("source_type", "")

    if source_type in ("drive_document", "local_file", "local_document"):
        body_text = raw_content
    else:
        body_text = extract_text(raw_content)

    md_path = write_summary(
        source["id"],
        source["title"],
        body_text,
        root_path=resolved_root,
        summary_dir=resolved_summary_dir,
    )
    page_id = upsert_wiki_page(source["id"], source["title"], md_path, resolved_db_path)
    upsert_wiki_fts(page_id, source["title"], body_text, resolved_db_path)

    return {
        "status": "ok",
        "source_id": source["id"],
        "page_id": page_id,
        "title": source["title"],
        "source_type": source_type,
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
