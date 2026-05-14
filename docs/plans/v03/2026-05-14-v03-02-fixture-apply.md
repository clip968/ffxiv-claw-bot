# v0.3-02: Manifest 기반 Fixture Apply

## Spec

`docs/specs/0003-google-drive-sync.md`
- Manifest 기반 apply
- Idempotent 재실행 원칙

## Status
## Checklist

- [x] `sync_drive.py`에 `--apply` / `--dry-run` 선택 CLI 플래그 추가
- [x] fixture content를 `raw/drive/<category>/<safe_title>__<drive_file_id>.md`에 저장
- [x] `sources.source_type = drive_document`로 DB upsert
- [x] `source_url = gdrive://<drive_file_id>` 기준 idempotent 갱신
- [x] content_hash 같으면 raw 파일 overwrite 없음 (unchanged)
- [x] 같은 manifest 재실행 시 new 3 -> unchanged 3 (idempotent)
- [x] `--apply` 없는 dry-run은 raw 저장/DB upsert 없음
- [x] unittest: apply 시 raw 파일 생성 확인
- [x] unittest: DB upsert 확인
- [x] unittest: 재실행 idempotent 확인
- [x] unittest: 기존 dry-run test 유지

## Verification
```bash
python -m unittest tests.test_sync_drive            # apply tests 포함
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json
# 재실행 idempotent 확인
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json
# dry-run 유지 확인
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```

## Key Decisions

- `contentFixture`: manifest item에 fixture content 파일 경로 추가
- source id: `drive_<safe_drive_file_id>` (deterministic)
- `--root-path`: `raw/drive`를 쓸 repo root (기본값: repo root)
- skipped 조건: contentFixture가 없는 new/changed item도 apply에서 skipped
