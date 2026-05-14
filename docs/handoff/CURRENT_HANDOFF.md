# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.3 Google Docs export/download 완료.

완료된 것:
- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run (manifest 기반, 실제 Drive API 없음)
- v0.3 Google Drive sync fixture apply (`--apply`, raw/drive 저장 + DB upsert, 실제 Drive API 없음)
- v0.3 Google Drive API 인증/파일 목록 조회 (`--auth`, `--from-drive`, metadata -> manifest 변환)
- v0.3 Google Docs export/download (`--from-drive --download`, Markdown export, binary download, SHA256 content hash, `--apply` 연결)
- docs-first workflow tooling (DOC_OWNERS, finish_task, check_docs_freshness 등)
- **Notion 문서 repo docs 이관 완료** (이번 세션, 2026-05-14)

미구현:
- Drive 변경 감지 후 wiki/FTS/graph 재빌드 연결
- Discord/OpenClaw 연결
- OpenClaw/Discord 저장 요청 -> Google Drive 업로드/생성
- 패치노트 자동 수집
- embedding/vector DB

## Notion 문서 이관 완료

Notion에 있던 모든 프로젝트 문서를 repo `docs/`로 이관했다.
Notion은 더 이상 source of truth가 아니다. repo `docs/`가 유일한 source of truth다.

Notion 문서 매핑:

| Notion | Local path |
|---|---|
| CURRENT_HANDOFF | `docs/handoff/CURRENT_HANDOFF.md` |
| SPEC - v0.3 Google Drive Sync | `docs/specs/0003-google-drive-sync.md` |
| ROADMAP | `docs/plans/2026-05-14-post-v03-next-steps.md` |
| DECISION_LOG | `docs/adrs/0001-0004` |
| AI_CONTEXT | `docs/PROJECT_PROFILE.md` |
| FILE_INVENTORY | `docs/FILE_INVENTORY.md` |
| 초기 ffxiv bot 설계 | `docs/archive/notion/initial-design.md` |
| 오래된 핸드오프/작업 로그 | `docs/archive/notion/*.md` |

## 다음 agent가 먼저 읽을 문서

1. `docs/WORKFLOW.md`
2. `docs/handoff/CURRENT_HANDOFF.md`
3. `docs/PROJECT_PROFILE.md`
4. `docs/FILE_INVENTORY.md`
5. `docs/specs/0003-google-drive-sync.md`
6. `docs/plans/2026-05-14-post-v03-next-steps.md` (v0.3 master plan)
7. `docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md`
8. `docs/plans/v03/2026-05-14-v03-01-manifest-dry-run.md`
9. `docs/plans/v03/2026-05-14-v03-02-fixture-apply.md`
10. `docs/plans/v03/2026-05-14-v03-04-drive-export-download.md`
11. `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` (다음 구현 1순위)
12. `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

## 이번 세션 완료: manifest 기반 --apply

`docs/plans/v03/2026-05-14-v03-02-fixture-apply.md` 참조.

완료된 하위 작업:
1. `sync_drive.py`에 `--apply` 플래그 추가
2. fixture content를 `raw/drive/<category>/...`에 저장
3. `sources.source_type = drive_document`로 DB upsert
4. `source_url = gdrive://<drive_file_id>` + `content_hash` 기준 idempotent 갱신
5. 같은 manifest 재실행 시 idempotent 동작 검증
6. 기존 `--dry-run` 동작 유지
7. `--apply` 전용 unittest 추가
8. 기존 dry-run test가 --apply 추가 후에도 정상 동작하는지 확인

이 단계는 여전히 실제 Google Drive API/OAuth/export-download를 구현하지 않는다.
fixture 기반 local apply만 다룬다.

## 이번 세션 완료: Drive API 인증/조회 설계

`docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md` 참조.

완료된 하위 작업:
1. OAuth credential 위치와 token 저장 위치 결정
2. 필요한 Google API scope 문서화
3. `FFXIV_KB` folder id는 `--drive-folder-id`로 명시 입력
4. `--auth`, `--from-drive`, `--output-manifest` CLI 추가
5. Drive file metadata를 기존 manifest JSON 포맷으로 변환
6. token 없음, Drive response parsing, manifest conversion unittest 추가

이 단계는 아직 Google Docs export/download를 구현하지 않는다.
content hash는 API metadata의 `md5Checksum`, `headRevisionId`, `modifiedTime` 순서로 사용한다.

## 이번 세션 완료: Google Docs export/download

`docs/plans/v03/2026-05-14-v03-04-drive-export-download.md` 참조.

완료된 하위 작업:
1. `sync_drive.py`에 `--download` 플래그 추가
2. `--from-drive --download`에서 Google Docs를 `text/markdown`으로 export
3. PDF/이미지/text 계열 일반 Drive file은 binary download
4. Google Sheets는 v0.3-04에서 `skipped` 처리
5. export/download bytes의 SHA256 hex digest를 `contentHash`와 DB `content_hash`로 사용
6. `--from-drive --download --apply`가 기존 raw 저장/DB upsert 흐름을 재사용
7. `--from-drive --apply` 단독 실행은 `--download` 필요 parser error 반환
8. Google Docs export, binary download, Sheets skip, CLI apply unittest 추가
9. Windows test temp DB 잠금 방지를 위해 SQLite 연결을 명시적으로 close

## 다음 구현 후보 1순위: Drive rebuild chain

`docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` 참조.

## 이번 세션 계획 수립: v0.4 OpenClaw Drive ingest

`docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`와 `docs/plans/v04/` 참조.

추가한 v0.4 feature plan:
1. `v04-00-openclaw-ingest-contract`: OpenClaw/Discord ingest request/result 계약
2. `v04-01-drive-write-foundation`: Drive write/upload 기반
3. `v04-02-ingest-discord-note-cli`: Discord note ingest CLI
4. `v04-03-openclaw-tool-adapter`: OpenClaw 설정/tool adapter
5. `v04-04-publish-then-rebuild`: Drive publish 후 sync/rebuild 연결
6. `v04-05-discord-summary-notification`: Discord 저장 결과/부분 실패 알림

embedding/vector DB는 필요성이 확인될 때까지 보류.

## 건드리지 말아야 할 것

명시 요청 없이는 다음을 건드리지 않는다:

- `tools/` 구현 코드
- `tests/` 코드
- `config/`
- `raw/`
- `wiki/`
- `graph/`
- `db/`
- `db/ffxiv.sqlite`
- Discord/OpenClaw 연결
- embedding/vector DB
- 기존 사용자 변경

## 테스트 명령

```bash
python scripts/finish_task.py
```

특정 unittest만:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

이번 세션에서 확인한 명령:

```bash
python -m unittest tests.test_sync_drive
python -m unittest discover -s tests -p "test_*.py"
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --db-path /tmp/ffxiv-claw-bot-apply-smoke.sqlite --root-path /tmp/ffxiv-claw-bot-apply-smoke
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --db-path /tmp/ffxiv-claw-bot-apply-smoke.sqlite --root-path /tmp/ffxiv-claw-bot-apply-smoke
python scripts/finish_task.py
```

이번 v0.3-03 세션에서 확인한 명령:

```bash
python -m unittest tests.test_sync_drive
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python tools/sync_drive.py --from-drive --dry-run --drive-folder-id folder_root --token-path /tmp/ffxiv-missing-token.json  # expected parser error: OAuth token not found
```

이번 v0.3-04 세션에서 확인한 명령:

```bash
python -m unittest tests.test_sync_drive
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --db-path C:\Users\clip9\AppData\Local\Temp\ffxiv-claw-bot-v03-04-smoke.sqlite --root-path C:\Users\clip9\AppData\Local\Temp\ffxiv-claw-bot-v03-04-smoke
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --db-path C:\Users\clip9\AppData\Local\Temp\ffxiv-claw-bot-v03-04-smoke.sqlite --root-path C:\Users\clip9\AppData\Local\Temp\ffxiv-claw-bot-v03-04-smoke
python tools/sync_drive.py --download --manifest tests/fixtures/drive_manifest.json  # expected parser error: --download requires --from-drive
python tools/sync_drive.py --from-drive --apply --drive-folder-id folder_root --token-path D:\tmp\ffxiv-missing-token.json  # expected parser error: --from-drive --apply requires --download
```
