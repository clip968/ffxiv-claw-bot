# v0.3-01: Manifest 기반 Dry-run

## Spec

`docs/specs/0003-google-drive-sync.md`
- Manifest 기반 dry-run
- Manifest 형식
- Local raw path 규칙
- Drive 폴더 구조
- 변경 감지 기준
- JSON 출력 계약

## Status
## Checklist

- [x] manifest JSON schema 정의 (drive_file_id, source_url, title, category, contentFixture)
- [x] `sync_drive.py`에 `--dry-run` / `--manifest` CLI 플래그 추가
- [x] manifest fixture content를 메모리 로드해서 action 판별
- [x] `source_url = gdrive://<drive_file_id>` 기준 DB 조회 및 content_hash 비교
- [x] DB 미존재 = new, 존재 + hash 다름 = changed, 일치 = unchanged
- [x] dry-run 결과 출력 포맷 (new X, changed Y, unchanged Z, skipped W)
- [x] `--verbose` 플래그로 각 항목별 상세 출력 지원
- [x] unittest: manifest schema validation
- [x] unittest: new/changed/unchanged 분류
- [x] unittest: --dry-run은 raw 저장 안 함 검증

## Verification
```bash
python -m unittest tests.test_sync_drive
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```

## Key Decisions

- `drive_file_id`: 동일 문서 식별 기준
- `content_hash`: 최종 변경 판단 기준
- `modifiedTime`: 출력 metadata (분류 최종 기준 아님)
- skipped 조건: `id`, `name`, `category`, `exportExt`, `contentHash` 중 누락
