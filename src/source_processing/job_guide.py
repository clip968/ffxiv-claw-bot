from __future__ import annotations

import re

from src.derived_wiki.job_catalog import JOB_CATALOG, resolve_job


STRUCTURAL_JOB_GUIDE_LINES = {
    "-",
    "action name",
    "actions & traits",
    "acquired",
    "cast",
    "crafting & gathering guide",
    "deutsch",
    "effect",
    "english (uk)",
    "english (us)",
    "francais",
    "franã§ais",
    "gameplay guide",
    "job actions",
    "last update:",
    "mp cost",
    "pvp guide",
    "radius",
    "range",
    "recast",
    "type",
    "ui guide",
    "æ¥æ¬èª",
}


def detect_official_job_slug(title: str, text: str = "") -> str | None:
    for candidate in _job_guide_candidates(title, text):
        job = resolve_job(candidate)
        if job is not None:
            return job.slug
    return None


def clean_official_job_guide_text(text: str, job_slug: str) -> str:
    job = resolve_job(job_slug)
    if job is None:
        return text

    current_job_names = {_normalize_name(job.slug), _normalize_name(job.display_name)}
    current_job_names.update(_normalize_name(alias) for alias in job.aliases)
    all_job_names = _all_job_names()

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = _normalize_name(line)
        if normalized in STRUCTURAL_JOB_GUIDE_LINES:
            continue
        if normalized in all_job_names and normalized not in current_job_names:
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def is_official_job_guide_title(title: str) -> bool:
    return detect_official_job_slug(title) is not None


def _job_guide_candidates(title: str, text: str) -> tuple[str, ...]:
    candidates: list[str] = []
    for value in (title, text):
        if not value:
            continue
        candidates.extend(
            match.group(1).strip()
            for match in re.finditer(
                r"(?:Official FFXIV Job Guide -|Job Guide:)\s*(.+?)(?:\s*\|\s*FINAL FANTASY XIV|\s*$)",
                value,
                flags=re.IGNORECASE | re.MULTILINE,
            )
        )
    return tuple(dict.fromkeys(candidates))


def _all_job_names() -> set[str]:
    names: set[str] = set()
    for job in JOB_CATALOG:
        names.add(_normalize_name(job.slug))
        names.add(_normalize_name(job.display_name))
        names.update(_normalize_name(alias) for alias in job.aliases)
    return names


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())
