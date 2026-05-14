# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.3-05 Drive rebuild chain (wiki/FTS/graph) 완료. v0.3 전체 완료.
v0.4-00 OpenClaw Ingest Contract 완료. v0.4-01 Drive Write Foundation 완료. v0.4 feature 02~05는 미구현.

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
- **v0.4-00 OpenClaw Ingest Contract** (ingest request/result JSON 계약 정의)
- **v0.4-01 Drive Write Foundation** (Drive write/publish 기반 구현)

미구현:
- Discord/OpenClaw 연결
- OpenClaw/Discord 저장 요청 CLI/adapter 연결
- publish 후 sync/rebuild 연결
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
7. `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md` (v0.4 master plan, feature00 완료)
8. `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` (완료, contract 정의)
9. `docs/plans/v04/2026-05-14-v04-01-drive-write-foundation.md` (다음 구현 1순위)
10. `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` (참고용)
11. `docs/plans/v03/2026-05-14-v03-04-drive-export-download.md` (참고용)
12. `docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md` (참고용)
13. `docs/plans/v03/2026-05-14-v03-02-fixture-apply.md` (참고용)
14. `docs/plans/v03/2026-05-14-v03-01-manifest-dry-run.md` (참고용)

## 이번 세션 완료: v0.4-00 OpenClaw Ingest Contract

`docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` 참조.

완료된 contract 정의:

1. **입력 타입 결정**: `url`, `text_note`, `markdown_file`, `plain_text_file`, `binary_attachment` 5가지
2. **Ingest Request JSON**: `source_type`, `content_type`, `title`, `body`, `url`, `attachments[]`, `category`, `author`, `channel`, `created_at`
3. **Category 매핑**: Drive `FFXIV_KB` 폴더 구조와 일치하는 7개 category (patch_notes, job_guides, raid_guides, static_docs, macros, bis_sheets, personal_notes)
4. **Result JSON**: `status`, `actions[]`, `summary`, `dry_run` — spec0003 JSON 출력 패턴 재사용
5. **Dry-run/apply 차이**: dry_run=true는 계획만 출력 (Drive/raw/DB 변경 없음), false는 실제 실행
6. **오류 계약**: `invalid_input`, `unsupported_attachment`, `drive_auth_missing`(전체 실패), `drive_write_failed`, `rebuild_failed`(부분 실패)
7. **응답 문구 기준**: result JSON을 OpenClaw 자연어 응답으로 변환하는 기준
8. **Spec 불필요**: v04-00 plan 자체가 contract 역할, 별도 spec 파일 생성하지 않음

참조한 문서:
- `docs/specs/01-architecture.md`: source metadata 형식, Drive 폴더 구조
- `docs/specs/0003-google-drive-sync.md`: dry-run/apply JSON 출력 패턴, raw path 규칙
- `docs/specs/03-roadmap.md`: v0.4 범위
- `docs/adrs/0002-drive-is-canonical-source.md`: Drive canonical source 원칙

코드 변경 없음. 문서 계약 plan.
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

## 이번 세션 완료: v0.4-01 Drive Write Foundation

`docs/plans/v04/2026-05-14-v04-01-drive-write-foundation.md` 참조.

ADR 0005: Drive write scope `drive` (full), file upload (no Docs convert), timestamp append 중복 정책, config file folder ID.

### 구현한 것

1. **`tools/publish_drive.py`** (신규, 670+ line):
   - `--dry-run` / `--apply` / `--auth` CLI
   - Drive API `files.create`로 folder 내 파일 업로드
   - 로컬 `raw/drive/<category>/`에 raw content 저장
   - `db/ffxiv.sqlite` `sources` 테이블 upsert
   - 중복 title → timestamp append (`My Note__2026-05-14`)
   - v04-00 ingest contract JSON 출력 형식 준수
   - `source_type`: `text_note`, `markdown_file`, `plain_text_file` 지원 (`url`, `binary_attachment`는 v0.4-01에서 미지원)
   - `--folders-config` YAML에서 category → folder ID 매핑

2. **`tests/test_publish_drive.py`** (신규, 17 tests):
   - Dry-run JSON shape 검증
   - Drive API 호출 없음 검증
   - Apply → Drive file 생성 검증 (FakeDriveService)
   - Raw content 저장 검증
   - DB sources upsert 검증
   - 중복 title timestamp append 검증
   - 오류 입력 검증 (missing body, invalid category, missing token, missing folder config)
   - v04-00 contract format 준수 검증
   - PyYAML 없는 환경에서 folders config fallback 검증
   - Meta-test: 모든 unittest가 실제 API/token 없이 통과

3. **`docs/adrs/0005-drive-write-scope-and-upload.md`** (신규)
4. **`docs/runbooks/publish-drive.md`** (신규)
5. **`docs/DOC_OWNERS.yml`** 업데이트 (publish_drive.py, test)

### 결정 사항 (ADR 0005)

| 항목 | 결정 |
|---|---|
| OAuth scope | `drive` (full) — 기존 read-only와 별도 token 관리 |
| Upload 방식 | File upload (원본 `.md`/`.txt` 형식 보존, Google Docs convert 안 함) |
| 중복 정책 | Timestamp append (`My Note__2026-05-14.md`) |
| Folder ID 입력 | `config/drive_folders.yaml` config file |
| 테스트 전략 | FakeDriveService mock + dry-run은 API 호출 없음 + smoke test 제외 |

`docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`와 `docs/plans/v04/` 참조.

추가한 v0.4 feature plan:
1. `v04-00-openclaw-ingest-contract`: OpenClaw/Discord ingest request/result 계약
2. `v04-01-drive-write-foundation`: Drive write/upload 기반
3. `v04-02-ingest-discord-note-cli`: Discord note ingest CLI
4. `v04-03-openclaw-tool-adapter`: OpenClaw 설정/tool adapter
5. `v04-04-publish-then-rebuild`: Drive publish 후 sync/rebuild 연결
6. `v04-05-discord-summary-notification`: Discord 저장 결과/부분 실패 알림

embedding/vector DB는 필요성이 확인될 때까지 보류.

## v0.4 진행 상황

| Feature | Status |
|---|---|
| `v04-00-openclaw-ingest-contract` | **Completed 2026-05-14** (ingest request/result JSON 계약 정의) |
| `v04-01-drive-write-foundation` | **Completed 2026-05-14** (Drive write/publish 구현 완료) |
| `v04-02-ingest-discord-note-cli` | [ ] 미구현 — 다음 구현 1순위 |
| `v04-03-openclaw-tool-adapter` | [ ] 미구현 |
| `v04-04-publish-then-rebuild` | [ ] 미구현 |
| `v04-05-discord-summary-notification` | [ ] 미구현 |

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
