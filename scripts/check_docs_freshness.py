from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath


DOC_OWNERS_PATH = Path("docs/DOC_OWNERS.yml")
HANDOFF_PATH = Path("docs/handoff/CURRENT_HANDOFF.md")
IGNORED_PREFIXES = ("raw/", "wiki/", "graph/", "db/", ".git/")
CODE_PREFIXES = ("tools/", "tests/", "config/", "prompts/", "scripts/")
DOCS_PREFIXES = (
    "docs/specs/",
    "docs/adrs/",
    "docs/plans/",
    "docs/runbooks/",
    "docs/handoff/",
)
DOCS_EXACT = {"docs/DOC_OWNERS.yml", "docs/WORKFLOW.md", "README.md", "CLAUDE.md"}
CODE_EXACT = {"pyproject.toml", "setup.cfg"}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def is_ignored_path(path: str) -> bool:
    normalized = normalize_path(path)
    parts = PurePosixPath(normalized).parts
    return (
        normalized.startswith(IGNORED_PREFIXES)
        or "__pycache__" in parts
        or normalized.endswith(".pyc")
    )


def is_code_path(path: str) -> bool:
    normalized = normalize_path(path)
    if is_ignored_path(normalized):
        return False

    name = PurePosixPath(normalized).name
    return (
        normalized.startswith(CODE_PREFIXES)
        or ("/" not in normalized and normalized.endswith(".py"))
        or name.startswith("requirements") and name.endswith(".txt")
        or normalized in CODE_EXACT
    )


def is_docs_path(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized.startswith(DOCS_PREFIXES) or normalized in DOCS_EXACT


def classify_changed_files(paths: list[str]) -> dict:
    code_files = []
    docs_files = []
    ignored_files = []
    other_files = []

    for path in paths:
        normalized = normalize_path(path)
        if is_ignored_path(normalized):
            ignored_files.append(normalized)
        elif is_code_path(normalized):
            code_files.append(normalized)
        elif is_docs_path(normalized):
            docs_files.append(normalized)
        else:
            other_files.append(normalized)

    return {
        "code_change": bool(code_files),
        "docs_change": bool(docs_files),
        "code_files": code_files,
        "docs_files": docs_files,
        "ignored_files": ignored_files,
        "other_files": other_files,
    }


def parse_doc_owners(text: str) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    current_path: str | None = None
    in_required_docs = False

    for raw_line in text.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment.strip():
            continue

        stripped = line_without_comment.strip()
        if not raw_line.startswith((" ", "\t")) and stripped.endswith(":"):
            current_path = normalize_path(stripped[:-1])
            owners.setdefault(current_path, [])
            in_required_docs = False
            continue

        if current_path is None:
            continue

        if stripped == "required_docs:":
            in_required_docs = True
            continue

        if in_required_docs and stripped.startswith("- "):
            owners[current_path].append(normalize_path(stripped[2:].strip("'\"")))

    return {path: docs for path, docs in owners.items() if docs}


def load_doc_owners(path: Path = DOC_OWNERS_PATH) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    return parse_doc_owners(path.read_text(encoding="utf-8"))


def parse_reviewed_docs(text: str) -> set[str]:
    reviewed_docs: set[str] = set()
    in_reviewed_docs = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            in_reviewed_docs = stripped.casefold() == "## reviewed docs"
            continue

        if not in_reviewed_docs or not stripped.startswith("- "):
            continue

        bullet = stripped[2:].strip()
        backtick_match = re.search(r"`([^`]+)`", bullet)
        candidate = backtick_match.group(1) if backtick_match else bullet.split()[0]
        reviewed_docs.add(normalize_path(candidate.strip("'\"")))

    return reviewed_docs


def load_reviewed_docs(path: Path = HANDOFF_PATH) -> set[str]:
    if not path.exists():
        return set()
    return parse_reviewed_docs(path.read_text(encoding="utf-8"))


def find_missing_required_docs(
    code_files: list[str],
    docs_files: list[str],
    doc_owners: dict[str, list[str]],
    *,
    reviewed_docs: set[str] | None = None,
    allow_reviewed_docs: bool = False,
) -> dict[str, list[str]]:
    changed_docs = {normalize_path(path) for path in docs_files}
    reviewed = reviewed_docs or set()
    missing: dict[str, list[str]] = {}

    for code_file in code_files:
        normalized_code_file = normalize_path(code_file)
        required_docs = [
            normalize_path(path) for path in doc_owners.get(normalized_code_file, [])
        ]
        if not required_docs:
            continue

        has_required_doc_change = any(path in changed_docs for path in required_docs)
        has_reviewed_doc = allow_reviewed_docs and any(
            path in reviewed for path in required_docs
        )
        if not has_required_doc_change and not has_reviewed_doc:
            missing[normalized_code_file] = required_docs

    return missing


def should_fail_docs_check(
    code_change: bool,
    docs_change: bool,
    override: bool,
    missing_required_docs: dict[str, list[str]] | None = None,
) -> bool:
    if override:
        return False
    if missing_required_docs:
        return True
    return code_change and not docs_change


def run_git_name_only(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files_from_args(args: argparse.Namespace) -> list[str]:
    if getattr(args, "all", False):
        return unique_paths(
            [
                *run_git_name_only(["diff", "--cached", "--name-only"]),
                *run_git_name_only(["diff", "--name-only"]),
                *run_git_name_only(["ls-files", "--others", "--exclude-standard"]),
            ]
        )

    if args.staged:
        return run_git_name_only(["diff", "--cached", "--name-only"])

    if args.base and args.head:
        return run_git_name_only(["diff", "--name-only", args.base, args.head])

    raise ValueError("provide --all, --staged, or both --base and --head")


def unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        normalized = normalize_path(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when code changes have no related docs update."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check staged, unstaged, and untracked files.",
    )
    parser.add_argument("--staged", action="store_true", help="Check staged files.")
    parser.add_argument("--base", help="Base git revision.")
    parser.add_argument("--head", help="Head git revision.")
    parser.add_argument(
        "--allow-reviewed-docs",
        action="store_true",
        help=(
            "Allow required docs listed under CURRENT_HANDOFF.md "
            "'Reviewed docs' to satisfy mapped code changes."
        ),
    )
    args = parser.parse_args(argv)

    override = os.environ.get("DOCS_UPDATE_NOT_REQUIRED") == "1"

    try:
        paths = changed_files_from_args(args)
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f"docs freshness check error: {exc}", file=sys.stderr)
        return 1

    classification = classify_changed_files(paths)
    doc_owners = load_doc_owners()
    reviewed_docs = load_reviewed_docs() if args.allow_reviewed_docs else set()
    missing_required_docs = find_missing_required_docs(
        classification["code_files"],
        classification["docs_files"],
        doc_owners,
        reviewed_docs=reviewed_docs,
        allow_reviewed_docs=args.allow_reviewed_docs,
    )

    print("docs freshness check")
    print(f"  changed files: {len(paths)}")
    print(f"  code files: {len(classification['code_files'])}")
    print(f"  docs files: {len(classification['docs_files'])}")
    print(f"  doc owner mappings: {len(doc_owners)}")

    if override:
        print("  override: DOCS_UPDATE_NOT_REQUIRED=1")
    if args.allow_reviewed_docs:
        print(f"  reviewed docs allowed: {len(reviewed_docs)}")

    if should_fail_docs_check(
        classification["code_change"],
        classification["docs_change"],
        override,
        missing_required_docs=missing_required_docs,
    ):
        print("  result: fail")
        if missing_required_docs:
            print("  reason: mapped code changed without any required docs update")
            for code_file, required_docs in missing_required_docs.items():
                print(f"  missing required docs for {code_file}:")
                for required_doc in required_docs:
                    print(f"    - {required_doc}")
        else:
            print("  reason: code changed but no docs/spec/runbook/handoff update was found")
        return 1

    print("  result: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
