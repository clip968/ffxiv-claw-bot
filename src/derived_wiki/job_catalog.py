from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobEntry:
    slug: str
    display_name: str
    aliases: tuple[str, ...]
    is_limited: bool = False


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


JOB_CATALOG: tuple[JobEntry, ...] = (
    JobEntry("paladin", "Paladin", ("paladin", "pld", "나이트")),
    JobEntry("warrior", "Warrior", ("warrior", "war", "전사")),
    JobEntry("dark_knight", "Dark Knight", ("dark knight", "drk", "암흑기사", "암기")),
    JobEntry("gunbreaker", "Gunbreaker", ("gunbreaker", "gnb", "건브레이커", "건브")),
    JobEntry("white_mage", "White Mage", ("white mage", "whm", "백마도사", "백마")),
    JobEntry("scholar", "Scholar", ("scholar", "sch", "학자", "학")),
    JobEntry("astrologian", "Astrologian", ("astrologian", "ast", "점성술사", "점성")),
    JobEntry("sage", "Sage", ("sage", "sge", "현자")),
    JobEntry("monk", "Monk", ("monk", "mnk", "몽크")),
    JobEntry("dragoon", "Dragoon", ("dragoon", "drg", "용기사", "용기")),
    JobEntry("ninja", "Ninja", ("ninja", "nin", "닌자")),
    JobEntry("samurai", "Samurai", ("samurai", "sam", "사무라이", "사무")),
    JobEntry("reaper", "Reaper", ("reaper", "rpr", "리퍼")),
    JobEntry("viper", "Viper", ("viper", "vpr", "바이퍼")),
    JobEntry("bard", "Bard", ("bard", "brd", "음유시인", "음유")),
    JobEntry("machinist", "Machinist", ("machinist", "mch", "기공사", "기공")),
    JobEntry("dancer", "Dancer", ("dancer", "dnc", "무도가", "무도")),
    JobEntry("black_mage", "Black Mage", ("black mage", "blm", "흑마도사", "흑마")),
    JobEntry("summoner", "Summoner", ("summoner", "smn", "소환사", "솬사")),
    JobEntry("red_mage", "Red Mage", ("red mage", "rdm", "적마도사", "적마")),
    JobEntry("pictomancer", "Pictomancer", ("pictomancer", "pct", "픽토맨서", "픽토")),
    JobEntry("blue_mage", "Blue Mage", ("blue mage", "blu", "청마도사", "청마"), True),
)

_ALIAS_INDEX = {}
for job in JOB_CATALOG:
    aliases = {_normalize(job.slug), _normalize(job.display_name)}
    aliases.update(_normalize(alias) for alias in job.aliases)
    for alias in aliases:
        existing = _ALIAS_INDEX.get(alias)
        if existing and existing.slug != job.slug:
            raise ValueError(
                f"Duplicate job alias {alias!r}: {existing.slug} and {job.slug}"
            )
        _ALIAS_INDEX[alias] = job


def list_jobs(*, include_limited: bool = False) -> list[JobEntry]:
    return [
        job
        for job in JOB_CATALOG
        if include_limited or not job.is_limited
    ]


def resolve_job(query: str) -> JobEntry | None:
    return _ALIAS_INDEX.get(_normalize(query))
