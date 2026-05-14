# Publish Drive Runbook

## 원칙

`tools/publish_drive.py`는 로컬에서 받은 Discord note, text, attachment 등을
Google Drive `FFXIV_KB` 폴더 구조에 **쓰기** 위한 도구다.

`tools/sync_drive.py`가 Drive -> local read 전담인 반면,
`publish_drive.py`는 local/OpenClaw -> Drive write 전담이다.

기존 read-only Drive token(`drive.readonly`)과 별도로 `drive` (full) scope token을
`config/google_drive_token_write.json`에 저장한다.

## OAuth 인증

첫 실행 전에 `--auth`로 Drive write용 token을 발급받는다.

```bash
python tools/publish_drive.py --auth
```

기본 경로와 다른 credentials 파일을 쓰려면:

```bash
python tools/publish_drive.py --auth \
  --credentials-path /path/to/client_secret.json \
  --token-path /path/to/token.json
```

`--auth`는 `drive` (full) scope를 요청하므로,
기존 read-only token과는 별도 경로에 저장해야 한다.

## Category Folder ID 설정

`config/drive_folders.yaml`에 category별 Drive folder ID를 등록한다.

```yaml
patch_notes: "1a2b3c4d5e6f7g8h9i0j"
job_guides: "2b3c4d5e6f7g8h9i0j1a"
raid_guides: "3c4d5e6f7g8h9i0j1a2b"
static_docs: "4c4d5e6f7g8h9i0j1a2b"
macros: "5c4d5e6f7g8h9i0j1a2b"
bis_sheets: "6c4d5e6f7g8h9i0j1a2b"
personal_notes: "7c4d5e6f7g8h9i0j1a2b"
```

## Dry-run (계획만 확인)

```bash
python tools/publish_drive.py \
  --dry-run \
  --category patch_notes \
  --title "7.5 Patch Notes" \
  --body "# Patch 7.5\n\nJob adjustments." \
  --folders-config config/drive_folders.yaml
```

출력 JSON:

```json
{
  "status": "success",
  "actions": [
    {
      "action": "drive_upload",
      "source_type": "text_note",
      "title": "7.5 Patch Notes",
      "category": "patch_notes",
      "raw_path": "raw/drive/patch_notes/7.5_patch_notes__<drive_file_id>.md",
      "rebuild_status": "pending",
      "message": "Dry-run: would upload to Drive"
    }
  ],
  "summary": { "total": 1, "uploaded": 1, "updated": 0, "skipped": 0, "errors": 0 },
  "dry_run": true
}
```

## Apply (실제 Drive 업로드)

```bash
python tools/publish_drive.py \
  --apply \
  --category patch_notes \
  --title "7.5 Patch Notes" \
  --body "# Patch 7.5\n\nJob adjustments." \
  --folders-config config/drive_folders.yaml
```

동작:
1. `--folders-config`에서 category에 맞는 Drive folder ID 조회
2. Drive API `files.create`로 지정한 folder에 `.md` 파일 업로드
3. 로컬 `raw/drive/<category>/<safe_title>__<drive_file_id>.md`에 body 저장
4. `db/ffxiv.sqlite` `sources` 테이블에 upsert
5. `rebuild_status: "completed"`으로 결과 반환 (v04-04에서 rebuild 연결 시 갱신)

## 중복 처리

같은 title + 같은 category의 source가 DB에 이미 존재하면
Drive 파일명에 timestamp를 append한다.

- `"My Note"` -> `"My Note__2026-05-14"`
- `"My Note__2026-05-14" -> "My Note__2026-05-14__2026-05-14"` (중첩 가능)

## 출력 형식

v04-00 ingest contract에 정의된 JSON 형식:

```json
{
  "status": "success | partial | failed",
  "actions": [{ "action", "source_type", "title", "category",
                "drive_file_id", "drive_url", "source_id",
                "raw_path", "rebuild_status", "message" }],
  "summary": { "total": 1, "uploaded": 1, "updated": 0, "skipped": 0, "errors": 0 },
  "dry_run": true | false
}
```

## 테스트 (실제 API 없이)

```bash
python -m unittest tests.test_publish_drive
```

FakeDriveService로 Drive API 호출을 모킹하므로
실제 token이나 네트워크 없이 실행 가능하다.


## 현재 한계 (v0.4-01)

- `--source-type` 지원 범위는 `text_note`, `markdown_file`, `plain_text_file` 세 가지다 (`url`, `binary_attachment` 미지원)
- Google Docs convert 지원 안 함 (원본 `.md`/`.txt` file upload만)
- 기존 Drive file overwrite/update 안 함 (항상 새 파일 생성, timestamp append)
- `drive` (full) scope 필요 (read-only token으로는 publish 불가)
- 다중 action 배치 처리 미지원 (추후 추가 예정)
- Binary attachment upload 미지원
