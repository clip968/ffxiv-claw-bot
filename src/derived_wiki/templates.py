from __future__ import annotations


def render_heading(title: str, *, level: int = 1) -> str:
    level = min(max(level, 1), 6)
    return f"{'#' * level} {title.strip()}"


def render_section(title: str, lines: list[str] | tuple[str, ...], *, level: int = 2) -> str:
    body = "\n".join(line.rstrip() for line in lines).strip()
    heading = render_heading(title, level=level)
    if not body:
        return heading
    return f"{heading}\n\n{body}"
