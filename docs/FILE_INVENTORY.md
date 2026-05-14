# FILE_INVENTORY - ffxiv-claw-bot

이 문서는 AI가 다음 작업을 빠르게 이해하는 데 필요한 핵심 파일만 정리한다.
전체 작업 트리 복제가 목적이 아니다.

## Core Tools

| Path | Role | Status |
|---|---|---|
| `tools/init_db.py` | SQLite schema 생성 | 완료 |
| `tools/ingest_url.py` | URL HTML 수집 및 raw 저장 | 완료 |
| `tools/compile_wiki.py` | raw HTML -> wiki markdown 변환 및 FTS 색인 | 완료 |
| `tools/search_kb.py` | `wiki_fts` 기반 검색 (graph_paths 포함) | 완료 |
| `tools/answer.py` | 검색 결과 기반 context pack 및 근거 답변 출력 | 완료 |
| `tools/build_graph.py` | wiki/source 기반 deterministic graph 생성 | 완료 |
| `tools/graph_path.py` | graph 관계 조회 | 완료 |
| `tools/sync_drive.py` | Google Drive 동기화 (dry-run만) | dry-run 완료 |

## Data / Output

| Path | Role | Status |
|---|---|---|
| `db/ffxiv.sqlite` | sources, wiki_pages, wiki_fts, graph 테이블 저장 | 생성 산출물 |
| `raw/urls/` | 수집한 URL HTML 저장 | 생성 산출물 |
| `raw/drive/` | Google Drive 문서 저장 예정 (--apply 후 생성) | 예정 |
| `wiki/source_summaries/` | source 단위 wiki markdown 저장 | 생성 산출물 |
| `graph/nodes.json` | graph node export | 생성 산출물 |
| `graph/edges.json` | graph edge export | 생성 산출물 |

## Docs (Source of Truth)

| Path | Role |
|---|---|
| `docs/PROJECT_PROFILE.md` | 프로젝트 개요와 개발 원칙 |
| `docs/FILE_INVENTORY.md` | 핵심 파일 인벤토리 |
| `docs/WORKFLOW.md` | 작업 흐름 규칙 |
| `docs/README.md` | docs 디렉터리 개요 |
| `docs/specs/0001-local-kb-pipeline.md` | v0.1 local KB pipeline spec |
| `docs/specs/0002-graph-layer.md` | v0.2 graph layer spec |
| `docs/specs/0003-google-drive-sync.md` | v0.3 Google Drive sync spec |
| `docs/adrs/0001-use-sqlite-fts-before-vector-db.md` | FTS 우선 결정 |
| `docs/adrs/0002-drive-is-canonical-source.md` | Drive canonical source 결정 |
| `docs/adrs/0003-notion-is-index-not-source-of-truth.md` | Notion index 결정 |
| `docs/adrs/0004-dry-run-before-real-drive-api.md` | dry-run 우선 결정 |
| `docs/plans/2026-05-14-post-v03-next-steps.md` | v0.3 이후 다음 단계 |
| `docs/handoff/CURRENT_HANDOFF.md` | 현재 상태 handoff |
| `docs/archive/notion/` | Notion에서 이관한 오래된 문서 (참고용) |

## Notion에 기록하지 않을 것

- `raw/urls/*.html` 전체 내용
- `wiki/source_summaries/*.md` 전체 내용
- `graph/nodes.json`, `graph/edges.json` 전체 내용
- `db/ffxiv.sqlite` 내부 레코드 전체
- `__pycache__`
- 임시 로그 파일
- 테스트 출력 전문

## 기록 원칙

Notion에는 핵심 엔트리포인트와 역할만 기록한다.
실제 파일 내용과 변경 이력은 GitHub, Git commit, 로컬 파일시스템을 source of truth로 삼는다.
