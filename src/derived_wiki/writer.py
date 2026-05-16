from __future__ import annotations

from pathlib import Path


def write_derived_wiki(path: Path | str, content: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
