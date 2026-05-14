# ADR 0004: Dry-Run Before Real Drive API

## Status

Accepted

## Context

v0.3 Google Drive Sync 구현을 시작할 때, 실제 Google Drive API 연동은 OAuth 인증, API scope, credential 관리, 네트워크 의존성, 실제 파일 다운로드 등 여러 복잡한 요소가 한 번에 필요했다.

이 모든 요소를 한 번에 구현하면:
- 테스트가 네트워크와 외부 인증에 의존하게 된다.
- 실패 지점이 많아 디버깅이 어렵다.
- 작은 단위로 검증하고 커밋하기 어렵다.

## Decision

v0.3 구현의 첫 범위를 실제 Google API 연동 없이 manifest 기반 dry-run으로 고정한다.

선택한 접근:
1. Manifest JSON으로 Drive API 응답을 대체한다.
2. `sync_drive.py --dry-run`으로 동기화 계획(new/changed/unchanged/skipped)을 검증한다.
3. `raw/drive/<category>/...` 경로 규칙을 먼저 정한다.
4. `source_url = gdrive://<drive_file_id>` 식별 규칙을 정한다.
5. 모든 테스트는 네트워크와 외부 API 없이 실행 가능하다.
6. 그 다음 단계에서 manifest 기반 --apply로 local write를 먼저 구현한다.
7. 실제 Google Drive API/OAuth/export-download는 그 이후에 구현한다.

## Consequences

Good:
- CLI 계약과 JSON 입출력 포맷을 실제 API 전에 고정할 수 있다.
- 테스트가 빠르고 네트워크에 의존하지 않는다.
- Drive 인증 문제와 동기화 로직 문제를 분리할 수 있다.
- 실제 API 구현 전에 반복 재실행(idempotent)을 검증할 수 있다.

Tradeoff:
- manifest fixture가 실제 Drive API 응답 구조와 다를 수 있다.
- 실제 API 연동 시 manifest 기반 --dry-run 출력과 다른 결과가 나올 가능성이 있다.
- --apply와 실제 API 사이에 추가 조정 작업이 필요할 수 있다.
