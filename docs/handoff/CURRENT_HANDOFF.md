# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.3 Google Drive sync dry-run 완료.

완료된 것:
- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run (manifest 기반, 실제 Drive API 없음)
- docs-first workflow tooling (DOC_OWNERS, finish_task, check_docs_freshness 등)
- **Notion 문서 repo docs 이관 완료** (이번 세션, 2026-05-14)

미구현:
- manifest 기반 `--apply` (raw/drive 저장 + DB upsert)
- 실제 Google Drive API / OAuth / Google Docs export-download
- Discord/OpenClaw 연결
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
6. `docs/plans/2026-05-14-post-v03-next-steps.md`
7. `docs/runbooks/test.md`

## 다음 구현 후보 1순위: manifest 기반 --apply

`docs/plans/2026-05-14-post-v03-next-steps.md` 후보 1 참조.

포함할 하위 작업:
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
- 실제 Google Drive API/OAuth
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
