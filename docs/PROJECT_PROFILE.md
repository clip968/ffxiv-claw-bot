# PROJECT PROFILE - ffxiv-claw-bot

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`

## Project Purpose

이 프로젝트는 파이널판타지14 전용 로컬 지식 베이스와 OpenClaw/Discord agent를 만들기 위한 프로젝트다.

목표는 단순 RAG 챗봇이 아니라, URL, 문서, 패치노트, 공대 자료를 지속적으로 저장하고 이를 raw archive, wiki markdown, SQLite FTS5, graph layer로 재구성한 뒤 근거 기반 답변을 제공하는 것이다.

## Core Pipeline

```text
Local storage / URL / Discord/OpenClaw request / Notion local path
  -> raw/local_storage snapshot 또는 raw/urls 저장
  -> sources DB 기록
  -> wiki markdown 생성
  -> SQLite FTS 색인
  -> search_kb.py 검색
  -> answer.py context pack 생성
  -> graph 구축
  -> graph path 포함 답변
```

## Current Phase

v0.3 Google Drive sync와 v0.4-01 Drive write foundation은 구현 완료 상태로 보존한다.
2026-05-14 이후 기본 운영 경로는 Google Drive가 아니라 `/mnt/d/ffixiv-bot-storage` 기반 Local Storage + OpenClaw Notion direct control로 전환한다.

Drive 기반 sync/write 구조는 Legacy / Deferred / Optional Integration이다.

## Key Tools

- `tools/init_db.py`: SQLite schema 생성
- `tools/ingest_url.py`: URL HTML 수집 및 raw 저장
- `tools/compile_wiki.py`: raw HTML을 wiki markdown으로 변환하고 FTS 색인 갱신
- `tools/search_kb.py`: SQLite FTS5 기반 검색 (graph_paths 포함)
- `tools/answer.py`: 검색 결과 기반 context pack 및 근거 답변 출력
- `tools/build_graph.py`: wiki/source 기반 deterministic graph 생성
- `tools/graph_path.py`: graph 관계 조회
- `tools/sync_storage.py`: Local Storage manifest dry-run sync skeleton (new/changed/unchanged/skipped 분류, JSON 출력)
- `tools/sync_drive.py`: Google Drive 동기화 (Legacy / Deferred optional integration)
- `tools/publish_drive.py`: Google Drive write/publish (Legacy / Deferred optional integration)

## Development Principles

1. 큰 기능을 한 번에 구현하지 않는다.
2. 각 기능은 CLI에서 먼저 검증한다.
3. Discord/OpenClaw 연결은 로컬 CLI 파이프라인이 안정화된 뒤 진행한다.
4. v0.1~v0.3에서는 embedding을 추가하지 않는다.
5. FFXIV 정보는 로컬 KB에 근거가 있을 때만 확정적으로 답한다.
6. 출처 없는 패치 내용, 직업 변경점, BIS 정보는 생성하지 않는다.
7. `/mnt/d/ffixiv-bot-storage`가 사람이 관리하는 원본 파일 저장소다.
8. 로컬 `raw/local_storage`, `wiki`, `db`, FTS, graph는 재생성 가능한 파생 캐시다.
9. Notion은 원본 파일 저장소가 아니라 OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층이다.
10. Google Drive 구현은 삭제하지 않고 Legacy / Deferred / Optional Integration으로 유지한다.

## Docs Structure (Source of Truth)

GitHub repo `docs/`가 유일한 source of truth다.

- `docs/specs/`: 구현 계약
- `docs/adrs/`: 기술 결정 이유
- `docs/plans/`: 작업 계획 (임시)
- `docs/runbooks/`: 실행 절차
- `docs/handoff/`: 다음 session 인계
- `docs/archive/`: 오래된 문서 보관

Notion은 더 이상 문서 source of truth가 아니다. Notion 내용은 2026-05-14에 모두 repo docs로 이관 완료되었다.

OpenClaw는 Notion을 직접 다루되, Notion에는 원본 파일 자체를 올리지 않는다. Notion에는 local source path, category, source_id, processing status, wiki path, graph status, last error 같은 상태 metadata만 기록한다.
