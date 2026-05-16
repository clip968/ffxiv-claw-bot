from __future__ import annotations

import re

PATCH = r"(\d+)\.(\d+)"
PATCH_X = r"(\d+)\.x"


def parse_patch_range(query: str) -> str | None:
    text = query.casefold()

    korean_range = re.search(rf"{PATCH}\s*부터\s*{PATCH}\s*까지", text)
    if korean_range:
        return _range_from_match_groups(korean_range.groups())

    explicit_range = re.search(rf"{PATCH}\s*[~\-–]\s*{PATCH}", text)
    if explicit_range:
        return _range_from_match_groups(explicit_range.groups())

    x_range = re.search(PATCH_X, text)
    if x_range:
        major = int(x_range.group(1))
        return f"{major}.0..{major}.99"

    single = re.search(PATCH, text)
    if single:
        major = int(single.group(1))
        minor = int(single.group(2))
        return f"{major}.{minor}..{major}.{minor}"

    return None


def _range_from_match_groups(groups: tuple[str, ...]) -> str:
    start_major, start_minor, end_major, end_minor = (int(part) for part in groups)
    return f"{start_major}.{start_minor}..{end_major}.{end_minor}"
