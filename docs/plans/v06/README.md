# v0.6 Feature Plans

v0.6 Multi-format Source Processing and Derived Wiki Generation의 feature별 plan을 보관한다.

v0.6의 목표는 두 가지다.

1. 다양한 원본 파일 형식(`.txt`, `.md`, `.html`, `.csv`, `.xlsx`)을 source로 등록하고 자동 처리한다.
2. source별 요약(`wiki/source_summaries/*.md`)을 다시 주제별 derived wiki 문서(`wiki/jobs/*.md` 등)로 재구성한다.

v0.5/v05.1과 동일하게 기본 운영 경로는 `/mnt/d/ffixiv-bot-storage` 기반 Local Storage이며, Notion은 원본 파일 저장소가 아니라 control/status/index layer로만 사용한다.

v0.6 완료 후 목표 파이프라인:

```text
local source file
  -> extension detection
  -> extractor registry
  -> normalized text
  -> source ingest
  -> source summary generation
  -> FTS indexing
  -> graph build
  -> derived wiki generation
  -> wiki/jobs/*.md generation
  -> derived wiki FTS indexing
```

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-16-v06-implementation-plan.md`에 있다.

구현 계약은 `docs/specs/0005- v06-Multi-format-Source-Processing.md` (SPEC 0006)를 따른다.

부모 pipeline 계약은 `docs/specs/0004-v05-source-processing-pipeline.md`와 `docs/specs/0004a-v05.1-source-processing-hardening.md`를 그대로 유지한다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 01 | 2026-05-16-v06-01-extractor-model-and-errors.md | 공통 ExtractedSource 모델과 SourceExtractionError 계열 추가 | **Completed** 2026-05-16 |
| 02 | 2026-05-16-v06-02-extractor-registry.md | 확장자별 extractor를 선택하는 registry 구현 | **Completed** 2026-05-16 |
| 03 | 2026-05-16-v06-03-text-markdown-html-extractors.md | `.txt`, `.md`, `.html` extractor 구현 | **Completed** 2026-05-16 |
| 04 | 2026-05-16-v06-04-csv-extractor.md | `.csv` extractor 구현 | **Completed** 2026-05-16 |
| 05 | 2026-05-16-v06-05-xlsx-extractor.md | `.xlsx` extractor 구현 | **Completed** 2026-05-16 |
| 06 | 2026-05-16-v06-06-process-source-integration.md | `tools/process_source.py`와 extractor layer 연결 | **Completed** 2026-05-16 |
| 07 | 2026-05-16-v06-07-pending-source-loop.md | `tools/process_pending_sources.py` 일괄 처리 CLI 구현 | **Completed** 2026-05-16 |
| 08 | 2026-05-16-v06-08-derived-wiki-foundation.md | source summaries loader/writer/templates foundation 추가 | Pending |
| 09 | 2026-05-16-v06-09-job-catalog-and-aliases.md | FFXIV 직업 canonical slug와 alias resolver 정의 | Pending |
| 10 | 2026-05-16-v06-10-job-wiki-generator.md | `wiki/jobs/<job>.md` deterministic generator 구현 | Pending |
| 11 | 2026-05-16-v06-11-generate-derived-wiki-cli.md | `tools/generate_derived_wiki.py` 통합 CLI 구현 | Pending |
| 12 | 2026-05-16-v06-12-fts-indexing-extension.md | FTS 인덱싱에 derived wiki 문서 포함 | Pending |
| 13 | 2026-05-16-v06-13-derived-wiki-hook.md | source 처리 후 derived wiki 생성 hook 연결 | Pending |
| 14 | 2026-05-16-v06-14-readme-and-handoff.md | README와 handoff 문서 업데이트 | Pending |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 01 | `tests/test_v06_extractors.py` | `src/source_processing/models.py`, `src/source_processing/errors.py` |
| 02 | `tests/test_v06_extractors.py` | `src/source_processing/extractor_registry.py`, `src/source_processing/extractors/__init__.py` |
| 03 | `tests/test_v06_extractors.py` | `src/source_processing/extractors/text.py`, `markdown.py`, `html.py` |
| 04 | `tests/test_v06_extractors.py` | `src/source_processing/extractors/csv.py` |
| 05 | `tests/test_v06_extractors.py` | `src/source_processing/extractors/xlsx.py` |
| 06 | `tests/test_v06_extractors.py` or `tests/test_v05_process_source.py` | `tools/process_source.py` |
| 07 | `tests/test_v06_pending_sources.py` | `tools/process_pending_sources.py` |
| 08 | `tests/test_v06_job_wiki_generator.py` | `src/derived_wiki/summary_loader.py`, `writer.py`, `templates.py` |
| 09 | `tests/test_v06_job_wiki_generator.py` | `src/derived_wiki/job_catalog.py` |
| 10 | `tests/test_v06_job_wiki_generator.py` | `src/derived_wiki/job_wiki_generator.py`, `tools/generate_job_wiki.py` |
| 11 | `tests/test_v06_job_wiki_generator.py` | `tools/generate_derived_wiki.py` |
| 12 | `tests/test_v06_fts_indexing.py` | `src/wiki_indexing/wiki_document_scanner.py`, 기존 FTS module |
| 13 | `tests/test_v06_pending_sources.py` | `tools/process_source.py`, `tools/process_pending_sources.py` |
| 14 | documentation-only; no red test required | `README.md`, `docs/handoff/CURRENT_HANDOFF.md` 등 |

## v0.6 Scope

v0.6에서 구현하는 것:

- ExtractedSource shared model과 SourceExtractionError 계열
- 확장자 기반 extractor registry
- `.txt`, `.md`, `.html`/`.htm`, `.csv`, `.xlsx` extractor
- `tools/process_source.py`의 local file source 경로에 extractor 통합
- `tools/process_pending_sources.py` 일괄 처리 CLI (`--limit`, `--dry-run`, `--retry-errors`, `--max-retry`)
- derived wiki foundation (`summary_loader`, `writer`, `templates`)
- FFXIV job catalog와 alias resolver
- deterministic job wiki generator (`wiki/jobs/<job>.md`)
- `tools/generate_derived_wiki.py --kind jobs` 통합 CLI
- FTS 인덱싱에 `wiki/jobs/*.md` 포함, `wiki_type`/`topic` metadata 추가
- source processing 성공 후 optional derived wiki hook
- v0.6 사용법 README/handoff 문서화

## v0.6 Non-Goals

v0.6에서는 다음을 구현하지 않는다.

- 이미지 OCR
- 스캔 PDF OCR
- PDF table extraction
- DOCX 스타일 보존
- Excel 차트/수식 의미 분석
- Discord command 추가
- scheduler 또는 watcher daemon 추가
- 신규 web crawler 구현
- LLM 기반 derived wiki 요약 생성
- LLM 기반 답변 품질 튜닝
- 새 source type 확장 (v0.5 source type 그대로 유지)
- raids/items/systems derived wiki 구현 (interface만 예약)

PDF, DOCX, 이미지 지원은 이후 v0.6.1 또는 v0.7에서 별도 spec으로 다룬다.

## Source Type Policy

v0.6은 v0.5 source type을 확장하지 않는다. 대신 local file source의 본문 정규화 방식을 확장자별로 분기한다.

| Source Type | v0.5 status | v0.6 변경점 |
|---|---|---|
| text_note | Supported | 변경 없음 |
| markdown_file | Supported | extractor registry 경유로 변환 일관화 |
| plain_text_file | Supported | extractor registry 경유로 변환 일관화 |
| url | Supported (Lodestone routing 포함) | 변경 없음 |
| binary_attachment | Contract only / limited | `.csv`, `.xlsx`, `.html` 같은 표/문서 파일은 file source로 들어와도 일관 처리 |

미지원 확장자는 다음 상태로 기록된다.

```text
status: error
error_stage: extract
error_message: Unsupported source extension: .png
retry_count: retry_count + 1
```

## Entrypoint Policy

v0.5/v05.1과 동일하게 OpenClaw/사용자 normal source 처리 entrypoint는 `tools/process_source.py`다. v0.6에서 추가되는 일괄 처리 entrypoint는 `tools/process_pending_sources.py`다.

Allowed:

```bash
python tools/process_source.py --apply --source-type markdown_file --category patch_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/patch.md"
python tools/process_source.py --apply --source-type binary_attachment --category sheets --local-path "/mnt/d/ffixiv-bot-storage/incoming/bis.xlsx"
python tools/process_pending_sources.py --limit 10
python tools/process_pending_sources.py --retry-errors --max-retry 3
python tools/generate_job_wiki.py --job gunbreaker
python tools/generate_derived_wiki.py --kind jobs
```

Disallowed for normal OpenClaw source processing:

```bash
python tools/ingest_local.py ...
python tools/local_rebuild.py
python tools/status_notification.py
```

수동 디버깅 시 helper module을 직접 호출할 수 있지만, 공식 워크플로 문서는 `process_source.py`와 `process_pending_sources.py`만 권장한다.

## Default Storage Policy

원본 source 저장소:

```text
/mnt/d/ffixiv-bot-storage
```

repo 내부 derived artifacts:

```text
db/ffxiv.sqlite
raw/local_storage/
wiki/source_summaries/
wiki/jobs/                # v0.6 신규
graph/nodes.json
graph/edges.json
```

Notion에는 derived wiki 본문을 저장하지 않는다. Notion에는 source ID, category, local source path, wiki path, graph status, derived wiki status, last error, next action 같은 metadata만 기록한다.

## Status Semantics

v0.5 status 계약을 유지하면서 v0.6에서 다음 stage가 추가된다.

| Stage | Owner | 비고 |
|---|---|---|
| extract | extractor registry | 미지원 확장자, decoding error, parse error 기록 |
| derived_wiki_generate | derived wiki layer | derived wiki 생성 실패 시 source processing 성공과 분리 |

| 상태 키 | 의미 |
|---|---|
| processed | source ingest 성공 |
| wiki_built | source summary 생성 성공 |
| graph_built | graph 생성 성공 |
| derived_wiki_built | derived wiki 생성 성공 (v0.6 신규, optional) |
| error + error_stage=extract | extractor 실패 |
| error + error_stage=derived_wiki_generate | derived wiki 생성 실패 |

## Verification

각 task 완료 후 다음을 실행한다.

Focused v06 tests:

```bash
python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v
```

기존 v0.5/v05.1 regression:

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Docs freshness:

```bash
python scripts/check_docs_freshness.py --all
```

Whitespace:

```bash
git diff --check
```

Final gate:

```bash
python scripts/finish_task.py
```

v0.6 최종 smoke scenarios (구현 계획서 §10 참조):

```bash
# Scenario 1. Markdown source
python tools/process_pending_sources.py --limit 10

# Scenario 2. XLSX source
python tools/process_pending_sources.py --limit 10

# Scenario 3. Unsupported source (.png)
python tools/process_pending_sources.py --limit 10

# Scenario 4. Gunbreaker derived wiki
python tools/generate_job_wiki.py --job gunbreaker

# Scenario 5. Derived wiki FTS search
python tools/search_kb.py "건브레이커"
```

## 권장 구현 순서

```text
v06-1 -> v06-2 -> v06-3 -> v06-4 -> v06-5
  -> v06-6 -> v06-7
  -> v06-8 -> v06-9 -> v06-10 -> v06-11
  -> v06-12 -> v06-13 -> v06-14
```

Batch 단위:

- **Batch A. Extractor foundation**: v06-1, v06-2, v06-3
- **Batch B. Table file support**: v06-4, v06-5
- **Batch C. Source processing automation**: v06-6, v06-7
- **Batch D. Derived wiki foundation**: v06-8, v06-9, v06-10, v06-11
- **Batch E. Search integration and docs**: v06-12, v06-13, v06-14

병렬 가능: v06-3 ↔ v06-4, v06-4 ↔ v06-5, v06-8 ↔ v06-9.

병렬 불가: v06-1 이전 v06-2 금지, v06-2 이전 v06-6 금지, v06-8/v06-9 이전 v06-10 금지, v06-10 이전 v06-12 금지, v06-7/v06-11 이전 v06-13 금지.

## Writing Rules

- 각 plan은 spec의 한 기능 단위에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 코드 변경 task는 handoff 외에도 관련 spec/runbook/ADR 중 하나 이상을 갱신해야 한다.
- 행동 변경은 먼저 red test를 작성한다. `Start by writing the failing regression tests for this task. Run the tests and confirm they fail for the expected reason before implementing the fix.`
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다. `pytest`를 새 표준으로 도입하지 않는다.
- Google Drive를 기본 경로로 되살리지 않는다.
- Notion을 원본 파일 저장소로 사용하지 않는다.
- `process_source.py`에서 Notion API를 직접 호출하지 않는다.
- crawler/scheduler/daemon은 v0.6에 넣지 않는다.
- derived wiki는 source summary에 없는 정보를 추가하지 않는다. LLM 요약은 v0.6 범위가 아니다.

## Completion Criteria

v0.6은 다음 조건을 모두 만족하면 완료로 본다.

- `.txt`, `.md`, `.html`, `.csv`, `.xlsx` extractor가 동작한다.
- extractor registry가 확장자별 extractor를 선택한다.
- 미지원 확장자는 `error_stage=extract` 상태로 기록된다.
- `tools/process_pending_sources.py`가 여러 source를 일괄 처리한다.
- source summary, FTS, graph 생성이 기존처럼 유지된다.
- `wiki/jobs/gunbreaker.md`가 실제 생성된다.
- derived wiki가 source_id와 patch version을 보존한다.
- FTS가 `wiki/jobs/*.md`를 인덱싱하고 `wiki_type`/`topic` metadata를 노출한다.
- 주요 task별 regression test가 있다.
- README/handoff에 v0.6 사용법이 문서화되어 있다.

## Future Work

v0.6 완료 후 다음 버전에서 다룬다.

- v0.6.1 또는 v0.7: PDF parsing, DOCX, 이미지 OCR
- raids/items/systems derived wiki 구현
- action catalog 기반 정밀 추출
- LLM 기반 derived wiki 요약
- vector DB / embedding pipeline
- Notion polling 또는 scheduler 기반 자동화
