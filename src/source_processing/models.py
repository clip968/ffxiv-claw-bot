from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractedSource:
    """Normalized source text plus metadata from an extractor.

    Required metadata keys: source_path, extension, extracted_at, extractor_name.
    """

    title: str
    text: str
    metadata: dict[str, Any]
