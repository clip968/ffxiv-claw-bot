# FILE_INVENTORY - ffxiv-claw-bot

이 문서는 AI agent가 다음 작업을 빠르게 이해하는 데 필요한 핵심 파일만 정리한다.

## Core Tools

| Path | Role | Status |
|---|---|---|
| `tools/init_db.py` | SQLite schema 생성 | Active |
| `tools/ingest_url.py` | URL HTML 수집 및 raw 저장 | Legacy v0.1 path |
| `tools/fetch_url.py` | v0.5 단일 URL fetch helper | Active v0.5 |
| `tools/process_source.py` | 통합 source processing entrypoint | Active v0.5 |
| `tools/extractors/lodestone.py` | Lodestone `.news__detail__wrapper` article extractor | Active v05.1 |
| `tools/compile_wiki.py` | raw content -> wiki markdown 변환 및 FTS 색인 | Active |
| `tools/search_kb.py` | `wiki_fts` 기반 검색, graph_paths 포함 | Active |
| `tools/answer.py` | 검색 결과 기반 context pack과 근거 답변 출력 | Active |
| `tools/build_graph.py` | wiki/source 기반 deterministic graph 생성 | Active |
| `tools/graph_path.py` | graph 관계 조회 | Active |
| `tools/sync_storage.py` | Local Storage manifest dry-run/apply sync | Active v0.4 local path |
| `tools/sync_drive.py` | Google Drive sync | Legacy / Deferred optional integration |
| `tools/publish_drive.py` | Google Drive write/publish | Legacy / Deferred optional integration |

## v0.6 Source Processing Packages

| Path | Role | Status |
|---|---|---|
| `src/source_processing/models.py` | v0.6 `ExtractedSource` shared model | Active v0.6 |
| `src/source_processing/errors.py` | v0.6 extractor error hierarchy | Active v0.6 |
| `src/source_processing/extractor_registry.py` | v0.6 extension-to-extractor registry | Active v0.6 |
| `src/source_processing/extractors/__init__.py` | v0.6 concrete extractor exports | Active v0.6 |
| `src/source_processing/extractors/text.py` | v0.6 UTF-8 plain text extractor | Active v0.6 |
| `src/source_processing/extractors/markdown.py` | v0.6 markdown extractor with lightweight frontmatter metadata | Active v0.6 |
| `src/source_processing/extractors/html.py` | v0.6 generic HTML extractor that strips script/style/nav/footer noise | Active v0.6 |
| `src/source_processing/extractors/csv.py` | v0.6 CSV-to-Markdown-table extractor | Active v0.6 |
| `src/source_processing/extractors/xlsx.py` | v0.6 standard-library XLSX-to-Markdown-table extractor | Active v0.6 |

## Data / Output

| Path | Role | Status |
|---|---|---|
| `/mnt/d/ffixiv-bot-storage/` | 사용자가 관리하는 원본 파일 저장소 | External canonical source |
| `raw/local_storage/` | Local Storage source의 처리용 snapshot | Derived cache |
| `raw/urls/` | 수집한 URL HTML 저장 | Derived cache |
| `db/ffxiv.sqlite` | sources, wiki_pages, wiki_fts, graph table 저장 | Derived local DB |
| `wiki/source_summaries/` | source 단위 LLM Wiki markdown | Derived cache |
| `graph/nodes.json` | graph node export | Derived cache |
| `graph/edges.json` | graph edge export | Derived cache |
| `raw/drive/` | Google Drive 문서 local cache | Legacy / Deferred optional integration |

## Docs Source of Truth

| Path | Role |
|---|---|
| `docs/PROJECT_PROFILE.md` | 프로젝트 개요와 현재 운영 원칙 |
| `docs/FILE_INVENTORY.md` | 핵심 파일 inventory |
| `docs/WORKFLOW.md` | 작업 흐름 규칙 |
| `docs/README.md` | docs directory 개요 |
| `docs/specs/0001-local-kb-pipeline.md` | local KB pipeline spec |
| `docs/specs/0002-graph-layer.md` | graph layer spec |
| `docs/specs/0003-google-drive-sync.md` | Google Drive sync spec, legacy optional integration |
| `docs/adrs/0001-use-sqlite-fts-before-vector-db.md` | FTS 우선 결정 |
| `docs/adrs/0002-drive-is-canonical-source.md` | Drive canonical source 결정, superseded |
| `docs/adrs/0003-notion-is-index-not-source-of-truth.md` | Notion index 결정 |
| `docs/adrs/0004-dry-run-before-real-drive-api.md` | Drive dry-run 우선 결정 |
| `docs/adrs/0005-drive-write-scope-and-upload.md` | Drive write 결정, legacy optional integration |
| `docs/adrs/0006-local-storage-and-notion-control.md` | Local Storage + Notion direct control 결정 |
| `docs/runbooks/local-storage.md` | Local Storage ingest/sync 실행 절차 |
| `docs/runbooks/openclaw-notion.md` | OpenClaw Notion direct control 실행 절차 |
| `docs/runbooks/sync-drive.md` | Drive sync legacy runbook |
| `docs/runbooks/publish-drive.md` | Drive publish legacy runbook |
| `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md` | Active v0.4 master plan |
| `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md` | Historical legacy v0.4 Drive-era master plan |
| `docs/specs/0004-v05-source-processing-pipeline.md` | v0.5 source processing pipeline spec |
| `docs/specs/0004a-v05.1-source-processing-hardening.md` | v05.1 source processing hardening spec |
| `docs/specs/0005- v06-Multi-format-Source-Processing.md` | v0.6 multi-format source processing and derived wiki spec |
| `docs/plans/v06/README.md` | v0.6 feature map |
| `docs/handoff/CURRENT_HANDOFF.md` | 현재 상태 handoff |

## v0.5 Plan Files

| Path | Role | Status |
|---|---|---|
| `docs/plans/v05/README.md` | v0.5 feature map | Active |
| `docs/plans/v05/2026-05-16-v05-01-spec-and-plan.md` | Spec + plan 작성 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-02-openclaw-skill-draft.md` | OpenClaw skill 문서 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-03-process-source-skeleton.md` | process_source.py CLI skeleton | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-04-local-source-integration.md` | Local source ingest 연결 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-05-url-integration.md` | URL fetch + ingest 연결 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-06-rebuild-integration.md` | wiki/FTS/graph rebuild 연결 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-07-notion-payload-integration.md` | Notion payload 생성 연결 | **Completed** 2026-05-16 |
| `docs/plans/v05/2026-05-16-v05-08-tests-and-runbook.md` | 테스트, runbook, handoff 정리 | **Completed** 2026-05-16 |

## v05.1 Plan Files

| Path | Role | Status |
|---|---|---|
| `docs/plans/v05.1/README.md` | v05.1 feature map | Active |
| `docs/plans/v05.1/2026-05-16-v05.1-01-spec-and-plan.md` | v05.1 scope, spec, task breakdown 고정 | **Completed** 2026-05-16 |
| `docs/plans/v05.1/2026-05-16-v05.1-02-lodestone-fixture-and-red-tests.md` | Lodestone fixture와 extractor red test 작성 | **Completed** 2026-05-16 |
| `docs/plans/v05.1/2026-05-16-v05.1-03-lodestone-extractor.md` | Lodestone 전용 article extractor 구현 | **Completed** 2026-05-16 |
| `docs/plans/v05.1/2026-05-16-v05.1-04-fetch-url-routing.md` | `fetch_url.py`에서 Lodestone URL을 전용 extractor로 라우팅 | Pending |
| `docs/plans/v05.1/2026-05-16-v05.1-05-process-source-extractor-metadata.md` | `process_source.py` action log에 extractor metadata 포함 | Pending |
| `docs/plans/v05.1/2026-05-16-v05.1-06-entrypoint-boundary-docs.md` | 공식 entrypoint와 helper boundary 문서화 | Pending |
| `docs/plans/v05.1/2026-05-16-v05.1-07-runbook-regression-tests.md` | helper misuse/Notion boundary 문서 회귀 테스트 추가 | Pending |
| `docs/plans/v05.1/2026-05-16-v05.1-08-final-verification-and-handoff.md` | 전체 검증, docs freshness, handoff 마무리 | Pending |

## v0.4 Plan Files

| Path | Role | Status |
|---|---|---|
| `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` | Local Storage ingest request/result contract | Active |
| `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md` | Local Storage foundation plan | Active proposed |
| `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md` | OpenClaw Notion control contract plan | Active proposed |
| `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md` | Local note ingest CLI plan | Active proposed |
| `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md` | Local publish/snapshot/rebuild plan | Active proposed |
| `docs/plans/v04/2026-05-14-v04-05-status-notification.md` | Notion status + Discord summary plan | Active proposed |
| `docs/plans/v04/2026-05-14-v04-legacy-drive-integration.md` | Drive optional integration plan | Deferred |
| `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md` | Drive write foundation | Completed but deferred |
| `docs/plans/v04/legacy/2026-05-14-v04-02-ingest-discord-note-cli.md` | Historical local ingest CLI slice | Historical |
| `docs/plans/v04/legacy/2026-05-14-v04-03-openclaw-tool-adapter.md` | Drive-era adapter plan | Superseded |
| `docs/plans/v04/legacy/2026-05-14-v04-04-publish-then-rebuild.md` | Drive-era publish/rebuild plan | Superseded |
| `docs/plans/v04/legacy/2026-05-14-v04-05-discord-summary-notification.md` | Drive-era Discord summary plan | Superseded |

## Notion에 기록하지 않을 것

- `raw/urls/*.html` 전체 내용
- `/mnt/d/ffixiv-bot-storage/sources/**` 원본 파일 전체 내용
- `/mnt/d/ffixiv-bot-storage/exports/**` 변환본 전체 내용
- `wiki/source_summaries/*.md` 전체 내용
- `graph/nodes.json`, `graph/edges.json` 전체 내용
- `db/ffxiv.sqlite` 내부 레코드 전체
- `__pycache__`
- 임시 로그 파일
- 테스트 출력 전문

## Notion 기록 원칙

Notion에는 인덱스 포인트, local path, 처리 상태, 실패 사유, 다음 액션만 기록한다.

실제 파일 내용은 `/mnt/d/ffixiv-bot-storage`, 문서 계약과 변경 이력은 GitHub/repo docs를 source of truth로 따른다.
