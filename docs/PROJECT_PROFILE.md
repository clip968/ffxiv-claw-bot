# PROJECT PROFILE - ffxiv-claw-bot

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`

## Project Purpose

이 프로젝트는 파이널판타지14 전용 로컬 지식 베이스와 OpenClaw/Discord agent를 만들기 위한 프로젝트다.

목표는 단순 RAG 챗봇이 아니다. URL, 문서, 패치노트, 공대 자료를 지속적으로 저장하고, 이를 raw archive, LLM Wiki markdown, SQLite FTS5, graph layer로 재구성한 뒤 근거 기반 답변을 제공한다.

## Current Phase

v0.3 Google Drive sync와 v0.4-01 Drive write foundation은 구현 완료 상태로 보존한다.

2026-05-15 현재 기본 v0.4 운영 경로는 Google Drive write/publish가 아니라 `/mnt/d/ffixiv-bot-storage` 기반 Local Storage + OpenClaw Notion direct control이다.

Drive 기반 sync/write 구조는 Legacy / Deferred / Optional Integration이다. 삭제하지 않는다.

## Source of Truth

- 원본 파일 저장소: `/mnt/d/ffixiv-bot-storage`
- 문서 source of truth: repo `docs/`
- 작업 관리/status/index layer: Notion
- 처리용 snapshot: `raw/local_storage`
- 파생 산출물: `wiki`, `graph`, `db/ffxiv.sqlite`

Notion은 원본 파일 저장소가 아니다. Notion에는 local source path, category, source_id, processing status, wiki path, graph status, last error 같은 상태 metadata만 기록한다.

## Core Pipeline

```text
Local storage / URL / Discord/OpenClaw request / Notion local path
-> raw/local_storage snapshot 또는 raw/urls 저장
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki markdown 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

원본을 단순 저장하지 않고 FFXIV 개념 단위 wiki로 재구성한다. wiki 문서에서 entity와 relation을 뽑아 graph를 만든다.

embedding/vector DB는 아직 도입하지 않는다.

## v0.4 Planning

기본 v0.4 master plan:

- `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`

Historical legacy master plan:

- `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

Active v0.4 feature map:

1. `v04-00-openclaw-ingest-contract`
2. `v04-01-local-storage-foundation`
3. `v04-02-openclaw-notion-control-contract`
4. `v04-03-ingest-local-note-cli`
5. `v04-04-local-publish-then-rebuild`
6. `v04-05-status-notification`
7. `v04-legacy-drive-integration`

## Key Tools

- `tools/init_db.py`: SQLite schema 생성
- `tools/ingest_url.py`: URL HTML 수집 및 raw 저장
- `tools/compile_wiki.py`: raw content를 wiki markdown으로 변환하고 FTS 색인 갱신
- `tools/search_kb.py`: SQLite FTS5 기반 검색, graph_paths 포함
- `tools/answer.py`: 검색 결과 기반 context pack과 근거 답변 출력
- `tools/build_graph.py`: wiki/source 기반 deterministic graph 생성
- `tools/graph_path.py`: graph 관계 조회
- `tools/sync_storage.py`: Local Storage manifest dry-run/apply sync
- `tools/sync_drive.py`: Google Drive sync, legacy optional integration
- `tools/publish_drive.py`: Google Drive write/publish, legacy optional integration

## Development Principles

1. 기능은 작은 CLI 단위로 먼저 검증한다.
2. Discord/OpenClaw 연결은 로컬 CLI pipeline이 안정화된 뒤 진행한다.
3. 행동이 바뀌는 코드 변경은 먼저 실패하는 unittest를 작성한다.
4. `/mnt/d/ffixiv-bot-storage`가 사용자가 관리하는 원본 파일 저장소다.
5. `raw/local_storage`, `wiki`, `db`, FTS, graph는 재생성 가능한 파생 계층이다.
6. Notion은 파일 저장소가 아니라 OpenClaw control/status/index layer다.
7. Google Drive 구현은 삭제하지 않고 Legacy / Deferred / Optional Integration으로 유지한다.
8. embedding/vector DB는 별도 결정 전까지 도입하지 않는다.
9. 출처 없는 패치 내용, 직업 변경점, BIS 정보는 생성하지 않는다.
10. repo `docs/`가 구현 계약과 작업 흐름의 source of truth다.

## Docs Structure

- `docs/specs/`: 구현 계약
- `docs/adrs/`: 기술 결정 이유
- `docs/plans/`: 작업 계획
- `docs/runbooks/`: 반복 가능한 실행 절차
- `docs/handoff/`: 다음 session 인계
- `docs/archive/`: 현재 실행 대상이 아닌 과거 문서

Notion 문서보다 repo `docs/`를 우선한다. Notion에만 있는 정보는 stale할 수 있다고 간주한다.
