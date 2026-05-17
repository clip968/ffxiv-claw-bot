from __future__ import annotations


def confidence_for_context_count(count: int) -> str:
    if count <= 0:
        return "N/A"
    return "source_grounded"
