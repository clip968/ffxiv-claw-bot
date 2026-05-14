from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
DEFAULT_CREDENTIALS_PATH = ROOT / "config" / "google_drive_client_secret.json"
DEFAULT_TOKEN_PATH = ROOT / "config" / "google_drive_token.json"

DRIVE_SOURCE_PREFIX = "gdrive://"
DRY_RUN_ACTIONS = ("new", "changed", "unchanged", "skipped")
GOOGLE_DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_APPS_MIME_PREFIX = "application/vnd.google-apps."
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_DOC_EXPORT_MIME = "text/markdown"
GOOGLE_DRIVE_SCOPES = ("https://www.googleapis.com/auth/drive.readonly",)
GOOGLE_MIME_EXPORT_EXTENSIONS = {
    GOOGLE_DOC_MIME: "md",
    "text/plain": "txt",
    "text/markdown": "md",
}
DOWNLOAD_MIME_EXTENSIONS = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "text/plain": "txt",
    "text/markdown": "md",
}

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
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9가-힣._-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("._")
    return normalized or "untitled"


def planned_raw_path(item: dict[str, Any]) -> str:
    file_id = str(item["id"])
    title = str(item["name"])
    category = str(item["category"])
    extension = str(item["exportExt"]).lstrip(".")

    filename = f"{safe_path_part(title)}__{safe_path_part(file_id)}.{extension}"
    return f"raw/drive/{safe_path_part(category)}/{filename}"


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def drive_source_url(drive_file_id: str) -> str:
    return f"{DRIVE_SOURCE_PREFIX}{drive_file_id}"


def drive_source_id(drive_file_id: str) -> str:
    return f"drive_{safe_path_part(drive_file_id)}"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_sources_table(conn: sqlite3.Connection) -> None:
    conn.execute(SOURCES_SCHEMA)


def load_existing_drive_sources(db_path: Path) -> dict[str, dict[str, Any]]:
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT id, title, source_url, raw_path, content_hash
                  FROM sources
                 WHERE source_type = ?
                   AND source_url LIKE ?
                """,
                ("drive_document", f"{DRIVE_SOURCE_PREFIX}%"),
            ).fetchall()
        except sqlite3.OperationalError:
            return {}
    finally:
        conn.close()

    existing: dict[str, dict[str, Any]] = {}
    for row in rows:
        source_url = row["source_url"]
        drive_file_id = source_url.removeprefix(DRIVE_SOURCE_PREFIX)
        existing[drive_file_id] = dict(row)

    return existing


def classify_item(item: dict[str, Any], existing_sources: dict[str, dict[str, Any]]) -> str:
    required_fields = ("id", "name", "category", "exportExt", "contentHash")
    if any(not item.get(field) for field in required_fields):
        return "skipped"

    existing = existing_sources.get(str(item["id"]))
    if not existing:
        return "new"

    if existing["content_hash"] == item["contentHash"]:
        return "unchanged"

    return "changed"


def build_plan_item(
    item: dict[str, Any],
    existing_sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action = classify_item(item, existing_sources)
    planned_path = planned_raw_path(item) if action != "skipped" else None

    result = {
        "drive_file_id": item.get("id"),
        "title": item.get("name"),
        "category": item.get("category"),
        "mime_type": item.get("mimeType"),
        "modified_time": item.get("modifiedTime"),
        "source_url": item.get("webViewLink") or drive_source_url(str(item.get("id"))),
        "action": action,
        "planned_raw_path": planned_path,
    }

    if action == "skipped":
        result["reason"] = item.get("skipReason") or "missing required dry-run metadata"

    return result


def plan_sync(manifest_path: Path, db_path: Path = DB_PATH) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    existing_sources = load_existing_drive_sources(db_path)
    items = [
        build_plan_item(item, existing_sources)
        for item in manifest.get("files", [])
    ]

    summary = {action: 0 for action in DRY_RUN_ACTIONS}
    for item in items:
        summary[item["action"]] += 1

    return {
        "status": "ok",
        "dry_run": True,
        "root_folder": manifest.get("root_folder"),
        "summary": summary,
        "items": items,
    }


def export_extension_for_mime(mime_type: str | None) -> str | None:
    if not mime_type:
        return None
    return GOOGLE_MIME_EXPORT_EXTENSIONS.get(mime_type)


def file_name_extension(file_name: str | None) -> str | None:
    if not file_name:
        return None
    extension = Path(file_name).suffix.lower().lstrip(".")
    return extension or None


def download_extension_for_drive_file(file_item: dict[str, Any]) -> str | None:
    mime_type = file_item.get("mimeType")
    export_ext = export_extension_for_mime(str(mime_type) if mime_type else None)
    if export_ext:
        return export_ext

    if mime_type and str(mime_type).startswith(GOOGLE_APPS_MIME_PREFIX):
        return None

    name_ext = file_name_extension(str(file_item.get("name") or ""))
    if name_ext:
        return name_ext

    if not mime_type:
        return None
    return DOWNLOAD_MIME_EXTENSIONS.get(str(mime_type))


def content_hash_for_drive_file(file_item: dict[str, Any]) -> str | None:
    for field in ("md5Checksum", "headRevisionId", "modifiedTime"):
        value = file_item.get(field)
        if value:
            return str(value)
    return None


def category_for_drive_file(
    file_item: dict[str, Any],
    category_by_folder_id: dict[str, str],
) -> str:
    for parent_id in file_item.get("parents", []):
        category = category_by_folder_id.get(str(parent_id))
        if category:
            return category
    return "uncategorized"


def drive_files_to_manifest(
    files: list[dict[str, Any]],
    root_folder: str,
    category_by_folder_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    categories = category_by_folder_id or {}
    manifest_files: list[dict[str, Any]] = []

    for file_item in files:
        mime_type = file_item.get("mimeType")
        if mime_type == GOOGLE_DRIVE_FOLDER_MIME:
            continue

        manifest_item = {
            "id": file_item.get("id"),
            "name": file_item.get("name"),
            "category": category_for_drive_file(file_item, categories),
            "mimeType": mime_type,
            "modifiedTime": file_item.get("modifiedTime"),
            "webViewLink": file_item.get("webViewLink"),
        }

        export_ext = download_extension_for_drive_file(file_item)
        if export_ext:
            manifest_item["exportExt"] = export_ext

        content_hash = content_hash_for_drive_file(file_item)
        if content_hash:
            manifest_item["contentHash"] = content_hash

        manifest_files.append(manifest_item)

    return {
        "root_folder": root_folder,
        "files": manifest_files,
    }


def load_drive_credentials(token_path: Path) -> Any:
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
        scopes=list(GOOGLE_DRIVE_SCOPES),
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


def run_drive_auth(credentials_path: Path, token_path: Path) -> dict[str, Any]:
    if not credentials_path.exists():
        raise DriveAuthError(f"OAuth client secret not found: {credentials_path}")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ModuleNotFoundError as exc:
        raise DriveAuthError(
            "Google OAuth dependency is not installed. "
            "Install google-auth-oauthlib."
        ) from exc

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        scopes=list(GOOGLE_DRIVE_SCOPES),
    )
    credentials = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return {
        "status": "ok",
        "auth": True,
        "token_path": str(token_path),
    }


def build_drive_service(credentials: Any) -> Any:
    try:
        from googleapiclient.discovery import build
    except ModuleNotFoundError as exc:
        raise DriveApiError(
            "Google API client dependency is not installed. "
            "Install google-api-python-client."
        ) from exc
    return build("drive", "v3", credentials=credentials)


def list_drive_files(service: Any, folder_id: str) -> list[dict[str, Any]]:
    query = f"'{folder_id}' in parents and trashed = false"
    fields = (
        "nextPageToken, files("
        "id,name,mimeType,modifiedTime,webViewLink,parents,md5Checksum,headRevisionId"
        ")"
    )
    files: list[dict[str, Any]] = []
    page_token = None

    while True:
        request = service.files().list(
            q=query,
            fields=fields,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        response = request.execute()
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return files


def manifest_from_drive(
    folder_id: str,
    token_path: Path = DEFAULT_TOKEN_PATH,
    root_folder: str = "FFXIV_KB",
) -> dict[str, Any]:
    credentials = load_drive_credentials(token_path)
    service = build_drive_service(credentials)
    files = list_drive_files(service, folder_id)
    category_by_folder_id = {
        str(file_item["id"]): str(file_item["name"])
        for file_item in files
        if file_item.get("mimeType") == GOOGLE_DRIVE_FOLDER_MIME
    }
    return drive_files_to_manifest(files, root_folder, category_by_folder_id)


def export_mime_for_drive_file(file_item: dict[str, Any]) -> str | None:
    if file_item.get("mimeType") == GOOGLE_DOC_MIME:
        return GOOGLE_DOC_EXPORT_MIME
    return None


def execute_drive_content_request(request: Any) -> bytes:
    response = request.execute()
    if isinstance(response, bytes):
        return response
    if isinstance(response, str):
        return response.encode("utf-8")
    raise DriveApiError("Drive download returned unsupported content type")


def download_drive_file_content(service: Any, item: dict[str, Any]) -> bytes:
    file_id = str(item["id"])
    export_mime = export_mime_for_drive_file(item)
    if export_mime:
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=file_id)
    return execute_drive_content_request(request)


def download_drive_contents(
    service: Any,
    manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    downloaded_files: list[dict[str, Any]] = []
    content_by_file_id: dict[str, bytes] = {}

    for item in manifest.get("files", []):
        downloaded_item = dict(item)
        file_id = downloaded_item.get("id")
        export_ext = download_extension_for_drive_file(downloaded_item)

        if not file_id:
            downloaded_item["skipReason"] = "missing drive file id"
            downloaded_files.append(downloaded_item)
            continue
        if not export_ext:
            downloaded_item["skipReason"] = "unsupported download mime type"
            downloaded_item.pop("contentHash", None)
            downloaded_files.append(downloaded_item)
            continue

        downloaded_item["exportExt"] = export_ext
        content = download_drive_file_content(service, downloaded_item)
        content_by_file_id[str(file_id)] = content
        downloaded_item["contentHash"] = hashlib.sha256(content).hexdigest()
        downloaded_files.append(downloaded_item)

    downloaded_manifest = dict(manifest)
    downloaded_manifest["files"] = downloaded_files
    return downloaded_manifest, content_by_file_id


def resolve_content_fixture(manifest_path: Path, item: dict[str, Any]) -> Path | None:
    fixture = item.get("contentFixture")
    if not fixture:
        return None

    fixture_path = Path(str(fixture))
    if fixture_path.is_absolute():
        return fixture_path

    repo_relative = ROOT / fixture_path
    if repo_relative.exists():
        return repo_relative

    return manifest_path.parent / fixture_path


def write_raw_file(root_path: Path, relative_raw_path: str, content: str | bytes) -> None:
    raw_path = root_path / relative_raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        raw_path.write_bytes(content)
    else:
        raw_path.write_text(content, encoding="utf-8")


def upsert_drive_source(
    db_path: Path,
    item: dict[str, Any],
    relative_raw_path: str,
    existing_source: dict[str, Any] | None,
) -> None:
    now = utc_now()
    source_url = drive_source_url(str(item["id"]))

    conn = sqlite3.connect(db_path)
    try:
        ensure_sources_table(conn)
        if existing_source:
            conn.execute(
                """
                UPDATE sources
                   SET title = ?,
                       source_url = ?,
                       raw_path = ?,
                       content_hash = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    item["name"],
                    source_url,
                    relative_raw_path,
                    item["contentHash"],
                    now,
                    existing_source["id"],
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO sources (
                  id,
                  source_type,
                  title,
                  source_url,
                  raw_path,
                  content_hash,
                  created_at,
                  updated_at
                )
                VALUES (?, 'drive_document', ?, ?, ?, ?, ?, ?)
                """,
                (
                    drive_source_id(str(item["id"])),
                    item["name"],
                    source_url,
                    relative_raw_path,
                    item["contentHash"],
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def apply_sync_manifest(
    manifest: dict[str, Any],
    db_path: Path = DB_PATH,
    root_path: Path = ROOT,
    *,
    manifest_path: Path | None = None,
    content_by_file_id: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    existing_sources = load_existing_drive_sources(db_path)
    items: list[dict[str, Any]] = []

    for item in manifest.get("files", []):
        plan_item = build_plan_item(item, existing_sources)
        action = plan_item["action"]

        if action in ("new", "changed"):
            content: str | bytes | None = None
            if content_by_file_id is not None:
                content = content_by_file_id.get(str(item["id"]))
            elif manifest_path is not None:
                content_fixture = resolve_content_fixture(manifest_path, item)
                if content_fixture is not None and content_fixture.exists():
                    content = content_fixture.read_bytes()

            if content is None:
                plan_item["action"] = "skipped"
                plan_item["planned_raw_path"] = None
                plan_item["reason"] = (
                    "missing downloaded content"
                    if content_by_file_id is not None
                    else "missing content fixture"
                )
            else:
                relative_raw_path = str(plan_item["planned_raw_path"])
                write_raw_file(root_path, relative_raw_path, content)
                upsert_drive_source(
                    db_path,
                    item,
                    relative_raw_path,
                    existing_sources.get(str(item["id"])),
                )

        items.append(plan_item)

    summary = {action: 0 for action in DRY_RUN_ACTIONS}
    for item in items:
        summary[item["action"]] += 1

    return {
        "status": "ok",
        "dry_run": False,
        "root_folder": manifest.get("root_folder"),
        "summary": summary,
        "items": items,
    }


def apply_sync(
    manifest_path: Path,
    db_path: Path = DB_PATH,
    root_path: Path = ROOT,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    return apply_sync_manifest(
        manifest,
        db_path,
        root_path,
        manifest_path=manifest_path,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Plan Google Drive sync for FFXIV knowledge base."
    )
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Run OAuth browser flow and write the token file.",
    )
    parser.add_argument(
        "--from-drive",
        action="store_true",
        help="Fetch Drive file metadata and convert it to a manifest.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan changes without writing files or updating the database.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write manifest fixture content and upsert Drive source records.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download Drive content when using --from-drive.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to a local Drive manifest JSON file.",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        help="Write the Drive file list as a manifest JSON file.",
    )
    parser.add_argument(
        "--drive-folder-id",
        help="Google Drive folder id to list when using --from-drive.",
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
        help="OAuth token JSON path for --auth or --from-drive.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help="Path to the SQLite database.",
    )
    parser.add_argument(
        "--root-path",
        type=Path,
        default=ROOT,
        help="Repository root used for raw/drive writes.",
    )

    args = parser.parse_args(argv)

    try:
        if args.auth:
            if (
                args.from_drive
                or args.dry_run
                or args.apply
                or args.download
                or args.output_manifest
            ):
                parser.error("--auth cannot be combined with sync actions")
            result = run_drive_auth(args.credentials_path, args.token_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.from_drive:
            if not args.drive_folder_id:
                parser.error("--from-drive requires --drive-folder-id")
            if args.dry_run and args.apply:
                parser.error("choose at most one of --dry-run or --apply with --from-drive")
            if args.apply and not args.download:
                parser.error("--from-drive --apply requires --download")

            credentials = load_drive_credentials(args.token_path)
            service = build_drive_service(credentials)
            files = list_drive_files(service, args.drive_folder_id)
            category_by_folder_id = {
                str(file_item["id"]): str(file_item["name"])
                for file_item in files
                if file_item.get("mimeType") == GOOGLE_DRIVE_FOLDER_MIME
            }
            manifest = drive_files_to_manifest(
                files,
                "FFXIV_KB",
                category_by_folder_id,
            )
            content_by_file_id: dict[str, bytes] | None = None
            if args.download:
                manifest, content_by_file_id = download_drive_contents(service, manifest)

            if args.output_manifest:
                write_manifest(manifest, args.output_manifest)

            if args.apply:
                result = apply_sync_manifest(
                    manifest,
                    args.db_path,
                    args.root_path,
                    content_by_file_id=content_by_file_id,
                )
            elif args.dry_run:
                existing_sources = load_existing_drive_sources(args.db_path)
                items = [
                    build_plan_item(item, existing_sources)
                    for item in manifest.get("files", [])
                ]
                summary = {action: 0 for action in DRY_RUN_ACTIONS}
                for item in items:
                    summary[item["action"]] += 1
                result = {
                    "status": "ok",
                    "dry_run": True,
                    "root_folder": manifest.get("root_folder"),
                    "summary": summary,
                    "items": items,
                }
            else:
                result = {
                    "status": "ok",
                    "dry_run": None,
                    "root_folder": manifest.get("root_folder"),
                    "files": manifest.get("files", []),
                }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if args.download:
            parser.error("--download requires --from-drive")
        if args.dry_run == args.apply:
            parser.error("choose exactly one of --dry-run or --apply")
        if not args.manifest:
            parser.error("--manifest is required unless --from-drive or --auth is used")

        if args.dry_run:
            result = plan_sync(args.manifest, args.db_path)
        else:
            result = apply_sync(args.manifest, args.db_path, args.root_path)
    except (DriveAuthError, DriveApiError) as exc:
        parser.error(str(exc))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
