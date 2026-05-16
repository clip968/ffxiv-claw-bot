from __future__ import annotations

from pathlib import Path


class SourceExtractionError(Exception):
    def __init__(self, message: str, *, source_path: str | Path | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.source_path = str(source_path) if source_path is not None else None


class UnsupportedSourceExtensionError(SourceExtractionError):
    def __init__(self, extension: str, source_path: str | Path) -> None:
        normalized_extension = extension if extension.startswith(".") else f".{extension}"
        self.extension = normalized_extension.lower()
        self.source_path = str(source_path)
        super().__init__(
            f"Unsupported source extension: {self.extension} (path={self.source_path})",
            source_path=self.source_path,
        )


class SourceDecodingError(SourceExtractionError):
    pass


class SourceParseError(SourceExtractionError):
    pass
