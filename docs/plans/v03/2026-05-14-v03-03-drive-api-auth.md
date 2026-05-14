# v0.3-03: Google Drive API 인증 및 파일 목록 조회

## Spec

`docs/specs/0003-google-drive-sync.md`
- v0.3 manifest sync 범위 밖: 실제 OAuth, 실제 Google Drive API 호출

## Status
## Checklist

- [ ] Google Cloud Console Drive API 활성화
- [ ] OAuth 2.0 Client ID (Desktop application) 생성
- [ ] `config/`에 client secret 저장 규칙 정의
- [ ] `sync_drive.py`에 `--auth`, `--from-drive` 플래그 추가
- [ ] 브라우저 인증 -> token.json 저장/refresh 구현
- [ ] `drive.list_files(folder_id)` Drive API 호출 구현
- [ ] FFXIV_KB 폴더 ID를 root로 지정
- [ ] Drive file list를 manifest JSON 포맷으로 변환
- [ ] 변환된 manifest를 기존 dry-run/apply에서 재사용
- [ ] OAuth token 만료/refresh 처리
- [ ] unittest: OAuth token 없을 때 에러 메시지
- [ ] unittest: Drive API response parsing
- [ ] unittest: manifest 변환 결과 포맷 검증

## Verification
```bash
# OAuth 인증 + 파일 목록 조회 (실제 Drive 필요)
python tools/sync_drive.py --from-drive --dry-run

# 조회 결과를 manifest로 저장
python tools/sync_drive.py --from-drive --output-manifest /tmp/drive-manifest.json

# 저장된 manifest로 dry-run (Drive 재호출 없음)
python tools/sync_drive.py --dry-run --manifest /tmp/drive-manifest.json
```

Drive API test는 기본 unittest에서 제외하고, integration test로 분리한다.

## Key Decisions (미결정)

- OAuth token 저장 위치
- folder id 관리 방식 (검색 vs 고정)
- `--from-drive` 플래그 vs 별도 CLI
- API 응답 -> manifest JSON 변환 로직 위치
