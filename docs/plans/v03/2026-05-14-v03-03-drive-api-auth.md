# v0.3-03: Google Drive API 인증 및 파일 목록 조회

## Spec

`docs/specs/0003-google-drive-sync.md`
- v0.3 manifest sync 범위 밖: 실제 OAuth, 실제 Google Drive API 호출

## Status
Completed

## Checklist

- [x] Google Cloud Console Drive API 활성화 절차 문서화
- [x] OAuth 2.0 Client ID (Desktop application) 생성 절차 문서화
- [x] `config/`에 client secret 저장 규칙 정의
- [x] `sync_drive.py`에 `--auth`, `--from-drive` 플래그 추가
- [x] 브라우저 인증 -> token.json 저장/refresh 구현
- [x] `drive.list_files(folder_id)` Drive API 호출 구현
- [x] FFXIV_KB 폴더 ID를 root로 지정
- [x] Drive file list를 manifest JSON 포맷으로 변환
- [x] 변환된 manifest를 기존 dry-run에서 재사용
- [x] OAuth token 만료/refresh 처리
- [x] unittest: OAuth token 없을 때 에러 메시지
- [x] unittest: Drive API response parsing
- [x] unittest: manifest 변환 결과 포맷 검증

## Verification
```bash
# OAuth 인증 + 파일 목록 조회 (실제 Drive 필요)
python tools/sync_drive.py --from-drive --dry-run

# 조회 결과를 manifest로 저장
python tools/sync_drive.py --from-drive --output-manifest /tmp/drive-manifest.json

# 저장된 manifest로 dry-run (Drive 재호출 없음)
python tools/sync_drive.py --dry-run --manifest /tmp/drive-manifest.json
```

Drive API live call은 기본 unittest에서 제외한다. 기본 unittest는 token missing error와 response parsing/manifest conversion만 검증한다.

## Key Decisions

- OAuth client secret 기본 위치: `config/google_drive_client_secret.json`
- OAuth token 기본 위치: `config/google_drive_token.json`
- folder id 관리 방식: v0.3-03에서는 `--drive-folder-id` 명시 입력
- CLI: 기존 `tools/sync_drive.py`에 `--auth`, `--from-drive` 플래그 추가
- API 응답 -> manifest JSON 변환 로직 위치: `tools/sync_drive.py`
- v0.3-03은 metadata list까지만 다룬다. Google Docs export/download는 v0.3-04 범위다.
