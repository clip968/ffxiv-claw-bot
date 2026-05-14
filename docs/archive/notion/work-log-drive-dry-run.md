# 작업 로그 - 2026-05-14 - v0.3 Drive dry-run 시작 (Archive)

> Notion `작업 로그 - 2026-05-14 - v0.3 Drive dry-run 시작`에서 2026-05-14 가져옴.
> 현재 v0.3 Drive sync dry-run은 완료된 상태다. 과거 작업 로그 참고용으로 보관한다.

## 원본 출처

Notion URL: https://www.notion.so/35f4bf16ed1f81da83e9e6bfbaea6b87

## 요약

- tools/sync_drive.py 생성
- tests/test_sync_drive.py + tests/fixtures/drive_manifest.json 추가
- manifest 기반 --dry-run CLI: new/changed/unchanged/skipped 분류
- raw/drive/<category>/<safe_title>__<drive_file_id>.<ext> 경로 규칙
- 실제 Drive API, 파일 다운로드, DB write는 아직 미구현

검증: unittest 3/3 OK, --dry-run 정상 출력
