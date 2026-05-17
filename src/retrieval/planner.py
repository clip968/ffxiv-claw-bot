from __future__ import annotations

from src.derived_wiki.job_catalog import resolve_job
from src.query.models import ParsedQuery
from src.retrieval.models import RetrievalPlan, RetrievalTarget

ITEM_QUERY_KEYWORDS = (
    "item",
    "weapon",
    "gear",
    "equipment",
    "drop",
    "source",
    "obtain",
    "acquisition",
    "아이템",
    "무기",
    "장비",
    "방어구",
    "획득",
    "얻",
    "드랍",
    "보상",
    "출처",
    "건블레이드",
)


def build_retrieval_plan(parsed: ParsedQuery, *, limit: int = 5) -> RetrievalPlan:
    if parsed.intent == "job_change_history" and parsed.job:
        query = _job_query(parsed.job)
        return RetrievalPlan(
            primary=(
                RetrievalTarget(
                    wiki_type="job",
                    topic=parsed.job,
                    query=query,
                    priority=0,
                ),
            ),
            fallback=(
                RetrievalTarget(
                    wiki_type="source_summary",
                    topic=None,
                    query=query,
                    priority=10,
                ),
                RetrievalTarget(
                    wiki_type=None,
                    topic=None,
                    query=query,
                    priority=20,
                ),
            ),
            limit=limit,
        )

    if _is_item_query(parsed):
        return RetrievalPlan(
            primary=(
                RetrievalTarget(
                    wiki_type="item",
                    topic=None,
                    query=_item_query(parsed),
                    priority=0,
                ),
            ),
            fallback=(
                RetrievalTarget(
                    wiki_type=None,
                    topic=None,
                    query=parsed.normalized_query,
                    priority=10,
                ),
            ),
            limit=limit,
        )

    return RetrievalPlan(
        primary=(
            RetrievalTarget(
                wiki_type=None,
                topic=None,
                query=parsed.normalized_query,
                priority=0,
            ),
        ),
        fallback=(),
        limit=limit,
    )


def _job_query(job_slug: str) -> str:
    job = resolve_job(job_slug)
    if job is None:
        return job_slug
    aliases = (job.slug, job.display_name, *job.aliases)
    return " OR ".join(dict.fromkeys(alias for alias in aliases if alias))


def _is_item_query(parsed: ParsedQuery) -> bool:
    query = parsed.normalized_query
    return any(keyword in query for keyword in ITEM_QUERY_KEYWORDS)


def _item_query(parsed: ParsedQuery) -> str:
    terms = [parsed.normalized_query, *parsed.terms]
    if parsed.job:
        job = resolve_job(parsed.job)
        if job:
            terms.extend((job.slug, job.display_name, *job.aliases))
        else:
            terms.append(parsed.job)
    return " OR ".join(dict.fromkeys(term for term in terms if term))
