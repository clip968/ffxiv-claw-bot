from __future__ import annotations

JOB_CHANGE_KEYWORDS = (
    "변경 이력",
    "변경점",
    "뭐 바뀜",
    "바뀐",
    "패치 변경",
    "change history",
    "changes",
)


def detect_intent(query: str, *, job: str | None = None) -> str:
    normalized = " ".join(query.strip().casefold().split())
    if job and any(keyword in normalized for keyword in JOB_CHANGE_KEYWORDS):
        return "job_change_history"
    return "generic_search"
