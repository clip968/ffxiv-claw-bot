from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.search_kb import format_query, search_fts


def read_content_excerpt(md_path: str, max_chars: int = 1000) -> str:
    full_path = ROOT / md_path
    if not full_path.exists():
        return ""

    text = full_path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text

    return text[:max_chars].rsplit("\n", 1)[0] + "\n..."


def build_contexts(query: str, limit: int = 3, max_chars: int = 1000) -> list[dict]:
    results = search_fts(query)
    contexts: list[dict] = []

    for r in results[:limit]:
        content_excerpt = read_content_excerpt(r["path"], max_chars)
        contexts.append({
            "page_id": r["page_id"],
            "title": r["title"],
            "path": r["path"],
            "score": r["score"],
            "snippet": r["snippet"],
            "content_excerpt": content_excerpt,
        })

    return contexts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build context pack for answering.")
    parser.add_argument("question", help="Question to build context for")
    parser.add_argument("--limit", type=int, default=3, help="Max documents to include")
    parser.add_argument("--max-chars", type=int, default=1000, help="Max chars per content excerpt")
    args = parser.parse_args()

    try:
        query = format_query(args.question)
    except ValueError as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        return

    contexts = build_contexts(query, limit=args.limit, max_chars=args.max_chars)

    print(
        json.dumps(
            {"status": "ok", "question": args.question, "contexts": contexts},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
