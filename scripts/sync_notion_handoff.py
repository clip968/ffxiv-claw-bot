from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = ROOT / "docs" / "handoff" / "CURRENT_HANDOFF.md"
NOTION_VERSION = "2022-06-28"


def read_handoff() -> str:
    return HANDOFF_PATH.read_text(encoding="utf-8")


def build_plain_text_summary(markdown: str, max_chars: int = 1800) -> str:
    summary = markdown.strip()
    if len(summary) <= max_chars:
        return summary
    return summary[:max_chars].rsplit("\n", 1)[0] + "\n..."


def print_dry_run(summary: str) -> None:
    print("Notion handoff sync dry-run")
    print("source: docs/handoff/CURRENT_HANDOFF.md")
    print("target: NOTION_HANDOFF_PAGE_ID")
    print("mode: mirror/index only; docs remain source of truth")
    print("--- preview ---")
    print(summary)


def append_plain_text_block(api_key: str, page_id: str, summary: str) -> None:
    # Notion is a mirror/index for handoff content. The source of truth remains
    # docs/handoff/CURRENT_HANDOFF.md in this repository.
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": summary,
                            },
                        }
                    ]
                },
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        response.read()


def apply_sync(summary: str) -> int:
    api_key = os.environ.get("NOTION_API_KEY")
    page_id = os.environ.get("NOTION_HANDOFF_PAGE_ID")
    if not api_key or not page_id:
        print(
            "NOTION_API_KEY and NOTION_HANDOFF_PAGE_ID are required for --apply",
            file=sys.stderr,
        )
        return 1

    try:
        append_plain_text_block(api_key, page_id, summary)
    except urllib.error.URLError as exc:
        print(f"Notion apply failed: {exc}", file=sys.stderr)
        return 1

    print("Notion handoff mirror updated")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirror docs handoff content to Notion."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Print planned sync.")
    mode.add_argument("--apply", action="store_true", help="Apply mirror update to Notion.")
    args = parser.parse_args(argv)

    summary = build_plain_text_summary(read_handoff())
    if args.apply:
        return apply_sync(summary)

    print_dry_run(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
