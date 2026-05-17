from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.answering import compose_answer
from src.query import parse_query
from src.retrieval import (
    build_context_pack,
    build_retrieval_plan,
    execute_graph_aware_retrieval,
    execute_retrieval_plan,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask the grounded FFXIV KB.")
    parser.add_argument("question", help="Question to answer")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--db-path", type=Path, default=ROOT / "db" / "ffxiv.sqlite")
    parser.add_argument("--root-path", type=Path, default=ROOT)
    parser.add_argument("--graph-dir", type=Path, default=ROOT / "graph")
    return parser


def run_ask(args: argparse.Namespace) -> dict[str, Any]:
    question = args.question
    if not question.strip():
        return {
            "status": "error",
            "question": question,
            "error_stage": "parse",
            "error_message": "question must not be empty",
            "actions": [],
        }

    parsed = parse_query(question)
    plan = build_retrieval_plan(parsed, limit=args.limit)
    results = execute_retrieval_plan(plan, db_path=args.db_path)
    results = execute_graph_aware_retrieval(
        question,
        results,
        db_path=args.db_path,
        graph_dir=args.graph_dir,
        limit=max(args.limit, 8),
    )
    context_pack = build_context_pack(
        question,
        parsed,
        plan,
        results,
        root_path=args.root_path,
    )
    answer = compose_answer(context_pack)

    payload: dict[str, Any] = {
        "status": "ok",
        "question": question,
        "contexts": [dataclasses.asdict(context) for context in context_pack.contexts],
        "answer": {
            "format": "text",
            "body": answer.body,
            "confidence": answer.confidence,
            "sources": list(answer.sources),
        },
        "actions": [],
    }
    if args.debug:
        payload["parsed_query"] = dataclasses.asdict(parsed)
        payload["retrieval_plan"] = dataclasses.asdict(plan)
    return payload


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = run_ask(args)
    if args.format == "text" and payload.get("status") == "ok":
        print(payload["answer"]["body"])
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
