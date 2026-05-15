# v0.4 Legacy: Drive Integration

## Status

**Deferred / Optional Integration**

## Goal

v0.3 Drive sync와 v0.4-01 Drive write foundation을 삭제하지 않고 optional integration으로 문서화한다.

## Included Files

- `tools/sync_drive.py`
- `tools/publish_drive.py`
- `tests/test_sync_drive.py`
- `tests/test_publish_drive.py`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`
- `docs/specs/0003-google-drive-sync.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- `docs/adrs/0005-drive-write-scope-and-upload.md`
- `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md`
- `config/drive_folders.yaml` when configured locally

## Current Default Path

현재 기본 경로에서는 사용하지 않는다.

기본 source of truth는 `/mnt/d/ffixiv-bot-storage`다. Drive는 향후 cloud sync가 필요할 때 다시 활성화한다.

## Legacy Actions

- `upload_drive_file`
- `sync_drive`
- `drive_auth`
- `drive_download`
- `drive_export`

## Legacy Error Codes

- `drive_auth_missing`
- `drive_write_failed`

## Verification

Drive 테스트는 유지하되 기본 운영 경로 검증과 분리한다.

```bash
python -m unittest tests.test_sync_drive
python -m unittest tests.test_publish_drive
```

실제 Drive API smoke는 maintainer가 token/folder id를 승인한 환경에서만 실행한다.
