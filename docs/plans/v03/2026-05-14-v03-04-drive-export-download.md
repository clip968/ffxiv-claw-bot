# v0.3-04: Google Docs Export / 파일 Download

## Spec

`docs/specs/0003-google-drive-sync.md`
- v0.3 Google Drive sync: Google Docs export/download

## Status

**Completed**

## Context

Drive metadata listing만으로는 raw cache와 DB `content_hash`를 실제 문서 내용 기준으로 갱신할 수 없다.
이 단계에서는 `--from-drive --download`를 추가해 Google Drive에서 content bytes를 가져오고 SHA256을 계산한 뒤 기존 plan/apply 흐름을 재사용한다.

## Checklist

- [x] Google Docs export format 결정: Markdown (`text/markdown`, `.md`)
- [x] Google Docs -> Markdown export 구현 (`files.export_media`)
- [x] Google Sheets: 우선 skip, 이후 필요 시 CSV 추가
- [x] PDF/이미지: binary 저장 + 확장자 유지
- [x] export/download 결과 SHA256 content_hash 계산
- [x] `raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>` 저장
- [x] 기존 `--apply` raw 저장/DB upsert 로직 재사용
- [x] `sync_drive.py` 플래그 설계: `--from-drive --download` + optional `--dry-run`/`--apply`
- [x] content_hash 비교 -> new/changed/unchanged 분류
- [x] unittest: Google Docs export mock test
- [x] unittest: binary file download 저장 확인
- [x] unittest: content_hash 계산 정확성

## Verification
```bash
# Drive API 조회 + 다운로드 manifest 출력
python tools/sync_drive.py --from-drive --download --drive-folder-id <FFXIV_KB_FOLDER_ID>

# Drive API 조회 + 다운로드 + raw/DB 적용
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID>

# 같은 실행 재시도 (idempotent 확인)
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

실제 Drive API test는 기본 unittest에서 제외한다.

## Key Decisions

- Google Docs export format은 Markdown (`text/markdown`)으로 고정한다.
- Google Sheets는 v0.3-04에서 skip한다. CSV 변환은 실제 필요가 확인되면 별도 plan으로 추가한다.
- download는 `--from-drive --download`로 metadata 조회와 결합한다. 로컬 쓰기는 `--apply`가 있을 때만 수행한다.
- 네트워크 오류/부분 실패 재시도 정책은 별도 retry 없이 Drive API 오류를 surfaced error로 둔다.
