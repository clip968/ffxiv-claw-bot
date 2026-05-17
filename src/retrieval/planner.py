from __future__ import annotations

from src.derived_wiki.job_catalog import resolve_job
from src.query.models import ParsedQuery
from src.retrieval.models import RetrievalPlan, RetrievalTarget


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
    return " ".join(dict.fromkeys(alias for alias in aliases if alias))
