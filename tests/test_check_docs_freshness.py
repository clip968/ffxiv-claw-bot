from __future__ import annotations

import os
import argparse
import unittest
from unittest import mock

from scripts import check_docs_freshness
from scripts.check_docs_freshness import (
    classify_changed_files,
    find_missing_required_docs,
    should_fail_docs_check,
)


DOC_OWNERS = {
    "tools/sync_drive.py": [
        "docs/specs/0003-google-drive-sync.md",
        "docs/runbooks/sync-drive.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    ],
    "scripts/sync_notion_handoff.py": [
        "docs/runbooks/notion-sync.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    ],
}


class CheckDocsFreshnessTests(unittest.TestCase):
    def test_code_file_only_change_fails(self) -> None:
        result = classify_changed_files(["tools/sync_drive.py"])

        self.assertTrue(result["code_change"])
        self.assertFalse(result["docs_change"])
        self.assertTrue(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
            )
        )

    def test_mapped_code_change_fails_without_required_docs(self) -> None:
        result = classify_changed_files(["tools/sync_drive.py"])
        missing = find_missing_required_docs(
            result["code_files"],
            result["docs_files"],
            DOC_OWNERS,
        )

        self.assertEqual(
            missing,
            {
                "tools/sync_drive.py": [
                    "docs/specs/0003-google-drive-sync.md",
                    "docs/runbooks/sync-drive.md",
                    "docs/handoff/CURRENT_HANDOFF.md",
                ]
            },
        )
        self.assertTrue(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
                missing_required_docs=missing,
            )
        )

    def test_mapped_code_change_passes_with_required_spec(self) -> None:
        result = classify_changed_files(
            [
                "tools/sync_drive.py",
                "docs/specs/0003-google-drive-sync.md",
            ]
        )
        missing = find_missing_required_docs(
            result["code_files"],
            result["docs_files"],
            DOC_OWNERS,
        )

        self.assertEqual(missing, {})
        self.assertFalse(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
                missing_required_docs=missing,
            )
        )

    def test_sync_notion_change_passes_with_required_runbook(self) -> None:
        result = classify_changed_files(
            [
                "scripts/sync_notion_handoff.py",
                "docs/runbooks/notion-sync.md",
            ]
        )
        missing = find_missing_required_docs(
            result["code_files"],
            result["docs_files"],
            DOC_OWNERS,
        )

        self.assertEqual(missing, {})
        self.assertFalse(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
                missing_required_docs=missing,
            )
        )

    def test_reviewed_docs_can_optionally_satisfy_required_docs(self) -> None:
        result = classify_changed_files(["tools/sync_drive.py"])
        missing = find_missing_required_docs(
            result["code_files"],
            result["docs_files"],
            DOC_OWNERS,
            reviewed_docs={"docs/runbooks/sync-drive.md"},
            allow_reviewed_docs=True,
        )

        self.assertEqual(missing, {})

    def test_docs_file_only_change_passes(self) -> None:
        result = classify_changed_files(["docs/specs/0003-google-drive-sync.md"])

        self.assertFalse(result["code_change"])
        self.assertTrue(result["docs_change"])
        self.assertFalse(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
            )
        )

    def test_code_and_docs_change_passes(self) -> None:
        result = classify_changed_files(
            [
                "scripts/finish_task.py",
                "docs/runbooks/finish-task.md",
            ]
        )

        self.assertTrue(result["code_change"])
        self.assertTrue(result["docs_change"])
        self.assertFalse(
            should_fail_docs_check(
                result["code_change"],
                result["docs_change"],
                override=False,
            )
        )

    def test_override_passes_even_without_docs(self) -> None:
        self.assertFalse(
            should_fail_docs_check(
                code_change=True,
                docs_change=False,
                override=True,
                missing_required_docs={
                    "tools/sync_drive.py": ["docs/specs/0003-google-drive-sync.md"]
                },
            )
        )

    def test_env_override_passes_cli_check(self) -> None:
        with mock.patch.dict(os.environ, {"DOCS_UPDATE_NOT_REQUIRED": "1"}):
            with mock.patch.object(
                check_docs_freshness,
                "changed_files_from_args",
                return_value=["tools/sync_drive.py"],
            ):
                exit_code = check_docs_freshness.main(["--staged"])

        self.assertEqual(exit_code, 0)

    def test_generated_and_cache_paths_are_not_code_changes(self) -> None:
        result = classify_changed_files(
            [
                "raw/urls/example.html",
                "wiki/source_summaries/example.md",
                "graph/nodes.json",
                "db/ffxiv.sqlite",
                "tools/__pycache__/sync_drive.cpython-312.pyc",
            ]
        )

        self.assertFalse(result["code_change"])
        self.assertFalse(result["docs_change"])

    def test_all_mode_collects_staged_unstaged_and_untracked(self) -> None:
        args = argparse.Namespace(staged=False, all=True, base=None, head=None)

        def fake_git_name_only(git_args: list[str]) -> list[str]:
            if git_args == ["diff", "--cached", "--name-only"]:
                return ["scripts/check_docs_freshness.py"]
            if git_args == ["diff", "--name-only"]:
                return ["docs/WORKFLOW.md"]
            if git_args == ["ls-files", "--others", "--exclude-standard"]:
                return ["docs/DOC_OWNERS.yml"]
            return []

        with mock.patch.object(
            check_docs_freshness,
            "run_git_name_only",
            side_effect=fake_git_name_only,
        ):
            paths = check_docs_freshness.changed_files_from_args(args)

        self.assertEqual(
            paths,
            [
                "scripts/check_docs_freshness.py",
                "docs/WORKFLOW.md",
                "docs/DOC_OWNERS.yml",
            ],
        )


if __name__ == "__main__":
    unittest.main()
