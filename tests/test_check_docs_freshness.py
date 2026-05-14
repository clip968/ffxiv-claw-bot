from __future__ import annotations

import argparse
import os
import unittest
from unittest import mock

from scripts import check_docs_freshness


NEW_DOC_OWNERS = """
version: 1

policy:
  unmatched_code: fail
  archive_docs_are_invalid_owners: true
  notion_is_invalid_owner: true
  handoff_only_satisfies_contract: false

code_paths:
  - "tools/**/*.py"
  - "scripts/**/*.py"
  - "tests/**/*.py"

ignored_paths:
  - "docs/**"
  - "raw/**"
  - "__pycache__/**"
  - "*.pyc"

global_required_on_code_change:
  changed:
    - "docs/handoff/CURRENT_HANDOFF.md"

rules:
  - id: google-drive-sync
    paths:
      - "tools/sync_drive.py"
      - "tests/test_sync_drive.py"
    contract_docs:
      - "docs/specs/0003-google-drive-sync.md"
    procedure_docs:
      - "docs/runbooks/sync-drive.md"
      - "docs/runbooks/test.md"
"""


LEGACY_DOC_OWNERS = """
tools/sync_drive.py:
  required_docs:
    - docs/specs/0003-google-drive-sync.md
    - docs/runbooks/sync-drive.md
    - docs/handoff/CURRENT_HANDOFF.md
"""


class CheckDocsFreshnessTests(unittest.TestCase):
    def config(self) -> check_docs_freshness.DocOwnersConfig:
        return check_docs_freshness.load_doc_owners_from_text(NEW_DOC_OWNERS)

    def test_code_file_with_matching_contract_and_handoff_passes(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/specs/0003-google-drive-sync.md",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            self.config(),
        )

        self.assertFalse(result.should_fail)
        self.assertEqual(result.missing_rule_docs, {})
        self.assertEqual(result.missing_global_docs, [])

    def test_code_file_with_only_handoff_changed_fails_contract_freshness(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            self.config(),
        )

        self.assertTrue(result.should_fail)
        self.assertEqual(
            result.missing_rule_docs,
            {
                "tools/sync_drive.py": {
                    "rule": "google-drive-sync",
                    "required_docs": [
                        "docs/specs/0003-google-drive-sync.md",
                        "docs/runbooks/sync-drive.md",
                        "docs/runbooks/test.md",
                    ],
                }
            },
        )

    def test_code_file_with_no_matching_doc_owners_rule_fails(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "scripts/new_tool.py",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            self.config(),
        )

        self.assertTrue(result.should_fail)
        self.assertEqual(result.unmatched_code_files, ["scripts/new_tool.py"])

    def test_code_file_with_contract_doc_but_missing_global_handoff_fails(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/specs/0003-google-drive-sync.md",
            ],
            self.config(),
        )

        self.assertTrue(result.should_fail)
        self.assertEqual(result.missing_global_docs, ["docs/handoff/CURRENT_HANDOFF.md"])
        self.assertEqual(result.missing_rule_docs, {})

    def test_ignored_path_change_is_ignored_and_passes(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "raw/drive/example.md",
                "tools/__pycache__/sync_drive.cpython-312.pyc",
            ],
            self.config(),
        )

        self.assertFalse(result.should_fail)
        self.assertFalse(result.classification["code_change"])

    def test_archive_doc_does_not_count_as_owner(self) -> None:
        text = NEW_DOC_OWNERS.replace(
            "docs/specs/0003-google-drive-sync.md",
            "docs/archive/old-google-drive-sync.md",
        )
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/archive/old-google-drive-sync.md",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            check_docs_freshness.load_doc_owners_from_text(text),
        )

        self.assertTrue(result.should_fail)
        self.assertEqual(
            result.invalid_owner_docs,
            {"google-drive-sync": ["docs/archive/old-google-drive-sync.md"]},
        )
        self.assertIn("tools/sync_drive.py", result.missing_rule_docs)

    def test_notion_or_external_doc_does_not_count_as_owner(self) -> None:
        text = NEW_DOC_OWNERS.replace(
            "docs/specs/0003-google-drive-sync.md",
            "https://notion.so/example-page",
        )
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            check_docs_freshness.load_doc_owners_from_text(text),
        )

        self.assertTrue(result.should_fail)
        self.assertEqual(
            result.invalid_owner_docs,
            {"google-drive-sync": ["https://notion.so/example-page"]},
        )

    def test_legacy_doc_owners_schema_still_works(self) -> None:
        config = check_docs_freshness.load_doc_owners_from_text(LEGACY_DOC_OWNERS)
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/runbooks/sync-drive.md",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            config,
        )

        self.assertFalse(result.should_fail)
        self.assertEqual([rule.id for rule in config.rules], ["legacy:tools/sync_drive.py"])

    def test_limited_yaml_parser_supports_new_schema_without_pyyaml(self) -> None:
        with mock.patch.object(check_docs_freshness, "yaml", None):
            config = check_docs_freshness.load_doc_owners_from_text(NEW_DOC_OWNERS)

        self.assertEqual(config.policy["unmatched_code"], "fail")
        self.assertEqual(config.global_required_on_code_change, ["docs/handoff/CURRENT_HANDOFF.md"])
        self.assertEqual(config.rules[0].id, "google-drive-sync")
        self.assertEqual(config.rules[0].paths, ["tools/sync_drive.py", "tests/test_sync_drive.py"])

    def test_reviewed_docs_can_optionally_satisfy_contract_docs(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            [
                "tools/sync_drive.py",
                "docs/handoff/CURRENT_HANDOFF.md",
            ],
            self.config(),
            reviewed_docs={"docs/runbooks/sync-drive.md"},
            allow_reviewed_docs=True,
        )

        self.assertFalse(result.should_fail)

    def test_docs_file_only_change_passes(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            ["docs/specs/0003-google-drive-sync.md"],
            self.config(),
        )

        self.assertFalse(result.should_fail)
        self.assertFalse(result.classification["code_change"])
        self.assertTrue(result.classification["docs_change"])

    def test_override_passes_even_without_docs(self) -> None:
        result = check_docs_freshness.evaluate_freshness(
            ["tools/sync_drive.py"],
            self.config(),
            override=True,
        )

        self.assertFalse(result.should_fail)

    def test_env_override_passes_cli_check(self) -> None:
        with mock.patch.dict(os.environ, {"DOCS_UPDATE_NOT_REQUIRED": "1"}):
            with mock.patch.object(
                check_docs_freshness,
                "changed_files_from_args",
                return_value=["tools/sync_drive.py"],
            ):
                with mock.patch.object(
                    check_docs_freshness,
                    "load_doc_owners",
                    return_value=self.config(),
                ):
                    exit_code = check_docs_freshness.main(["--staged"])

        self.assertEqual(exit_code, 0)

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
