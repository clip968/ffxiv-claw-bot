from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.derived_wiki.job_catalog import JobEntry
from src.derived_wiki.summary_loader import SourceSummary
from src.derived_wiki.writer import write_derived_wiki


@dataclass(frozen=True)
class JobWikiEntry:
    patch_version: str | None
    source_id: str
    text: str


@dataclass(frozen=True)
class GeneratedJobWiki:
    job: JobEntry
    path: Path
    content: str
    entries: tuple[JobWikiEntry, ...]
    written: bool


def collect_job_entries(
    job: JobEntry,
    summaries: list[SourceSummary],
    *,
    patch_range: str | None = None,
) -> list[JobWikiEntry]:
    entries: list[JobWikiEntry] = []
    for summary in summaries:
        if not _patch_in_range(summary.patch_version, patch_range):
            continue
        for text in _matching_texts(job, summary.text):
            entries.append(
                JobWikiEntry(
                    patch_version=summary.patch_version,
                    source_id=summary.source_id,
                    text=text,
                )
            )
    return _sort_and_dedupe(entries)


def render_job_wiki(job: JobEntry, entries: list[JobWikiEntry]) -> str:
    lines = [
        f"# {job.display_name} 변경 이력",
        "",
        "## 개요",
        "",
        (
            f"이 문서는 source summaries를 기반으로 {job.display_name} "
            "관련 변경 사항을 시간순으로 정리한다."
        ),
        "",
    ]

    grouped = _group_entries_by_patch(entries)
    for patch_version, patch_entries in grouped:
        lines.extend([f"## {patch_version or 'Unknown Patch'}", "", "### 변경 사항"])
        for entry in patch_entries:
            lines.append(_as_bullet(entry.text))
        lines.extend(["", "### 출처"])
        for source_id in _unique(entry.source_id for entry in patch_entries):
            lines.append(f"- source_id: {source_id}")
        lines.append("")

    lines.extend(
        [
            "## 누적 요약",
            "",
            "- v06에서는 근거 기반 bullet만 나열한다.",
            "- 해석형 요약은 후속 버전에서 LLM summarizer로 확장한다.",
            "",
        ]
    )
    return "\n".join(lines)


def generate_job_wiki(
    job: JobEntry,
    summaries: list[SourceSummary],
    target_root: Path | str,
    *,
    dry_run: bool = False,
    patch_range: str | None = None,
) -> GeneratedJobWiki | None:
    entries = collect_job_entries(job, summaries, patch_range=patch_range)
    if not entries:
        return None
    target = Path(target_root) / f"{job.slug}.md"
    content = render_job_wiki(job, entries)
    if not dry_run:
        write_derived_wiki(target, content)
    return GeneratedJobWiki(
        job=job,
        path=target,
        content=content,
        entries=tuple(entries),
        written=not dry_run,
    )


def _matching_texts(job: JobEntry, text: str) -> list[str]:
    matches: list[str] = []
    in_matching_section = False
    section_level = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2)
            if in_matching_section and level > section_level:
                continue
            in_matching_section = _matches_job(job, title)
            section_level = level if in_matching_section else 0
            continue

        if in_matching_section:
            nested_heading = re.match(r"^(#{1,6})\s+", line)
            if nested_heading and len(nested_heading.group(1)) <= section_level:
                in_matching_section = False
            else:
                cleaned = _clean_entry_text(line)
                if cleaned:
                    matches.append(cleaned)
                continue

        if _matches_job(job, line):
            cleaned = _clean_entry_text(line)
            if cleaned:
                matches.append(cleaned)

    return matches


def _matches_job(job: JobEntry, text: str) -> bool:
    normalized_text = _normalize(text)
    aliases = {_normalize(job.slug), _normalize(job.display_name)}
    aliases.update(_normalize(alias) for alias in job.aliases)
    for alias in aliases:
        if not alias:
            continue
        if _is_ascii_alias(alias):
            pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
            if re.search(pattern, normalized_text):
                return True
        elif alias in normalized_text:
            return True
    return False


def _clean_entry_text(line: str) -> str:
    line = re.sub(r"^[-*]\s+", "", line.strip())
    line = re.sub(r"^\d+[.)]\s+", "", line)
    return line.strip()


def _sort_and_dedupe(entries: list[JobWikiEntry]) -> list[JobWikiEntry]:
    seen: set[str] = set()
    deduped: list[JobWikiEntry] = []
    for entry in sorted(entries, key=lambda item: (_patch_key(item.patch_version), item.source_id)):
        key = _normalize(entry.text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def _group_entries_by_patch(entries: list[JobWikiEntry]) -> list[tuple[str | None, list[JobWikiEntry]]]:
    grouped: list[tuple[str | None, list[JobWikiEntry]]] = []
    for entry in entries:
        if not grouped or grouped[-1][0] != entry.patch_version:
            grouped.append((entry.patch_version, [entry]))
        else:
            grouped[-1][1].append(entry)
    return grouped


def _patch_in_range(patch_version: str | None, patch_range: str | None) -> bool:
    if not patch_range or not patch_version:
        return True
    if ".." not in patch_range:
        return patch_version == patch_range
    start, end = patch_range.split("..", 1)
    value = _patch_key(patch_version)
    return _patch_key(start) <= value <= _patch_key(end)


def _patch_key(patch_version: str | None) -> tuple[int, ...]:
    if not patch_version:
        return (9999,)
    parts = re.findall(r"\d+", patch_version)
    if not parts:
        return (9999,)
    return tuple(int(part) for part in parts)


def _as_bullet(text: str) -> str:
    return f"- {_clean_entry_text(text)}"


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def _is_ascii_alias(value: str) -> bool:
    return all(ord(char) < 128 for char in value)
