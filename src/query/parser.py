from __future__ import annotations

from src.query.intent_detector import detect_intent
from src.query.job_detector import detect_job
from src.query.models import ParsedQuery
from src.query.normalize import extract_terms, normalize_query
from src.query.patch_parser import parse_patch_range


def parse_query(query: str) -> ParsedQuery:
    normalized = normalize_query(query)
    job = detect_job(normalized)
    return ParsedQuery(
        raw_query=query,
        normalized_query=normalized,
        intent=detect_intent(normalized, job=job),
        job=job,
        patch_range=parse_patch_range(normalized),
        topic="job" if job else None,
        terms=extract_terms(normalized),
    )
