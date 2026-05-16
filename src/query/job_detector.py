from __future__ import annotations

import re

from src.derived_wiki.job_catalog import JOB_CATALOG


def detect_job(query: str) -> str | None:
    normalized = _normalize(query)
    candidates: list[tuple[int, str]] = []

    for job in JOB_CATALOG:
        aliases = {job.slug, job.display_name, *job.aliases}
        for alias in aliases:
            alias_norm = _normalize(alias)
            if not alias_norm:
                continue
            if _matches_alias(normalized, alias_norm):
                candidates.append((len(alias_norm), job.slug))

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate[0])[1]


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def _matches_alias(text: str, alias: str) -> bool:
    if _is_ascii(alias):
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return alias in text


def _is_ascii(value: str) -> bool:
    return all(ord(char) < 128 for char in value)
