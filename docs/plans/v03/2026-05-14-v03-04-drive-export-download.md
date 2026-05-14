# v0.3-04: Google Docs Export / 파일 Download

## Spec

`docs/specs/0003-google-drive-sync.md`
- v0.3 manifest sync 범위 밖: Google Docs export/download

## Status

**Proposed**

## Context

## Checklist

- [ ] Google Docs export format 결정 (Markdown / HTML / plain text)
- [ ] Google Docs -> Markdown export 구현 (docs.export)
- [ ] Google Sheets: 우선 skip, 이후 필요 시 CSV 추가
- [ ] PDF/이미지: binary 저장 + 확장자 유지
- [ ] export/download 결과 SHA256 content_hash 계산
- [ ] `raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>` 저장
- [ ] 기존 `--apply` raw 저장/DB upsert 로직 재사용
- [ ] `sync_drive.py` 플래그 설계: `--download` vs `--from-drive` 통합
- [ ] content_hash 비교 -> new/changed/unchanged 분류
- [ ] unittest: Google Docs export mock test
- [ ] unittest: binary file download 저장 확인
- [ ] unittest: content_hash 계산 정확성

## Verification
```bash
# Drive API 조회 + 다운로드
python tools/sync_drive.py --from-drive --download

# 같은 실행 재시도 (idempotent 확인)
python tools/sync_drive.py --from-drive --download
```

실제 Drive API test는 기본 unittest에서 제외한다.

## Key Decisions (미결정)

- Google Docs export format (Markdown vs HTML)
- Sheets 처리 (skip 유지 vs CSV 변환)
- download CLI 설계 (별도 플래그 vs --from-drive 통합)
- 네트워크 오류/부분 실패 시 재시도 정책
