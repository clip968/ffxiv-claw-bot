# PROJECT PROFILE - ffxiv-claw-bot

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`

## Project Purpose

이 프로젝트는 파이널판타지14 전용 로컬 지식 베이스와 OpenClaw/Discord agent를 만들기 위한 프로젝트다.

목표는 단순 RAG 챗봇이 아니라, URL, 문서, 패치노트, 공대 자료를 지속적으로 저장하고 이를 raw archive, wiki markdown, SQLite FTS5, graph layer로 재구성한 뒤 근거 기반 답변을 제공하는 것이다.

## Core Pipeline

```text
URL / Drive / Discord note
  -> raw 저장
  -> sources DB 기록
  -> wiki markdown 생성
  -> SQLite FTS 색인
  -> search_kb.py 검색
  -> answer.py context pack 생성
  -> graph 구축
  -> graph path 포함 답변
```

## Current Phase

v0.3 Google Drive sync dry-run 완료.
manifest 기반 --apply는 아직 미구현.
실제 Google Drive API/OAuth/Google Docs export-download도 아직 미구현.

## Key Tools

- `tools/init_db.py`: SQLite schema 생성
- `tools/ingest_url.py`: URL HTML 수집 및 raw 저장
- `tools/compile_wiki.py`: raw HTML을 wiki markdown으로 변환하고 FTS 색인 갱신
- `tools/search_kb.py`: SQLite FTS5 기반 검색 (graph_paths 포함)
- `tools/answer.py`: 검색 결과 기반 context pack 및 근거 답변 출력
- `tools/build_graph.py`: wiki/source 기반 deterministic graph 생성
- `tools/graph_path.py`: graph 관계 조회
- `tools/sync_drive.py`: Google Drive 동기화 (현재 dry-run만)

## Development Principles

1. 큰 기능을 한 번에 구현하지 않는다.
2. 각 기능은 CLI에서 먼저 검증한다.
3. Discord/OpenClaw 연결은 로컬 CLI 파이프라인이 안정화된 뒤 진행한다.
4. v0.1~v0.3에서는 embedding을 추가하지 않는다.
5. FFXIV 정보는 로컬 KB에 근거가 있을 때만 확정적으로 답한다.
6. 출처 없는 패치 내용, 직업 변경점, BIS 정보는 생성하지 않는다.
7. Google Drive `FFXIV_KB`가 사람이 관리하는 canonical source다.
8. 로컬 `raw/drive`, `wiki`, `db`, FTS, graph는 재생성 가능한 파생 캐시다.

## Docs Structure (Source of Truth)

GitHub repo `docs/`가 유일한 source of truth다.

- `docs/specs/`: 구현 계약
- `docs/adrs/`: 기술 결정 이유
- `docs/plans/`: 작업 계획 (임시)
- `docs/runbooks/`: 실행 절차
- `docs/handoff/`: 다음 session 인계
- `docs/archive/`: 오래된 문서 보관

Notion은 더 이상 source of truth가 아니다. Notion 내용은 2026-05-14에 모두 repo docs로 이관 완료되었다.
