from __future__ import annotations

import unittest
from pathlib import Path


class V06ExtractorModelTests(unittest.TestCase):
    def test_extracted_source_requires_text_and_metadata(self) -> None:
        from src.source_processing import ExtractedSource

        with self.assertRaises(TypeError):
            ExtractedSource(title="Patch Notes")  # type: ignore[call-arg]

    def test_extracted_source_preserves_title_text_metadata(self) -> None:
        from src.source_processing import ExtractedSource

        metadata = {
            "source_path": "/tmp/patch.md",
            "extension": ".md",
            "extracted_at": "2026-05-16T00:00:00+00:00",
            "extractor_name": "markdown",
        }
        source = ExtractedSource(
            title="Patch Notes",
            text="# Patch Notes\n\nGunbreaker potency changed.",
            metadata=metadata,
        )

        self.assertEqual(source.title, "Patch Notes")
        self.assertIn("Gunbreaker", source.text)
        self.assertEqual(source.metadata, metadata)

    def test_unsupported_extension_error_includes_extension_and_path(self) -> None:
        from src.source_processing import UnsupportedSourceExtensionError

        error = UnsupportedSourceExtensionError(".png", Path("/tmp/source.png"))

        self.assertEqual(error.extension, ".png")
        self.assertEqual(error.source_path, "/tmp/source.png")
        self.assertIn(".png", str(error))
        self.assertIn("/tmp/source.png", str(error))

    def test_source_decoding_error_is_extraction_error(self) -> None:
        from src.source_processing import SourceDecodingError, SourceExtractionError

        error = SourceDecodingError("Could not decode", source_path="/tmp/source.txt")

        self.assertIsInstance(error, SourceExtractionError)
        self.assertEqual(error.source_path, "/tmp/source.txt")
        self.assertIn("Could not decode", str(error))

    def test_source_parse_error_is_extraction_error(self) -> None:
        from src.source_processing import SourceExtractionError, SourceParseError

        error = SourceParseError("Could not parse", source_path="/tmp/source.csv")

        self.assertIsInstance(error, SourceExtractionError)
        self.assertEqual(error.source_path, "/tmp/source.csv")
        self.assertIn("Could not parse", str(error))
