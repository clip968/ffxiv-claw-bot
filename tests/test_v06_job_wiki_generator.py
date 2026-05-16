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


class V06JobWikiGeneratorTests(unittest.TestCase):
    fixture_dir = Path("tests/fixtures/source_summaries")

    def _summaries(self):
        from src.derived_wiki.summary_loader import load_summaries

        return load_summaries(self.fixture_dir)

    def _job(self, query: str = "gunbreaker"):
        from src.derived_wiki.job_catalog import resolve_job

        job = resolve_job(query)
        self.assertIsNotNone(job)
        return job

    def test_generate_single_job_wiki_creates_file(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "wiki" / "jobs"

            result = generate_job_wiki(self._job(), self._summaries(), target_root)

            self.assertIsNotNone(result)
            self.assertEqual(result.path, target_root / "gunbreaker.md")
            self.assertTrue(result.path.exists())

    def test_generate_job_wiki_includes_job_title(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_job_wiki(self._job(), self._summaries(), Path(tmp_dir))

            self.assertIn("# Gunbreaker 변경 이력", result.content)

    def test_generate_job_wiki_includes_matching_patch_entries(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_job_wiki(self._job(), self._summaries(), Path(tmp_dir))

            self.assertIn("Continuation potency adjusted", result.content)
            self.assertIn("No Mercy window clarified", result.content)
            self.assertNotIn("Atonement combo flow updated", result.content)
            self.assertNotIn("Inner Release timing adjusted", result.content)

    def test_generate_job_wiki_preserves_source_id(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_job_wiki(self._job(), self._summaries(), Path(tmp_dir))

            self.assertIn("## 7.0", result.content)
            self.assertIn("source_id: patch_7_0", result.content)
            self.assertIn("source_id: patch_7_1", result.content)

    def test_generate_job_wiki_sorts_entries_by_patch_version(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_job_wiki(self._job(), list(reversed(self._summaries())), Path(tmp_dir))

            self.assertLess(result.content.index("## 7.0"), result.content.index("## 7.1"))

    def test_generate_job_wiki_deduplicates_duplicate_entries(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki
        from src.derived_wiki.summary_loader import load_summaries

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "summaries"
            root.mkdir()
            (root / "patch_7_0.md").write_text(
                "# Patch 7.0 Notes\n\nsource_id: patch_7_0\n\n## Gunbreaker\n\n- Duplicate change.\n",
                encoding="utf-8",
            )
            (root / "patch_7_1.md").write_text(
                "# Patch 7.1 Notes\n\nsource_id: patch_7_1\n\n## Gunbreaker\n\n- Duplicate change.\n",
                encoding="utf-8",
            )

            result = generate_job_wiki(self._job(), load_summaries(root), Path(tmp_dir) / "jobs")

            self.assertEqual(result.content.count("Duplicate change."), 1)

    def test_generate_job_wiki_dry_run_does_not_write_file(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"

            result = generate_job_wiki(
                self._job(),
                self._summaries(),
                target_root,
                dry_run=True,
            )

            self.assertIsNotNone(result)
            self.assertFalse(result.path.exists())
            self.assertFalse(result.written)

    def test_generate_job_wiki_patch_range_filter(self) -> None:
        from src.derived_wiki.job_wiki_generator import generate_job_wiki

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = generate_job_wiki(
                self._job(),
                self._summaries(),
                Path(tmp_dir),
                patch_range="7.1..7.1",
            )

            self.assertNotIn("Continuation potency adjusted", result.content)
            self.assertIn("No Mercy window clarified", result.content)
            self.assertNotIn("## 7.0", result.content)
            self.assertIn("## 7.1", result.content)

    def test_generate_job_wiki_cli_dry_run_does_not_write_file(self) -> None:
        import contextlib
        import io
        import json

        from tools.generate_job_wiki import main

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                main(
                    [
                        "--job",
                        "gunbreaker",
                        "--summary-root",
                        str(self.fixture_dir),
                        "--target-root",
                        str(target_root),
                        "--dry-run",
                    ]
                )

            result = json.loads(stdout.getvalue())

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["summary"]["generated"], 1)
        self.assertFalse((target_root / "gunbreaker.md").exists())


class V06GenerateDerivedWikiCliTests(unittest.TestCase):
    fixture_dir = Path("tests/fixtures/source_summaries")

    def _run_cli(self, argv: list[str]) -> dict:
        import contextlib
        import io
        import json

        from tools.generate_derived_wiki import main

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main(argv)
        return json.loads(stdout.getvalue())

    def test_generate_derived_wiki_jobs_invokes_job_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"

            result = self._run_cli(
                [
                    "--kind",
                    "jobs",
                    "--job",
                    "gunbreaker",
                    "--summary-root",
                    str(self.fixture_dir),
                    "--target-root",
                    str(target_root),
                ]
            )

            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["kind"], "jobs")
            self.assertEqual(result["summary"]["generated"], 1)
            self.assertTrue((target_root / "gunbreaker.md").exists())

    def test_generate_derived_wiki_jobs_passes_job_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"

            result = self._run_cli(
                [
                    "--kind",
                    "jobs",
                    "--job",
                    "paladin",
                    "--summary-root",
                    str(self.fixture_dir),
                    "--target-root",
                    str(target_root),
                ]
            )

            self.assertEqual(result["actions"][0]["job"], "paladin")
            self.assertTrue((target_root / "paladin.md").exists())
            self.assertFalse((target_root / "gunbreaker.md").exists())

    def test_generate_derived_wiki_jobs_passes_patch_range(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"

            self._run_cli(
                [
                    "--kind",
                    "jobs",
                    "--job",
                    "gunbreaker",
                    "--patch-range",
                    "7.1..7.1",
                    "--summary-root",
                    str(self.fixture_dir),
                    "--target-root",
                    str(target_root),
                ]
            )

            content = (target_root / "gunbreaker.md").read_text(encoding="utf-8")
            self.assertNotIn("## 7.0", content)
            self.assertIn("## 7.1", content)

    def test_generate_derived_wiki_jobs_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_root = Path(tmp_dir) / "jobs"

            result = self._run_cli(
                [
                    "--kind",
                    "jobs",
                    "--job",
                    "gunbreaker",
                    "--summary-root",
                    str(self.fixture_dir),
                    "--target-root",
                    str(target_root),
                    "--dry-run",
                ]
            )

            self.assertTrue(result["dry_run"])
            self.assertEqual(result["summary"]["generated"], 1)
            self.assertFalse((target_root / "gunbreaker.md").exists())

    def test_generate_derived_wiki_rejects_unknown_kind(self) -> None:
        import subprocess
        import sys

        completed = subprocess.run(
            [sys.executable, "tools/generate_derived_wiki.py", "--kind", "raids"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("not supported in v0.6", completed.stderr)


if __name__ == "__main__":
    unittest.main()
