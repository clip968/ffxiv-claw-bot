# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.3-05 Drive rebuild chain (wiki/FTS/graph) 완료. v0.3 전체 완료.

완료된 것:
- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run (manifest 기반, 실제 Drive API 없음)
- v0.3 Google Drive sync fixture apply (`--apply`, raw/drive 저장 + DB upsert, 실제 Drive API 없음)
- v0.3 Google Drive API 인증/파일 목록 조회 (`--auth`, `--from-drive`, metadata -> manifest 변환)
- v0.3 Google Docs export/download (`--from-drive --download`, Markdown export, binary download, SHA256 content hash, `--apply` 연결)
- **v0.3-05 Drive rebuild chain** (`--rebuild`, compile_wiki Markdown 처리, build_graph 연결)
- docs-first workflow tooling (DOC_OWNERS, finish_task, check_docs_freshness 등)
- **Notion 문서 repo docs 이관 완료** (이전 세션, 2026-05-14)

미구현:
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
7. `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md` (다음 구현 1순위)
8. `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` (완료, 참고용)
9. `docs/plans/v03/2026-05-14-v03-04-drive-export-download.md` (참고용)
10. `docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md` (참고용)
11. `docs/plans/v03/2026-05-14-v03-02-fixture-apply.md` (참고용)
12. `docs/plans/v03/2026-05-14-v03-01-manifest-dry-run.md` (참고용)

## 이번 세션 완료: Drive rebuild chain (v0.3-05)

`docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` 참조 (상세 구현 요약 있음).

완료된 하위 작업:
1. `compile_wiki.py`에서 `source_type == "drive_document"` 감지 시 HTML 파싱 없이 raw Markdown/text을 그대로 사용
2. `sync_drive.py`에 `--rebuild` 플래그 추가 (`--apply`와 함께 사용 필수)
3. `build_plan_item()`에 실제 DB source_id 반영 (기존 source는 DB id, 새 source는 `drive_source_id()` 생성)
4. `rebuild_for_items()` 함수로 compile_wiki + build_graph 자동 실행
5. compile 실패 시에도 나머지 source 계속 처리 (부분 실패 정책)
6. `test_compile_wiki.py` 추가: drive_document Markdown 처리 검증
7. 기존 `test_sync_drive.py`에서 rebuild end-to-end 테스트 추가
8. `--from-drive` 경로와 manifest 경로 양쪽에서 `--rebuild` 지원

## 이번 세션 완료: v0.3 코드 리뷰 지적 수정

수정한 것:
1. `tools/html_utils.py` 추가: BeautifulSoup이 없어도 stdlib HTML parser fallback으로 기본 테스트/import가 통과하도록 변경
2. `sync_drive.py --from-drive`: root folder 아래 category folder를 재귀 조회하도록 변경
3. `sync_drive.py --rebuild`: CLI의 `--db-path`, `--root-path`를 compile/graph 단계까지 전달
4. `--rebuild` 대상 제한: Markdown/text/HTML 계열만 compile하고 PDF/이미지 같은 binary raw는 제외
5. `compile_wiki.py`, `build_graph.py`: SQLite connection을 명시적으로 close해서 Windows 임시 DB lock 방지
6. v0.3 master plan과 spec/runbook 상태 불일치 정리

추가/갱신한 테스트:
- Drive category folder 재귀 조회
- CLI rebuild 경로 전달
- binary Drive file rebuild 제외
- bs4 미설치 환경에서 HTML text fallback

검증:

```bash
python -m unittest tests.test_sync_drive tests.test_compile_wiki
python -m unittest discover -s tests -p "test_*.py"
python scripts/finish_task.py
```

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

- `tools/` 구현 코드 (v0.3-05 작업 완료 후)
- `tests/` 코드 (v0.3-05 작업 완료 후)
- `config/`
- `raw/`
- `wiki/`
- `graph/`
- `db/`
- `db/ffxiv.sqlite`
- Discord/OpenClaw 연결 (v0.4에서 다룰 예정)
- embedding/vector DB
- 기존 사용자 변경

## 테스트 명령

```bash
python scripts/finish_task.py
```

특정 unittest만:

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest tests.test_sync_drive
python -m unittest tests.test_compile_wiki
```

이번 v0.3-05 세션에서 확인한 명령:

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest tests.test_sync_drive
python -m unittest tests.test_compile_wiki
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```
