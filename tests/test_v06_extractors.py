from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SOURCE_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "source_files"


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


class V06ExtractorRegistryTests(unittest.TestCase):
    def test_registry_selects_text_extractor_for_txt(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        extractor = get_extractor_for_path("guide.txt")

        self.assertEqual(extractor.__name__, "extract_text_file")

    def test_registry_selects_markdown_extractor_for_md(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        extractor = get_extractor_for_path("guide.md")

        self.assertEqual(extractor.__name__, "extract_markdown_file")

    def test_registry_selects_html_extractor_for_html_and_htm(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        self.assertEqual(get_extractor_for_path("patch.html").__name__, "extract_html_file")
        self.assertEqual(get_extractor_for_path("patch.htm").__name__, "extract_html_file")

    def test_registry_selects_csv_extractor_for_csv(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        extractor = get_extractor_for_path("drops.csv")

        self.assertEqual(extractor.__name__, "extract_csv_file")

    def test_registry_selects_xlsx_extractor_for_xlsx(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        extractor = get_extractor_for_path("drops.xlsx")

        self.assertEqual(extractor.__name__, "extract_xlsx_file")

    def test_registry_is_case_insensitive(self) -> None:
        from src.source_processing.extractor_registry import get_extractor_for_path

        self.assertEqual(get_extractor_for_path("PATCH.HTML").__name__, "extract_html_file")
        self.assertEqual(get_extractor_for_path("DROPS.XLSX").__name__, "extract_xlsx_file")

    def test_registry_raises_for_unsupported_extension(self) -> None:
        from src.source_processing import UnsupportedSourceExtensionError
        from src.source_processing.extractor_registry import get_extractor_for_path

        with self.assertRaises(UnsupportedSourceExtensionError) as caught:
            get_extractor_for_path("/tmp/source.png")

        self.assertEqual(caught.exception.extension, ".png")
        self.assertIn("/tmp/source.png", str(caught.exception))

    def test_extract_source_text_uses_selected_extractor(self) -> None:
        from src.source_processing.extractor_registry import extract_source_text

        with TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "guide.txt"
            source_path.write_text("placeholder", encoding="utf-8")

            extracted = extract_source_text(source_path)

        self.assertEqual(extracted.title, "guide")
        self.assertEqual(extracted.metadata["extension"], ".txt")
        self.assertEqual(extracted.metadata["extractor_name"], "text")


class V06TextMarkdownHtmlExtractorTests(unittest.TestCase):
    def test_text_extractor_preserves_plain_text(self) -> None:
        from src.source_processing.extractors.text import extract_text_file

        source_path = SOURCE_FIXTURES / "sample.txt"

        extracted = extract_text_file(source_path)

        self.assertEqual(extracted.title, "sample")
        self.assertEqual(
            extracted.text,
            source_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(extracted.metadata["extractor_name"], "text")

    def test_text_extractor_raises_on_invalid_encoding(self) -> None:
        from src.source_processing import SourceDecodingError
        from src.source_processing.extractors.text import extract_text_file

        with TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "broken.txt"
            source_path.write_bytes(b"\xff\xfe\x00")

            with self.assertRaises(SourceDecodingError):
                extract_text_file(source_path)

    def test_markdown_extractor_preserves_headings(self) -> None:
        from src.source_processing.extractors.markdown import extract_markdown_file

        extracted = extract_markdown_file(SOURCE_FIXTURES / "sample.md")

        self.assertIn("# Patch 7.5 Notes", extracted.text)
        self.assertIn("## Gunbreaker", extracted.text)
        self.assertEqual(extracted.metadata["extractor_name"], "markdown")

    def test_markdown_extractor_records_frontmatter_metadata(self) -> None:
        from src.source_processing.extractors.markdown import extract_markdown_file

        extracted = extract_markdown_file(SOURCE_FIXTURES / "sample.md")

        self.assertEqual(extracted.metadata["frontmatter"]["patch"], "7.5")
        self.assertEqual(extracted.metadata["frontmatter"]["category"], "patch_notes")

    def test_html_extractor_removes_script_and_style(self) -> None:
        from src.source_processing.extractors.html import extract_html_file

        extracted = extract_html_file(SOURCE_FIXTURES / "sample.html")

        self.assertNotIn("console.log", extracted.text)
        self.assertNotIn("display: none", extracted.text)
        self.assertIn("script", extracted.metadata["removed_elements"])
        self.assertIn("style", extracted.metadata["removed_elements"])

    def test_html_extractor_removes_nav_and_footer(self) -> None:
        from src.source_processing.extractors.html import extract_html_file

        extracted = extract_html_file(SOURCE_FIXTURES / "sample.html")

        self.assertNotIn("Navigation noise", extracted.text)
        self.assertNotIn("Footer noise", extracted.text)
        self.assertIn("nav", extracted.metadata["removed_elements"])
        self.assertIn("footer", extracted.metadata["removed_elements"])

    def test_html_extractor_preserves_main_content(self) -> None:
        from src.source_processing.extractors.html import extract_html_file

        extracted = extract_html_file(SOURCE_FIXTURES / "sample.html")

        self.assertIn("Patch 7.5 Notes", extracted.text)
        self.assertIn("Gunbreaker potency has been adjusted.", extracted.text)
        self.assertEqual(extracted.metadata["html_title"], "Patch 7.5 Notes")

    def test_registry_uses_concrete_document_extractors(self) -> None:
        from src.source_processing.extractor_registry import extract_source_text

        txt = extract_source_text(SOURCE_FIXTURES / "sample.txt")
        markdown = extract_source_text(SOURCE_FIXTURES / "sample.md")
        html = extract_source_text(SOURCE_FIXTURES / "sample.html")

        self.assertIn("Plain text opener", txt.text)
        self.assertIn("Gunbreaker", markdown.text)
        self.assertIn("Gunbreaker potency", html.text)
