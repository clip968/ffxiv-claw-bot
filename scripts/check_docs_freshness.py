from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised where PyYAML is absent.
    yaml = None


DOC_OWNERS_PATH = Path("docs/DOC_OWNERS.yml")
HANDOFF_PATH = Path("docs/handoff/CURRENT_HANDOFF.md")
DEFAULT_CODE_PATHS = (
    "tools/**/*.py",
    "tests/**/*.py",
    "config/**",
    "prompts/**",
    "scripts/**/*.py",
    "*.py",
    "requirements*.txt",
    "pyproject.toml",
    "setup.cfg",
)
DEFAULT_IGNORED_PATHS = (
    "raw/**",
    "wiki/**",
    "graph/**",
    "db/**",
    ".git/**",
    "__pycache__/**",
    "*.pyc",
)
DOCS_PREFIXES = (
    "docs/specs/",
    "docs/adrs/",
    "docs/plans/",
    "docs/runbooks/",
    "docs/handoff/",
    "docs/templates/",
)
DOCS_EXACT = {
    "docs/DOC_OWNERS.yml",
    "docs/WORKFLOW.md",
    "docs/README.md",
    "README.md",
    "CLAUDE.md",
    ".github/pull_request_template.md",
}
HANDOFF_DOC = "docs/handoff/CURRENT_HANDOFF.md"


@dataclass(frozen=True)
class DocOwnerRule:
    id: str
    paths: list[str]
    contract_docs: list[str] = field(default_factory=list)
    procedure_docs: list[str] = field(default_factory=list)

    @property
    def owner_docs(self) -> list[str]:
        return unique_paths([*self.contract_docs, *self.procedure_docs])


@dataclass(frozen=True)
class DocOwnersConfig:
    version: int = 1
    policy: dict[str, Any] = field(default_factory=dict)
    code_paths: list[str] = field(default_factory=lambda: list(DEFAULT_CODE_PATHS))
    ignored_paths: list[str] = field(default_factory=lambda: list(DEFAULT_IGNORED_PATHS))
    global_required_on_code_change: list[str] = field(default_factory=list)
    rules: list[DocOwnerRule] = field(default_factory=list)


@dataclass(frozen=True)
class FreshnessResult:
    classification: dict[str, Any]
    unmatched_code_files: list[str]
    missing_global_docs: list[str]
    missing_rule_docs: dict[str, dict[str, Any]]
    invalid_owner_docs: dict[str, list[str]]
    override: bool = False

    @property
    def should_fail(self) -> bool:
        if self.override:
            return False
        return bool(
            self.unmatched_code_files
            or self.missing_global_docs
            or self.missing_rule_docs
            or self.invalid_owner_docs
        )


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        normalized = normalize_path(str(path))
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def glob_matches(path: str, pattern: str) -> bool:
    normalized_path = normalize_path(path)
    normalized_pattern = normalize_path(pattern)

    if fnmatch.fnmatchcase(normalized_path, normalized_pattern):
        return True

    # Treat "**/" as zero or more directories. fnmatch requires at least one
    # slash for patterns like "tools/**/*.py", but our policy should match
    # both "tools/a.py" and "tools/subdir/a.py".
    if "/**/" in normalized_pattern:
        zero_level_pattern = normalized_pattern.replace("/**/", "/")
        if fnmatch.fnmatchcase(normalized_path, zero_level_pattern):
            return True

    if normalized_pattern.endswith("/**"):
        prefix = normalized_pattern[:-3]
        return normalized_path == prefix.rstrip("/") or normalized_path.startswith(prefix)

    return False


def any_glob_matches(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    return any(glob_matches(path, pattern) for pattern in patterns)


def is_ignored_path(path: str, config: DocOwnersConfig | None = None) -> bool:
    normalized = normalize_path(path)
    patterns = config.ignored_paths if config else list(DEFAULT_IGNORED_PATHS)
    parts = PurePosixPath(normalized).parts
    return any_glob_matches(normalized, patterns) or "__pycache__" in parts


def is_code_path(path: str, config: DocOwnersConfig | None = None) -> bool:
    normalized = normalize_path(path)
    cfg = config or DocOwnersConfig()
    return not is_ignored_path(normalized, cfg) and any_glob_matches(
        normalized, cfg.code_paths
    )


def is_docs_path(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized.startswith(DOCS_PREFIXES) or normalized in DOCS_EXACT


def classify_changed_files(
    paths: list[str], config: DocOwnersConfig | None = None
) -> dict[str, Any]:
    code_files = []
    docs_files = []
    ignored_files = []
    other_files = []

    for path in paths:
        normalized = normalize_path(path)
        if is_docs_path(normalized):
            docs_files.append(normalized)
        elif is_code_path(normalized, config):
            code_files.append(normalized)
        elif is_ignored_path(normalized, config):
            ignored_files.append(normalized)
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
    data = load_yaml(text)
    if not isinstance(data, dict) or "rules" in data or "version" in data:
        return {}

    owners: dict[str, list[str]] = {}
    for code_path, value in data.items():
        if not isinstance(value, dict):
            continue
        required_docs = value.get("required_docs", [])
        if not isinstance(required_docs, list):
            continue
        docs = [normalize_path(str(path)) for path in required_docs]
        if docs:
            owners[normalize_path(str(code_path))] = docs
    return owners


def _legacy_to_config(data: dict[str, Any]) -> DocOwnersConfig:
    rules: list[DocOwnerRule] = []
    global_required: list[str] = []

    for code_path, value in data.items():
        if not isinstance(value, dict):
            continue
        required_docs = value.get("required_docs", [])
        if not isinstance(required_docs, list):
            continue

        normalized_docs = unique_paths([str(path) for path in required_docs])
        owner_docs = [path for path in normalized_docs if path != HANDOFF_DOC]
        if HANDOFF_DOC in normalized_docs:
            global_required.append(HANDOFF_DOC)

        rules.append(
            DocOwnerRule(
                id=f"legacy:{normalize_path(str(code_path))}",
                paths=[normalize_path(str(code_path))],
                contract_docs=owner_docs,
                procedure_docs=[],
            )
        )

    return DocOwnersConfig(
        policy={
            "unmatched_code": "ignore",
            "archive_docs_are_invalid_owners": True,
            "notion_is_invalid_owner": True,
            "handoff_only_satisfies_contract": False,
        },
        global_required_on_code_change=unique_paths(global_required),
        rules=rules,
    )


def load_doc_owners_from_text(text: str) -> DocOwnersConfig:
    data = load_yaml(text)
    if not isinstance(data, dict):
        return DocOwnersConfig()

    if "rules" not in data and "version" not in data:
        return _legacy_to_config(data)

    global_required = data.get("global_required_on_code_change", {})
    if isinstance(global_required, dict):
        global_required_docs = global_required.get("changed", [])
    else:
        global_required_docs = []

    rules: list[DocOwnerRule] = []
    for raw_rule in data.get("rules", []) or []:
        if not isinstance(raw_rule, dict):
            continue
        rule_id = str(raw_rule.get("id") or "unnamed")
        paths = raw_rule.get("paths", []) or []
        contract_docs = raw_rule.get("contract_docs", []) or []
        procedure_docs = raw_rule.get("procedure_docs", []) or []
        rules.append(
            DocOwnerRule(
                id=rule_id,
                paths=unique_paths([str(path) for path in paths]),
                contract_docs=unique_paths([str(path) for path in contract_docs]),
                procedure_docs=unique_paths([str(path) for path in procedure_docs]),
            )
        )

    return DocOwnersConfig(
        version=int(data.get("version", 1) or 1),
        policy=dict(data.get("policy", {}) or {}),
        code_paths=unique_paths(
            [str(path) for path in data.get("code_paths", DEFAULT_CODE_PATHS)]
        ),
        ignored_paths=unique_paths(
            [str(path) for path in data.get("ignored_paths", DEFAULT_IGNORED_PATHS)]
        ),
        global_required_on_code_change=unique_paths(
            [str(path) for path in global_required_docs]
        ),
        rules=rules,
    )


def load_yaml(text: str) -> Any:
    if yaml is not None:
        return yaml.safe_load(text) or {}
    return parse_limited_yaml(text)


def parse_limited_yaml(text: str) -> dict[str, Any]:
    lines = _yaml_lines(text)
    data: dict[str, Any] = {}
    index = 0

    while index < len(lines):
        indent, stripped = lines[index]
        if indent != 0 or not stripped.endswith(":") and ": " not in stripped:
            index += 1
            continue

        key, value = _split_yaml_key_value(stripped)
        if value is not None:
            data[key] = _parse_scalar(value)
            index += 1
            continue

        if key == "rules":
            value, index = _parse_rules(lines, index + 1)
        elif _next_starts_list(lines, index + 1, 2):
            value, index = _parse_list(lines, index + 1, 2)
        else:
            value, index = _parse_mapping(lines, index + 1, 2)
        data[key] = value

    return data


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    parsed: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        without_comment = raw_line.split("#", 1)[0].rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        parsed.append((indent, without_comment.strip()))
    return parsed


def _split_yaml_key_value(line: str) -> tuple[str, str | None]:
    if ": " in line:
        key, value = line.split(": ", 1)
        return key.strip("'\""), value.strip()
    return line[:-1].strip("'\""), None


def _parse_scalar(value: str) -> Any:
    stripped = value.strip().strip("'\"")
    if stripped.casefold() == "true":
        return True
    if stripped.casefold() == "false":
        return False
    if stripped.isdecimal():
        return int(stripped)
    return stripped


def _next_starts_list(lines: list[tuple[int, str]], index: int, indent: int) -> bool:
    return index < len(lines) and lines[index][0] == indent and lines[index][1].startswith("- ")


def _parse_list(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[list[Any], int]:
    items: list[Any] = []
    while index < len(lines):
        line_indent, stripped = lines[index]
        if line_indent < indent:
            break
        if line_indent != indent or not stripped.startswith("- "):
            break
        items.append(_parse_scalar(stripped[2:].strip()))
        index += 1
    return items, index


def _parse_mapping(
    lines: list[tuple[int, str]], index: int, indent: int
) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(lines):
        line_indent, stripped = lines[index]
        if line_indent < indent:
            break
        if line_indent != indent:
            index += 1
            continue

        key, value = _split_yaml_key_value(stripped)
        if value is not None:
            mapping[key] = _parse_scalar(value)
            index += 1
        elif _next_starts_list(lines, index + 1, indent + 2):
            mapping[key], index = _parse_list(lines, index + 1, indent + 2)
        else:
            mapping[key], index = _parse_mapping(lines, index + 1, indent + 2)
    return mapping, index


def _parse_rules(
    lines: list[tuple[int, str]], index: int
) -> tuple[list[dict[str, Any]], int]:
    rules: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    while index < len(lines):
        indent, stripped = lines[index]
        if indent < 2:
            break
        if indent == 2 and stripped.startswith("- "):
            if current is not None:
                rules.append(current)
            current = {}
            item = stripped[2:].strip()
            if item:
                key, value = _split_yaml_key_value(item)
                current[key] = _parse_scalar(value or "")
            index += 1
            continue
        if current is None or indent != 4:
            index += 1
            continue

        key, value = _split_yaml_key_value(stripped)
        if value is not None:
            current[key] = _parse_scalar(value)
            index += 1
        elif _next_starts_list(lines, index + 1, 6):
            current[key], index = _parse_list(lines, index + 1, 6)
        else:
            current[key], index = _parse_mapping(lines, index + 1, 6)

    if current is not None:
        rules.append(current)
    return rules, index


def load_doc_owners(path: Path = DOC_OWNERS_PATH) -> DocOwnersConfig:
    if not path.exists():
        return DocOwnersConfig()
    return load_doc_owners_from_text(path.read_text(encoding="utf-8"))


def is_invalid_owner_doc(path: str, config: DocOwnersConfig) -> bool:
    normalized = normalize_path(path)
    lower = normalized.casefold()
    if normalized == HANDOFF_DOC:
        return True
    if config.policy.get("archive_docs_are_invalid_owners", True) and normalized.startswith(
        "docs/archive/"
    ):
        return True
    if config.policy.get("notion_is_invalid_owner", True) and (
        lower.startswith(("http://", "https://"))
    ):
        return True
    return False


def valid_owner_docs(rule: DocOwnerRule, config: DocOwnersConfig) -> list[str]:
    return [
        path for path in rule.owner_docs if not is_invalid_owner_doc(path, config)
    ]


def invalid_owner_docs_by_rule(config: DocOwnersConfig) -> dict[str, list[str]]:
    invalid: dict[str, list[str]] = {}
    for rule in config.rules:
        docs = [path for path in rule.owner_docs if is_invalid_owner_doc(path, config)]
        if docs:
            invalid[rule.id] = docs
    return invalid


def matching_rules(path: str, config: DocOwnersConfig) -> list[DocOwnerRule]:
    return [
        rule
        for rule in config.rules
        if any(glob_matches(path, pattern) for pattern in rule.paths)
    ]


def evaluate_freshness(
    paths: list[str],
    config: DocOwnersConfig,
    *,
    reviewed_docs: set[str] | None = None,
    allow_reviewed_docs: bool = False,
    override: bool = False,
) -> FreshnessResult:
    classification = classify_changed_files(paths, config)
    changed_docs = {normalize_path(path) for path in classification["docs_files"]}
    reviewed = {normalize_path(path) for path in (reviewed_docs or set())}
    unmatched_code_files: list[str] = []
    missing_rule_docs: dict[str, dict[str, Any]] = {}

    for code_file in classification["code_files"]:
        rules = matching_rules(code_file, config)
        if not rules:
            if config.policy.get("unmatched_code", "fail") == "fail":
                unmatched_code_files.append(code_file)
            continue

        if any(
            _rule_has_fresh_doc(
                rule,
                config,
                changed_docs,
                reviewed,
                allow_reviewed_docs=allow_reviewed_docs,
            )
            for rule in rules
        ):
            continue

        first_rule = rules[0]
        missing_rule_docs[code_file] = {
            "rule": first_rule.id,
            "required_docs": valid_owner_docs(first_rule, config),
        }

    missing_global_docs: list[str] = []
    if classification["code_change"]:
        for doc_path in config.global_required_on_code_change:
            normalized = normalize_path(doc_path)
            if normalized not in changed_docs:
                missing_global_docs.append(normalized)

    return FreshnessResult(
        classification=classification,
        unmatched_code_files=unmatched_code_files,
        missing_global_docs=missing_global_docs,
        missing_rule_docs=missing_rule_docs,
        invalid_owner_docs=invalid_owner_docs_by_rule(config),
        override=override,
    )


def _rule_has_fresh_doc(
    rule: DocOwnerRule,
    config: DocOwnersConfig,
    changed_docs: set[str],
    reviewed_docs: set[str],
    *,
    allow_reviewed_docs: bool,
) -> bool:
    docs = valid_owner_docs(rule, config)
    if any(path in changed_docs for path in docs):
        return True
    return allow_reviewed_docs and any(path in reviewed_docs for path in docs)


def find_missing_required_docs(
    code_files: list[str],
    docs_files: list[str],
    doc_owners: dict[str, list[str]] | DocOwnersConfig,
    *,
    reviewed_docs: set[str] | None = None,
    allow_reviewed_docs: bool = False,
) -> dict[str, Any]:
    if isinstance(doc_owners, DocOwnersConfig):
        paths = [*code_files, *docs_files]
        return evaluate_freshness(
            paths,
            doc_owners,
            reviewed_docs=reviewed_docs,
            allow_reviewed_docs=allow_reviewed_docs,
        ).missing_rule_docs

    config = _legacy_to_config(
        {code_path: {"required_docs": docs} for code_path, docs in doc_owners.items()}
    )
    paths = [*code_files, *docs_files]
    result = evaluate_freshness(
        paths,
        config,
        reviewed_docs=reviewed_docs,
        allow_reviewed_docs=allow_reviewed_docs,
    )
    return {
        code_file: detail["required_docs"]
        for code_file, detail in result.missing_rule_docs.items()
    }


def should_fail_docs_check(
    code_change: bool,
    docs_change: bool,
    override: bool,
    missing_required_docs: dict[str, Any] | None = None,
) -> bool:
    if override:
        return False
    if missing_required_docs:
        return True
    return code_change and not docs_change


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when code changes have no related docs contract update."
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

    config = load_doc_owners()
    reviewed_docs = load_reviewed_docs() if args.allow_reviewed_docs else set()
    result = evaluate_freshness(
        paths,
        config,
        reviewed_docs=reviewed_docs,
        allow_reviewed_docs=args.allow_reviewed_docs,
        override=override,
    )
    classification = result.classification

    print("docs freshness check")
    print(f"  changed files: {len(paths)}")
    print(f"  code files: {len(classification['code_files'])}")
    print(f"  docs files: {len(classification['docs_files'])}")
    print(f"  doc owner rules: {len(config.rules)}")

    if override:
        print("  override: DOCS_UPDATE_NOT_REQUIRED=1")
    if args.allow_reviewed_docs:
        print(f"  reviewed docs allowed: {len(reviewed_docs)}")

    if result.should_fail:
        print("  result: fail")
        if result.unmatched_code_files:
            print("  reason: code files changed without a matching DOC_OWNERS rule")
            for code_file in result.unmatched_code_files:
                print(f"    - {code_file}")
        if result.missing_global_docs:
            print("  reason: code changed without required global docs update")
            for doc_path in result.missing_global_docs:
                print(f"    - {doc_path}")
        if result.invalid_owner_docs:
            print("  reason: DOC_OWNERS contains invalid owner docs")
            for rule_id, docs in result.invalid_owner_docs.items():
                print(f"  invalid owner docs for {rule_id}:")
                for doc_path in docs:
                    print(f"    - {doc_path}")
        if result.missing_rule_docs:
            print("  reason: matched code changed without contract/procedure doc update")
            for code_file, detail in result.missing_rule_docs.items():
                print(f"  missing owner docs for {code_file} ({detail['rule']}):")
                for doc_path in detail["required_docs"]:
                    print(f"    - {doc_path}")
        return 1

    print("  result: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
