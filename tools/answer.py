from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.search_kb import format_query, search_fts


POLICY_PATH = ROOT / "prompts" / "answer_policy.md"


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


def format_answer_text(question: str, contexts: list[dict]) -> str:
    lines: list[str] = []

    lines.append("=" * 48)
    lines.append("핵심 요약:")
    if not contexts:
        lines.append(f"현재 KB에서 \"{question}\"과(와) 관련된 문서를 찾을 수 없습니다.")
        lines.append("")
        lines.append("확실도:")
        lines.append("N/A")
        lines.append("")
        lines.append("주의:")
        lines.append("이 답변은 현재 로컬 KB에 저장된 문서만 기준으로 생성되었습니다.")
        lines.append("검색 결과가 없으므로 정확한 답변을 제공할 수 없습니다.")
        lines.append("=" * 48)
        return "\n".join(lines)

    doc_count = len(contexts)
    lines.append(f"현재 KB에서 \"{question}\"과(와) 관련된 문서 {doc_count}건을 찾았습니다.")
    lines.append("")

    lines.append("근거 문서:")
    for i, ctx in enumerate(contexts, 1):
        lines.append(f"{i}. {ctx['title']}")
        lines.append(f"   path: {ctx['path']}")
        lines.append(f"   score: {ctx['score']:.2e}")
        lines.append(f"   snippet: {ctx['snippet']}")
    lines.append("")

    lines.append("본문 발췌:")
    for i, ctx in enumerate(contexts, 1):
        lines.append(f"[{i}] {ctx['title']}")
        for line in ctx["content_excerpt"].splitlines()[:20]:
            lines.append(f"  {line}")
        lines.append("  ...")
    lines.append("")

    lines.append("확실도:")
    lines.append("source_grounded @ context_only")
    lines.append("")

    lines.append("주의:")
    lines.append("이 답변은 현재 로컬 KB에 저장된 문서만 기준으로 생성되었습니다.")
    lines.append("context에 없는 내용은 추정하지 않았습니다.")
    lines.append("=" * 48)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build context pack and answer.")
    parser.add_argument("question", help="Question to answer")
    parser.add_argument("--limit", type=int, default=3, help="Max documents to include")
    parser.add_argument("--max-chars", type=int, default=1000, help="Max chars per content excerpt")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format (default: json)",
    )
    args = parser.parse_args()

    try:
        query = format_query(args.question)
    except ValueError as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        return

    contexts = build_contexts(query, limit=args.limit, max_chars=args.max_chars)

    if args.format == "json":
        print(
            json.dumps(
                {"status": "ok", "question": args.question, "contexts": contexts},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_answer_text(args.question, contexts))


if __name__ == "__main__":
    main()
