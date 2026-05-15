# v0.4 Legacy Master Plan: OpenClaw Drive Ingest

## Legacy Notice

This file is preserved as a historical v0.4 transition plan. It is no longer the default v0.4 master plan.

Current default v0.4 planning lives in:

`docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`

Google Drive write/publish remains a Legacy / Deferred / Optional Integration. The default source of truth for user-managed source files is `/mnt/d/ffixiv-bot-storage`; Notion is an OpenClaw control/status/index layer, not file storage.

---

# Historical v0.4 Master Plan: OpenClaw Local Storage Ingest

Spec:
- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `docs/adrs/0006-local-storage-and-notion-control.md`

Legacy reference:
- `docs/specs/0003-google-drive-sync.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- `docs/adrs/0005-drive-write-scope-and-upload.md`

## Status

v0.4의 기본 운영 경로는 OpenClaw/Discord에서 들어온 저장 요청을 `/mnt/d/ffixiv-bot-storage` 원본 저장소에 반영하고, 처리용 snapshot과 로컬 KB를 재빌드한 뒤 Notion 상태판에 결과를 기록하는 구조로 전환한다.

Google Drive 기반 sync/write 구조는 v0.4-01까지 구현되어 있으나, 현재 기본 운영 경로에서는 사용하지 않는다. 향후 외부 클라우드 동기화가 필요할 때 optional integration으로 재검토한다.

## Prerequisite

- v0.3-05 `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` 완료
- v0.4-01 Drive write foundation 완료. 단, 현재는 Legacy / Deferred optional integration으로 격리
- ADR 0006 Local Storage and Notion Control 수락

## Feature Plans

| # | Plan | Status |
|---|---|---|
| 00 | `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` | [x] Completed 2026-05-14, Drive 중심 계약은 legacy reference |
| 01 | `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md` | [x] Completed 2026-05-14, optional legacy integration |
| 02 | `docs/plans/v04/legacy/2026-05-14-v04-02-ingest-discord-note-cli.md` | Historical local ingest slice |
| 03 | `docs/plans/v04/legacy/2026-05-14-v04-03-openclaw-tool-adapter.md` | Superseded by Local Storage/Notion plans |
| 04 | `docs/plans/v04/legacy/2026-05-14-v04-04-publish-then-rebuild.md` | Superseded by Local Storage rebuild plan |
| 05 | `docs/plans/v04/legacy/2026-05-14-v04-05-discord-summary-notification.md` | Superseded by status notification plan |

## v0.4 Default Goal

OpenClaw/Discord에서 다음 흐름을 지원한다.

```text
Discord/OpenClaw 저장 요청 또는 Notion 상태판 처리 대상
-> ingest request 정규화
-> /mnt/d/ffixiv-bot-storage/sources/<category>/ 원본 저장 또는 기존 local path 확인
-> raw/local_storage/<category>/ 처리용 snapshot 생성
-> db/ffxiv.sqlite sources upsert
-> compile_wiki.py로 LLM Wiki markdown 생성 또는 갱신
-> wiki_fts 색인 갱신
-> build_graph.py로 graph nodes/edges 생성
-> Notion 상태판에 처리 결과, 실패 사유, 다음 액션 기록
-> Discord/OpenClaw 결과 메시지
```

## Local Storage Contract

기본 원본 저장소:

```text
/mnt/d/ffixiv-bot-storage/
  incoming/
  sources/
    urls/
    documents/
    sheets/
    patch_notes/
    raid_guides/
    job_guides/
    static_docs/
    macros/
    bis_sheets/
    personal_notes/
  exports/
    markdown/
    text/
    html/
  manifests/
  archive/
```

입력 JSON 개념:

- `source_type`: `text_note`, `markdown_file`, `plain_text_file`, `binary_attachment`, `url`
- `content_type`: 예: `text/markdown`, `text/plain`, `application/pdf`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- 필드: `title`, `body`, `url`, `attachments`, `category`, `author`, `channel`, `created_at`
- category: `patch_notes`, `job_guides`, `raid_guides`, `static_docs`, `macros`, `bis_sheets`, `personal_notes`

출력 JSON 개념:

- `status`: `ok`, `partial`, `error`
- `dry_run`: `true` 또는 `false`
- `actions`: `write_local_source`, `snapshot_raw`, `upsert_source`, `compile_wiki`, `build_graph`, `update_notion_status`
- 각 action은 `target`, `status`, `message`를 가진다.

## Notion Direct Control

OpenClaw는 Notion을 다음 목적으로 직접 다룬다.

- Notion에서 작업 상태를 읽는다.
- Notion에서 저장 요청 또는 처리 대상을 찾는다.
- Notion에 처리 결과, 실패 사유, 다음 액션을 기록한다.
- Notion에는 파일 자체를 올리지 않는다.
- Notion에는 로컬 원본 파일 경로와 처리 상태만 기록한다.
- 실제 파일은 `/mnt/d/ffixiv-bot-storage`에서 읽는다.

Notion 상태 항목 예시:

| Field | Example |
|---|---|
| Title | 흑마 7.5 가이드 |
| Category | job_guides |
| Local Source Path | `/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md` |
| Status | Indexed |
| Source ID | local_001 |
| Wiki Path | `wiki/jobs/black_mage/7_5.md` |
| Graph Status | Built |
| Last Processed | `2026-05-14T00:00:00Z` |
| Last Error | null |

## Graphify + LLM Wiki 유지 조건

Google Drive를 기본 경로에서 빼더라도 다음 구조는 유지한다.

```text
원본 파일 감지
-> raw/local_storage snapshot 생성
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki 문서 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

원본을 단순 저장하지 않고 FFXIV 개념 단위 wiki로 재구성한다. wiki 문서에서 entity와 relation을 뽑아 graph를 만든다. 검색은 metadata + SQLite FTS + graph traversal 중심으로 하며 embedding/vector DB는 아직 도입하지 않는다.

## Legacy / Deferred

기존 Drive 흐름은 다음 의미로만 유지한다.

```text
Discord/OpenClaw 저장 요청
-> Google Drive FFXIV_KB 업로드/생성
-> Drive sync/download/apply
-> wiki/FTS/graph rebuild
-> Discord/OpenClaw 결과 메시지
```

이 흐름은 v0.4-01까지 구현된 optional integration이다. 현재 기본 CLI, runbook, handoff는 Local Storage를 우선한다.

## v0.4 Non-goals

- embedding/vector DB 도입
- 자동 패치노트 크롤링
- 다중 사용자 권한 모델
- Google Sheets CSV 변환
- Discord bot hosting/deployment 자동화
- 원본 파일을 repo 내부에 대량 저장

## How to Update

feature plan 하나가 완료되면:

1. 개별 plan 파일의 `## Status`를 갱신한다.
2. 이 master plan에서 해당 feature의 상태를 갱신한다.
3. `docs/handoff/CURRENT_HANDOFF.md`에 완료 상태와 검증 결과를 반영한다.
