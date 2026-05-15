# v0.5 Feature Plans

v0.5 Source Processing Pipeline의 feature별 plan을 보관한다.

v0.5의 목표는 OpenClaw가 source 처리 요청을 받을 때 여러 tool을 직접 이어 붙이지 않고, 하나의 안정된 source processing workflow로 처리할 수 있게 만드는 것이다.

기본 운영 경로는 /mnt/d/ffixiv-bot-storage 기반 Local Storage와 OpenClaw Notion direct control이다. Google Drive 기반 sync는 기본 경로가 아니며, Notion은 원본 파일 저장소가 아니라 control/status/index layer로만 사용한다.

v0.5는 완전 자동 크롤러가 아니다. 사용자가 URL, 로컬 파일 경로, 텍스트 본문 같은 source를 제공했을 때 다음 흐름을 안정화하는 단계다.

    사용자 요청
    -> OpenClaw Source Processing Skill
    -> tools/process_source.py
    -> ingest
    -> wiki/FTS/graph rebuild
    -> Notion update payload 생성
    -> OpenClaw가 Notion 상태 갱신

## Master Plan

docs/plans/v05/2026-05-16-v05-source-processing-pipeline.md에서 전체 진행 상태를 추적한다.

구현 계약은 docs/specs/0004-v05-source-processing-pipeline.md를 따른다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 01 | 2026-05-16-v05-01-spec-and-plan.md | v0.5 통합 spec, master plan, task breakdown 고정 | **Completed** 2026-05-16 |
| 02 | 2026-05-16-v05-02-openclaw-skill-draft.md | OpenClaw Source Processing Skill 규칙 작성 | **Completed** 2026-05-16 |
| 03 | 2026-05-16-v05-03-process-source-skeleton.md | tools/process_source.py CLI skeleton, validation, dry-run, JSON output 구현 | **Completed** 2026-05-16 |
| 04 | 2026-05-16-v05-04-local-source-integration.md | text_note, markdown_file, plain_text_file을 Local Storage ingest로 연결 | Pending |
| 05 | 2026-05-16-v05-05-url-integration.md | 사용자가 제공한 단일 URL을 fetch하고 Local Storage ingest로 연결 | Pending |
| 06 | 2026-05-16-v05-06-rebuild-integration.md | ingest 이후 wiki, FTS, graph rebuild를 process_source.py에 연결 | Pending |
| 07 | 2026-05-16-v05-07-notion-payload-integration.md | 처리 결과를 안전한 Notion update payload로 변환 | Pending |
| 08 | 2026-05-16-v05-08-tests-and-runbook.md | 테스트, runbook, handoff, workflow 문서 정리 | Pending |

## Red Test Map

The active v0.5 plan files name the red test file for each implementation slice.

| Plan | Red test | Implementation target |
|---|---|---|
| 03 | tests/test_v05_process_source.py | tools/process_source.py |
| 04 | tests/test_v05_process_source.py | tools/process_source.py, tools/ingest_local.py |
| 05 | tests/test_v05_fetch_url.py, tests/test_v05_process_source.py | tools/fetch_url.py, tools/process_source.py |
| 06 | tests/test_v05_process_source.py | tools/process_source.py, tools/local_rebuild.py, tools/compile_wiki.py, tools/build_graph.py |
| 07 | tests/test_v05_process_source.py, tests/test_v04_status_notification.py | tools/process_source.py, tools/status_notification.py |
| 08 | all v0.5 tests | docs/runbooks/process-source.md, docs/handoff/CURRENT_HANDOFF.md, docs/WORKFLOW.md, agent.md, CLAUDE.md |

## v0.5 Scope

v0.5에서 구현하는 것:

- OpenClaw source processing skill contract
- tools/process_source.py
- text_note ingest
- markdown_file ingest
- plain_text_file ingest
- 사용자가 제공한 단일 URL fetch
- URL content를 Local Storage source로 저장
- ingest 이후 wiki summary 생성
- FTS rebuild
- graph build
- Notion update payload 생성
- JSON output contract
- dry-run behavior
- partial/error/skipped status handling
- process-source runbook
- handoff update

## v0.5 Non-Goals

v0.5에서는 다음을 구현하지 않는다.

- Notion DB polling loop
- Notion Status = New 항목 자동 감시
- allowlist crawler
- arbitrary web crawling
- sitemap crawling
- scheduler 또는 daemon
- Discord slash command runtime
- vector DB
- embedding pipeline
- Google Drive 기본 경로 복구
- Notion을 원본 파일 저장소로 사용하는 구조
- PDF/OCR 기반 binary attachment 자동 추출

위 항목은 v0.6 Automation Loop 이후의 범위다.

## Source Type Policy

v0.5에서 지원하는 source type은 다음이다.

| Source Type | Status | Input |
|---|---|---|
| text_note | Required | --body |
| markdown_file | Required | --local-path |
| plain_text_file | Required | --local-path |
| url | Required | --url |
| binary_attachment | Contract only / Limited | --local-path |

binary_attachment는 기존 ingest path와 충돌하지 않도록 contract는 유지할 수 있지만, v0.5의 필수 완료 범위는 아니다.

## Default Storage Policy

원본 source 저장소:

    /mnt/d/ffixiv-bot-storage

repo 내부 derived artifacts:

    db/ffxiv.sqlite
    raw/local_storage/
    wiki/source_summaries/
    graph/nodes.json
    graph/edges.json

Notion에는 파일 원문을 저장하지 않는다. Notion에는 source ID, category, local source path, wiki path, graph status, last error, next action 같은 metadata만 기록한다.

## Expected CLI

v0.5 완료 후 기본 entrypoint는 다음이다.

    python tools/process_source.py \
      --apply \
      --source-type text_note \
      --category personal_notes \
      --title "P12S mitigation note" \
      --body "Use Reprisal before raidwide."

URL 처리:

    python tools/process_source.py \
      --apply \
      --source-type url \
      --category patch_notes \
      --url "https://example.com/ffxiv/patch-note"

로컬 markdown 파일 처리:

    python tools/process_source.py \
      --apply \
      --source-type markdown_file \
      --category raid_guides \
      --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"

dry-run:

    python tools/process_source.py \
      --dry-run \
      --source-type text_note \
      --category personal_notes \
      --title "Dry run note" \
      --body "This should not be persisted."

## Status Semantics

| Internal Status | Meaning |
|---|---|
| ok | ingest, wiki, FTS, graph, Notion payload generation all succeeded |
| partial | source was saved, but one or more downstream steps failed |
| error | source processing failed before a usable source was produced |
| skipped | dry-run, duplicate, or policy-based skip |

## Notion Status Mapping

| Internal Result | Notion Status | Graph Status |
|---|---|---|
| ok + graph built | Graph Built | Built |
| ok + graph pending | Indexed | Pending |
| partial + graph failed | Indexed or Partial | Failed |
| error before ingest | Error | Skipped |
| skipped | Skipped | Skipped |

notion_update payload에는 원문 body, raw HTML, attachment bytes, binary data를 넣지 않는다.

## Writing Rules

- 각 plan은 spec의 한 기능 단위에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 Completed YYYY-MM-DD로 변경하고 master plan의 체크리스트도 함께 갱신한다.
- 코드 변경 task는 handoff 외에도 관련 spec/runbook/ADR 중 하나 이상을 갱신해야 한다.
- v0.5 구현은 v0.4 Local Storage + Notion Control 구조를 유지해야 한다.
- plan에 없는 큰 구현 변경이 필요해지면 먼저 plan을 갱신한다.
- documentation-only change는 구현 계획 대신 문서 변경 범위와 검증 기준을 명확히 적는다.
- Google Drive를 기본 경로로 되살리지 않는다.
- Notion을 원본 파일 저장소로 사용하지 않는다.
- crawler/scheduler는 v0.5에 넣지 않는다.

## Verification

각 task 완료 후 최소 다음을 실행한다.

    python -m unittest discover -s tests -p "test_*.py"

가능하면 다음도 실행한다.

    python scripts/check_docs_freshness.py --all

    python scripts/finish_task.py --skip-notion-dry-run

v0.5 최종 smoke test:

    python tools/process_source.py \
      --dry-run \
      --source-type text_note \
      --category personal_notes \
      --title "v05 dry run smoke" \
      --body "This should not be written."

    python tools/process_source.py \
      --apply \
      --source-type text_note \
      --category personal_notes \
      --title "v05 apply smoke" \
      --body "This should be searchable."

검색 확인:

    python tools/search_kb.py "v05 apply smoke"

답변 확인:

    python tools/answer.py "v05 apply smoke" --format text

## Completion Criteria

v0.5는 다음 조건을 만족하면 완료로 본다.

- docs/specs/0004-v05-source-processing-pipeline.md가 존재한다.
- docs/plans/v05/2026-05-16-v05-source-processing-pipeline.md가 존재한다.
- docs/plans/v05/README.md가 현재 feature map을 반영한다.
- docs/skills/ffxiv-source-processing.md가 존재한다.
- tools/process_source.py가 존재한다.
- text_note, markdown_file, plain_text_file, url source를 처리할 수 있다.
- 처리 결과가 Local Storage와 SQLite DB에 반영된다.
- wiki summary, FTS, graph rebuild가 수행된다.
- 최종 결과가 JSON으로 출력된다.
- notion_update payload가 생성된다.
- body/raw HTML/attachment data가 Notion payload에 포함되지 않는다.
- docs/runbooks/process-source.md가 존재한다.
- docs/handoff/CURRENT_HANDOFF.md가 v0.5 완료 상태를 설명한다.
- 전체 테스트가 통과한다.

## Future Work

v0.5 완료 후 v0.6 Automation Loop에서 다음을 진행한다.

- Notion queue schema 고정
- Notion Status = New 항목을 process_source.py request로 변환
- tools/notion_job_mapper.py 구현
- tools/process_notion_queue.py 구현
- config/source_registry.yml 도입
- allowlist 기반 tools/discover_sources.py 구현
- scheduler/cron runbook 작성
- end-to-end automation dry-run 테스트
