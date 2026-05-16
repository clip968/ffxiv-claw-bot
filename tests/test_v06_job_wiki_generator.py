from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class V06DerivedWikiFoundationTests(unittest.TestCase):
    fixture_dir = Path("tests/fixtures/source_summaries")

    def test_summary_loader_reads_source_summary_files(self) -> None:
        from src.derived_wiki.summary_loader import load_summaries

        summaries = load_summaries(self.fixture_dir)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(
            [summary.path.name for summary in summaries],
            ["patch_7_0.md", "patch_7_1.md"],
        )

    def test_summary_loader_extracts_source_id(self) -> None:
        from src.derived_wiki.summary_loader import load_summaries

        summaries = {summary.source_id: summary for summary in load_summaries(self.fixture_dir)}

        self.assertIn("patch_7_0", summaries)
        self.assertIn("Continuation potency adjusted", summaries["patch_7_0"].text)

    def test_summary_loader_extracts_patch_version_from_filename(self) -> None:
        from src.derived_wiki.summary_loader import load_summaries

        summaries = {summary.source_id: summary for summary in load_summaries(self.fixture_dir)}

        self.assertEqual(summaries["patch_7_0"].patch_version, "7.0")
        self.assertEqual(summaries["patch_7_1"].patch_version, "7.1")
        self.assertEqual(summaries["patch_7_0"].title, "Patch 7.0 Notes")

    def test_summary_loader_extracts_patch_version_from_heading(self) -> None:
        from src.derived_wiki.summary_loader import load_summaries

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "custom_summary.md").write_text(
                "# Patch 7.2 Notes\n\nsource_id: custom_source\n\n## Gunbreaker\n\n- Change.\n",
                encoding="utf-8",
            )

            summaries = load_summaries(root)

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].source_id, "custom_source")
        self.assertEqual(summaries[0].patch_version, "7.2")

    def test_summary_writer_writes_to_target_path(self) -> None:
        from src.derived_wiki.writer import write_derived_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "wiki" / "jobs" / "gunbreaker.md"

            write_derived_wiki(target, "# Gunbreaker\n\n- Change.\n")

            self.assertEqual(target.read_text(encoding="utf-8"), "# Gunbreaker\n\n- Change.\n")

    def test_summary_writer_creates_missing_parent_directory(self) -> None:
        from src.derived_wiki.writer import write_derived_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "missing" / "jobs" / "warrior.md"

            write_derived_wiki(target, "# Warrior\n")

            self.assertTrue(target.exists())
            self.assertTrue(target.parent.is_dir())

    def test_templates_render_heading_and_section(self) -> None:
        from src.derived_wiki.templates import render_heading, render_section

        self.assertEqual(render_heading("Gunbreaker", level=1), "# Gunbreaker")
        self.assertEqual(
            render_section("Overview", ["Line one.", "Line two."]),
            "## Overview\n\nLine one.\nLine two.",
        )


class V06JobCatalogTests(unittest.TestCase):
    def test_job_catalog_contains_gunbreaker(self) -> None:
        from src.derived_wiki.job_catalog import resolve_job

        job = resolve_job("gunbreaker")

        self.assertIsNotNone(job)
        self.assertEqual(job.slug, "gunbreaker")
        self.assertEqual(job.display_name, "Gunbreaker")

    def test_job_catalog_contains_all_combat_jobs(self) -> None:
        from src.derived_wiki.job_catalog import list_jobs

        expected_slugs = {
            "paladin",
            "warrior",
            "dark_knight",
            "gunbreaker",
            "white_mage",
            "scholar",
            "astrologian",
            "sage",
            "monk",
            "dragoon",
            "ninja",
            "samurai",
            "reaper",
            "viper",
            "bard",
            "machinist",
            "dancer",
            "black_mage",
            "summoner",
            "red_mage",
            "pictomancer",
            "blue_mage",
        }

        self.assertEqual(
            {job.slug for job in list_jobs(include_limited=True)},
            expected_slugs,
        )

    def test_job_catalog_resolves_english_alias(self) -> None:
        from src.derived_wiki.job_catalog import resolve_job

        self.assertEqual(resolve_job("Gunbreaker").slug, "gunbreaker")
        self.assertEqual(resolve_job("Black Mage").slug, "black_mage")

    def test_job_catalog_resolves_abbreviation_alias(self) -> None:
        from src.derived_wiki.job_catalog import resolve_job

        self.assertEqual(resolve_job("GNB").slug, "gunbreaker")
        self.assertEqual(resolve_job("BLM").slug, "black_mage")
        self.assertEqual(resolve_job("PLD").slug, "paladin")

    def test_job_catalog_resolves_korean_alias(self) -> None:
        from src.derived_wiki.job_catalog import resolve_job

        self.assertEqual(resolve_job("건브레이커").slug, "gunbreaker")
        self.assertEqual(resolve_job("흑마도사").slug, "black_mage")
        self.assertEqual(resolve_job("나이트").slug, "paladin")

    def test_job_catalog_can_exclude_limited_jobs(self) -> None:
        from src.derived_wiki.job_catalog import list_jobs

        self.assertNotIn("blue_mage", {job.slug for job in list_jobs()})

    def test_job_catalog_can_include_limited_jobs(self) -> None:
        from src.derived_wiki.job_catalog import list_jobs, resolve_job

        self.assertIn("blue_mage", {job.slug for job in list_jobs(include_limited=True)})
        self.assertTrue(resolve_job("BLU").is_limited)


if __name__ == "__main__":
    unittest.main()
