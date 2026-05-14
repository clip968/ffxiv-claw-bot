from __future__ import annotations

import argparse
import hashlib
import io
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
DEFAULT_CREDENTIALS_PATH = ROOT / "config" / "google_drive_client_secret.json"
DEFAULT_TOKEN_PATH = ROOT / "config" / "google_drive_token_write.json"
DEFAULT_FOLDERS_CONFIG = ROOT / "config" / "drive_folders.yaml"

DRIVE_SOURCE_PREFIX = "gdrive://"
WRITE_SCOPES = ("https://www.googleapis.com/auth/drive",)

# v04-00 ingest contract: valid categories matching FFXIV_KB Drive folder structure
VALID_CATEGORIES = {
    "patch_notes",
    "job_guides",
    "raid_guides",
    "static_docs",
    "macros",
    "bis_sheets",
    "personal_notes",
}

# v04-00 ingest contract: supported source types
VALID_SOURCE_TYPES = {"text_note", "markdown_file", "plain_text_file"}
TEXT_SOURCE_TYPES = {"text_note", "markdown_file", "plain_text_file"}

SOURCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT,
  source_url TEXT,
  raw_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  language TEXT,
  patch TEXT,
  job TEXT,
  raid TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
"""


class DriveAuthError(RuntimeError):
    pass


class DriveApiError(RuntimeError):
    pass


def safe_path_part(value: str) -> str:
    import re

    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9가-힣._-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("._")
    return normalized or "untitled"


def drive_source_url(drive_file_id: str) -> str:
    return f"{DRIVE_SOURCE_PREFIX}{drive_file_id}"


def drive_source_id(drive_file_id: str) -> str:
    return f"drive_{safe_path_part(drive_file_id)}"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def date_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def content_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def load_folders_config(config_path: Path) -> dict[str, str]:
    """Load category -> folder_id mapping from YAML config file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Folders config not found: {config_path}")
    raw = config_path.read_text(encoding="utf-8")

    try:
        import yaml as _yaml  # type: ignore[import]
    except ModuleNotFoundError:
        data = parse_simple_folders_yaml(raw)
    else:
        data = _yaml.safe_load(raw) or {}

    if not isinstance(data, dict):
        raise ValueError("Folders config must be a YAML mapping")

    return {str(key): str(value) for key, value in data.items() if value is not None}


def parse_simple_folders_yaml(text: str) -> dict[str, str]:
    """Parse the flat category: folder_id YAML shape without PyYAML."""
    folders: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Invalid folders config line {line_number}: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip().strip("'\"")
        value = value.strip().strip("'\"")
        if not key or not value:
            raise ValueError(f"Invalid folders config line {line_number}: {raw_line}")
        folders[key] = value
    return folders


def ensure_sources_table(conn: sqlite3.Connection) -> None:
    conn.execute(SOURCES_SCHEMA)


def load_drive_credentials(token_path: Path) -> Any:
    """Load OAuth credentials from a saved token file.

    This function is swappable in tests to avoid real Drive API dependency.
    """
    if not token_path.exists():
        raise DriveAuthError(
            f"OAuth token not found: {token_path}. "
            "Run --auth with --credentials-path first."
        )

    try:
        from google.oauth2.credentials import Credentials
    except ModuleNotFoundError as exc:
        raise DriveAuthError(
            "Google API client dependencies are not installed. "
            "Install google-auth, google-auth-oauthlib, and google-api-python-client."
        ) from exc

    credentials = Credentials.from_authorized_user_file(
        str(token_path),
        scopes=list(WRITE_SCOPES),
    )

    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request
        except ModuleNotFoundError as exc:
            raise DriveAuthError(
                "google-auth transport dependency is not installed."
            ) from exc
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials.valid:
        raise DriveAuthError(
            f"OAuth token is invalid or expired without refresh token: {token_path}. "
            "Run --auth again."
        )

    return credentials


def build_drive_service(credentials: Any) -> Any:
    """Build a Drive API v3 service from credentials.

    This function is swappable in tests to avoid real Drive API dependency.
    """
    try:
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise DriveApiError(
            "Google API client dependency is not installed. "
            "Install google-api-python-client."
        ) from exc
    return build("drive", "v3", credentials=credentials)


def run_drive_auth(credentials_path: Path, token_path: Path) -> dict[str, Any]:
    """Run OAuth browser flow for Drive write scope."""
    if not credentials_path.exists():
        raise DriveAuthError(
            f"OAuth client secret not found: {credentials_path}. "
            "Download it from Google Cloud Console."
        )

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ModuleNotFoundError as exc:
        raise DriveAuthError(
            "Google OAuth dependency is not installed. "
            "Install google-auth-oauthlib."
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        scopes=list(WRITE_SCOPES),
    )
    credentials = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return {
        "status": "ok",
        "auth": True,
        "token_path": str(token_path),
    }


def infer_source_type(args: argparse.Namespace) -> str:
    """Infer the source_type from CLI arguments.

    Defaults to text_note. Uses --source-type if provided.
    """
    if args.source_type:
        return args.source_type
    return "text_note"


def infer_mime_type(source_type: str) -> str:
    """Map source_type to a Drive MIME type for upload."""
    return {
        "text_note": "text/markdown",
        "markdown_file": "text/markdown",
        "plain_text_file": "text/plain",
    }.get(source_type, "text/markdown")


def infer_file_extension(source_type: str) -> str:
    return {
        "text_note": "md",
        "markdown_file": "md",
        "plain_text_file": "txt",
    }.get(source_type, "md")


def validate_input(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Validate input and return a list of error actions if any."""
    errors: list[dict[str, Any]] = []

    source_type = infer_source_type(args)

    # Validate category
    if args.category not in VALID_CATEGORIES:
        errors.append(
            _error_action(
                source_type=source_type,
                title=args.title or "",
                message=(
                    f"Invalid category '{args.category}'. "
                    f"Valid categories: {', '.join(sorted(VALID_CATEGORIES))}"
                ),
                error_type="invalid_input",
            )
        )

    # Validate body for text source types
    if source_type in TEXT_SOURCE_TYPES and not args.body:
        errors.append(
            _error_action(
                source_type=source_type,
                title=args.title or "",
                message=f"--body is required for {', '.join(sorted(TEXT_SOURCE_TYPES))} source types",
                error_type="invalid_input",
            )
        )

    return errors


def _error_action(
    *,
    source_type: str,
    title: str,
    message: str,
    error_type: str = "invalid_input",
) -> dict[str, Any]:
    return {
        "action": "error",
        "source_type": source_type,
        "title": title,
        "category": None,
        "drive_file_id": None,
        "drive_url": None,
        "source_id": None,
        "raw_path": None,
        "rebuild_status": "skipped",
        "message": message,
        "error_type": error_type,
    }


def _success_action(
    *,
    source_type: str,
    title: str,
    category: str,
    drive_file_id: str,
    drive_url: str,
    source_id: str,
    raw_path: str,
    rebuild_status: str,
    message: str,
) -> dict[str, Any]:
    return {
        "action": "drive_upload",
        "source_type": source_type,
        "title": title,
        "category": category,
        "drive_file_id": drive_file_id,
        "drive_url": drive_url,
        "source_id": source_id,
        "raw_path": raw_path,
        "rebuild_status": rebuild_status,
        "message": message,
    }


def _summary_from_actions(actions: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {
        "total": len(actions),
        "uploaded": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }
    for action in actions:
        if action["action"] == "drive_upload":
            summary["uploaded"] += 1
        elif action["action"] == "drive_update":
            summary["updated"] += 1
        elif action["action"] in ("error",):
            summary["errors"] += 1
        elif action["action"] == "skip":
            summary["skipped"] += 1
    return summary


def _infer_status(actions: list[dict[str, Any]]) -> str:
    has_success = any(a["action"] == "drive_upload" for a in actions)
    has_error = any(a["action"] == "error" for a in actions)
    if has_success and has_error:
        return "partial"
    if has_error:
        return "failed"
    return "success"


def planned_raw_path(category: str, title: str, source_type: str, drive_file_id: str) -> str:
    ext = infer_file_extension(source_type)
    filename = f"{safe_path_part(title)}__{safe_path_part(drive_file_id)}.{ext}"
    return f"raw/drive/{safe_path_part(category)}/{filename}"


def check_duplicate_title(db_path: Path, title: str, category: str) -> bool:
    """Check if a source with the same title already exists in the DB."""
    if not db_path.exists():
        return False
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM sources WHERE title = ? AND raw_path LIKE ? LIMIT 1",
            (title, f"raw/drive/{safe_path_part(category)}/%"),
        ).fetchone()
        return row is not None
    except sqlite3.OperationalError:
        return False
    finally:
        conn.close()


def resolve_drive_file_name(title: str, db_path: Path, category: str) -> str:
    """Resolve the Drive file name, appending timestamp if duplicate exists."""
    if check_duplicate_title(db_path, title, category):
        return f"{title} __{date_str()}"
    return title


def upsert_source(
    db_path: Path,
    source_id: str,
    source_type: str,
    title: str,
    source_url: str,
    raw_path: str,
    hash_value: str,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        ensure_sources_table(conn)
        now = utc_now()
        conn.execute(
            """
            INSERT OR REPLACE INTO sources (
              id, source_type, title, source_url, raw_path, content_hash,
              created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, COALESCE(
              (SELECT created_at FROM sources WHERE id = ?), ?
            ), ?)
            """,
            (
                source_id,
                source_type,
                title,
                source_url,
                raw_path,
                hash_value,
                source_id,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def plan_dry_run(args: argparse.Namespace, folders: dict[str, str]) -> dict[str, Any]:
    """Execute a dry-run: plan what would happen without making any changes."""
    validation_errors = validate_input(args)
    if validation_errors:
        return {
            "status": _infer_status(validation_errors),
            "actions": validation_errors,
            "summary": _summary_from_actions(validation_errors),
            "dry_run": True,
        }

    category = args.category
    title = args.title or "untitled"
    source_type = infer_source_type(args)

    folder_id = folders.get(category)
    if not folder_id:
        error = _error_action(
            source_type=source_type,
            title=title,
            message=(
                f"Category '{category}' not found in --folders-config. "
                f"Available: {', '.join(sorted(folders.keys()))}"
            ),
            error_type="invalid_input",
        )
        return {
            "status": "failed",
            "actions": [error],
            "summary": _summary_from_actions([error]),
            "dry_run": True,
        }

    # Generate a placeholder drive_file_id for dry-run
    placeholder_id = f"dry_run_{safe_path_part(title)}"
    raw_path = planned_raw_path(category, title, source_type, placeholder_id)

    action = _success_action(
        source_type=source_type,
        title=title,
        category=category,
        drive_file_id=placeholder_id,
        drive_url=drive_source_url(placeholder_id),
        source_id=drive_source_id(placeholder_id),
        raw_path=raw_path,
        rebuild_status="pending",
        message="Dry-run: would upload to Drive",
    )

    return {
        "status": "success",
        "actions": [action],
        "summary": _summary_from_actions([action]),
        "dry_run": True,
    }


def execute_apply(args: argparse.Namespace, folders: dict[str, str]) -> dict[str, Any]:
    """Execute the publish operation: Drive upload, raw save, DB upsert."""
    validation_errors = validate_input(args)
    if validation_errors:
        return {
            "status": _infer_status(validation_errors),
            "actions": validation_errors,
            "summary": _summary_from_actions(validation_errors),
            "dry_run": False,
        }

    category = args.category
    title = args.title or "untitled"
    body = args.body or ""
    source_type = infer_source_type(args)
    mime_type = infer_mime_type(source_type)

    folder_id = folders.get(category)
    if not folder_id:
        error = _error_action(
            source_type=source_type,
            title=title,
            message=(
                f"Category '{category}' not found in --folders-config. "
                f"Available: {', '.join(sorted(folders.keys()))}"
            ),
            error_type="invalid_input",
        )
        return {
            "status": "failed",
            "actions": [error],
            "summary": _summary_from_actions([error]),
            "dry_run": False,
        }

    db_path = args.db_path or DB_PATH
    root_path = args.root_path or ROOT
    token_path = args.token_path or DEFAULT_TOKEN_PATH

    # Resolve Drive file name with duplicate detection
    drive_file_name = resolve_drive_file_name(title, db_path, category)

    # Load credentials and build service — structured JSON on auth failure
    try:
        credentials = load_drive_credentials(token_path)
        service = build_drive_service(credentials)
    except (DriveAuthError, DriveApiError) as exc:
        error_type = "drive_auth_missing" if isinstance(exc, DriveAuthError) else "drive_write_failed"
        error = _error_action(
            source_type=source_type,
            title=title,
            message=str(exc),
            error_type=error_type,
        )
        return {
            "status": "failed",
            "actions": [error],
            "summary": _summary_from_actions([error]),
            "dry_run": False,
        }

    # Drive API: files.create
    file_metadata: dict[str, object] = {
        "name": drive_file_name,
        "mimeType": mime_type,
        "parents": [folder_id],
    }
    media = io.BytesIO(body.encode("utf-8"))
    request = service.files().create(
        body=file_metadata,
        media_body=media,
    )
    try:
        created_file: dict[str, object] = request.execute()
    except Exception as exc:
        error = _error_action(
            source_type=source_type,
            title=title,
            message=f"Drive write failed: {exc}",
            error_type="drive_write_failed",
        )
        return {
            "status": "failed",
            "actions": [error],
            "summary": _summary_from_actions([error]),
            "dry_run": False,
        }

    drive_file_id = str(created_file.get("id", ""))
    drive_url = str(created_file.get("webViewLink", drive_source_url(drive_file_id)))

    # Build source_id
    sid = drive_source_id(drive_file_id)

    # Save raw content locally
    raw_path = planned_raw_path(category, title, source_type, drive_file_id)
    raw_full_path = root_path / raw_path
    raw_full_path.parent.mkdir(parents=True, exist_ok=True)
    raw_full_path.write_text(body, encoding="utf-8")

    # Compute content hash
    hash_value = content_hash(body)

    # Upsert DB
    source_url = drive_source_url(drive_file_id)
    upsert_source(db_path, sid, source_type, title, source_url, raw_path, hash_value)

    action = _success_action(
        source_type=source_type,
        title=title,
        category=category,
        drive_file_id=drive_file_id,
        drive_url=drive_url,
        source_id=sid,
        raw_path=raw_path,
        rebuild_status="completed",
        message=f"Uploaded to Drive: {drive_file_name}",
    )

    return {
        "status": "success",
        "actions": [action],
        "summary": _summary_from_actions([action]),
        "dry_run": False,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Publish content to Google Drive FFXIV_KB."
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run OAuth browser flow for Drive write scope and save the token.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan changes without writing files, calling Drive API, or updating the database.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Upload content to Drive, save raw cache, and upsert the database.",
    )
    parser.add_argument(
        "--category",
        help="Drive FFXIV_KB category folder for the uploaded content.",
    )
    parser.add_argument(
        "--title",
        help="Title of the document (used as Drive file name).",
    )
    parser.add_argument(
        "--body",
        help="Text/markdown content body to publish.",
    )
    parser.add_argument(
        "--folders-config",
        type=Path,
        help="Path to YAML config file mapping categories to Drive folder IDs.",
    )
    parser.add_argument(
        "--credentials-path",
        type=Path,
        default=DEFAULT_CREDENTIALS_PATH,
        help="OAuth client secret JSON path for --auth.",
    )
    parser.add_argument(
        "--token-path",
        type=Path,
        default=DEFAULT_TOKEN_PATH,
        help="OAuth token JSON path.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help="Path to the SQLite database.",
    )
    parser.add_argument(
        "--source-type",
        default="text_note",
        choices=sorted(VALID_SOURCE_TYPES),
        help=f"Source content type. Choices: {', '.join(sorted(VALID_SOURCE_TYPES))} (default: text_note).",
    )
    parser.add_argument(
        "--root-path",
        type=Path,
        default=ROOT,
        help="Repository root path for raw/drive writes.",
    )

    args = parser.parse_args(argv)

    try:
        if args.auth:
            if args.dry_run or args.apply or args.dry_run is False:
                parser.error("--auth cannot be combined with --dry-run or --apply")
            result = run_drive_auth(args.credentials_path, args.token_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.dry_run and args.apply:
            parser.error("choose at most one of --dry-run or --apply")
        if not args.dry_run and not args.apply:
            parser.error("choose exactly one of --dry-run or --apply")

        if not args.folders_config:
            parser.error("--folders-config is required for --dry-run or --apply")
        if not args.category:
            parser.error("--category is required")
        if not args.title:
            parser.error("--title is required")

        # Load YAML config
        try:
            folders = load_folders_config(args.folders_config)
        except Exception as exc:
            parser.error(f"Failed to load --folders-config: {exc}")

        if args.dry_run:
            result = plan_dry_run(args, folders)
        else:
            result = execute_apply(args, folders)
    except (DriveAuthError, DriveApiError) as exc:
        parser.error(str(exc))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
