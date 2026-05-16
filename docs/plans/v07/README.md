# v0.7 Feature Plans

v0.7 Grounded Ask Pipeline의 feature별 plan을 보관한다.

v0.7의 목표는 v06까지 구축된 지식 베이스(wiki/source_summaries, wiki/jobs, wiki_fts, graph)를 실제 질문 응답에 사용할 수 있는 ask pipeline으로 연결하는 것이다.

v0.7 완료 후 목표 파이프라인:

```text
user question
  -> query parser (normalize, job detect, patch parse, intent detect)
  -> retrieval planner
  -> filtered FTS search (job wiki first, source summary fallback)
  -> context pack builder
  -> grounded answer composer
  -> tools/ask.py output (JSON / text)
```

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-17-v07-implementation-plan.md`에 있다.

구현 계약은 `docs/specs/0007-v07-grounded-ask-pipeline.md`를 따른다.

부모 pipeline 계약은 v0.6 spec (`docs/specs/0005- v06-Multi-format-Source-Processing.md`)를 그대로 유지한다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 01 | 2026-05-17-v07-01-query-model-and-normalization.md | ParsedQuery 모델과 normalization helpers 추가 | Completed 2026-05-17 |
| 02 | 2026-05-17-v07-02-job-detector.md | 사용자 질문에서 FFXIV 직업 감지 | Completed 2026-05-17 |
| 03 | 2026-05-17-v07-03-patch-range-parser.md | 패치 버전 범위 파싱 | Completed 2026-05-17 |
| 04 | 2026-05-17-v07-04-intent-detector.md | 결정론적 intent 분류 | Pending |
| 05 | 2026-05-17-v07-05-query-parser-integration.md | query parser 통합 | Pending |
| 06 | 2026-05-17-v07-06-retrieval-models-and-planner.md | retrieval plan 모델과 planner 구현 | Pending |
| 07 | 2026-05-17-v07-07-filtered-fts-search.md | wiki_type/topic 필터링 FTS 검색 | Pending |
| 08 | 2026-05-17-v07-08-execute-retrieval-plan.md | retrieval plan 실행 (primary/fallback) | Pending |
| 09 | 2026-05-17-v07-09-context-pack-builder.md | 검색 결과를 AskContextPack으로 변환 | Pending |
| 10 | 2026-05-17-v07-10-citation-and-confidence.md | citation/confidence helper 구현 | Pending |
| 11 | 2026-05-17-v07-11-grounded-answer-composer.md | 결정론적 grounded answer 작성기 | Pending |
| 12 | 2026-05-17-v07-12-ask-cli-skeleton.md | tools/ask.py CLI skeleton과 JSON contract | Pending |
| 13 | 2026-05-17-v07-13-text-output-mode.md | tools/ask.py text 출력 모드 | Pending |
| 14 | 2026-05-17-v07-14-job-wiki-first-e2e.md | job wiki 우선 사용 E2E 테스트 | Pending |
| 15 | 2026-05-17-v07-15-source-summary-fallback-e2e.md | source summary fallback E2E 테스트 | Pending |
| 16 | 2026-05-17-v07-16-runbook-documentation.md | runbook 및 문서 작성 | Pending |
| 17 | 2026-05-17-v07-17-full-regression-verification.md | 전체 회귀 검증 | Pending |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 01 | `tests/test_v07_query_parser.py` | `src/query/models.py`, `src/query/normalize.py`, `src/query/__init__.py` |
| 02 | `tests/test_v07_query_parser.py` | `src/query/job_detector.py` |
| 03 | `tests/test_v07_query_parser.py` | `src/query/patch_parser.py` |
| 04 | `tests/test_v07_query_parser.py` | `src/query/intent_detector.py` |
| 05 | `tests/test_v07_query_parser.py` | `src/query/parser.py` |
| 06 | `tests/test_v07_retrieval.py` | `src/retrieval/models.py`, `src/retrieval/planner.py` |
| 07 | `tests/test_v07_retrieval.py` | `src/retrieval/fts_search.py` |
| 08 | `tests/test_v07_retrieval.py` | `src/retrieval/context_builder.py` |
| 09 | `tests/test_v07_context_builder.py` | `src/retrieval/context_builder.py`, `src/retrieval/models.py` |
| 10 | `tests/test_v07_answer_composer.py` | `src/answering/citations.py`, `src/answering/confidence.py` |
| 11 | `tests/test_v07_answer_composer.py` | `src/answering/composer.py` |
| 12 | `tests/test_v07_ask_cli.py` | `tools/ask.py` |
| 13 | `tests/test_v07_ask_cli.py` | `tools/ask.py` |
| 14 | `tests/test_v07_ask_cli.py` | E2E integration |
| 15 | `tests/test_v07_ask_cli.py` | E2E integration |
| 16 | documentation-only; no red test required | `docs/runbooks/ask.md`, `docs/handoff/CURRENT_HANDOFF.md` |
| 17 | verification-only; no new tests | full test suite run |

## v0.7 Scope

v0.7에서 구현하는 것:

- `ParsedQuery` 모델과 query normalization
- FFXIV 직업 감지 (v06 job catalog 재사용)
- 패치 버전 범위 파싱
- 결정론적 intent 감지
- query parser 통합
- retrieval plan 모델과 planner
- wiki_type/topic 필터링 FTS 검색
- retrieval plan 실행 (primary → fallback)
- context pack builder (file content read + source_id 추출)
- citation/confidence helpers
- deterministic grounded answer composer
- `tools/ask.py` CLI (JSON + text output)
- job wiki first E2E 검증
- source summary fallback E2E 검증
- 운영 runbook 문서화

## v0.7 Non-Goals

v0.7에서는 다음을 구현하지 않는다.

- Discord slash commands
- automatic official patchnote crawling
- webhook receiver
- scheduled polling
- LLM-generated fluent answers
- vector search / embedding
- raid/item/system derived wiki generation
- expansion-name patch mapping

## Entrypoint Policy

v0.7에서 추가되는 사용자 대면 entrypoint:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json
python tools/ask.py "M4S 공략 찾아줘" --format text
python tools/ask.py "GNB patch history" --debug
```

기존 v0.5/v0.6 entrypoint는 변경하지 않는다:

```bash
python tools/search_kb.py <query>
python tools/answer.py <question>
```

## Verification

각 task 완료 후 다음을 실행한다.

v07 focused tests:

```bash
python -m unittest tests.test_v07_query_parser -v
python -m unittest tests.test_v07_retrieval -v
python -m unittest tests.test_v07_context_builder -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v
```

기존 v0.6 regression:

```bash
python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 권장 구현 순서

```text
v07-01 -> v07-02 -> v07-03 -> v07-04 -> v07-05
  -> v07-06 -> v07-07 -> v07-08
  -> v07-09 -> v07-10 -> v07-11
  -> v07-12 -> v07-13 -> v07-14 -> v07-15
  -> v07-16 -> v07-17
```

Batch 단위:

- **Batch A. Query parsing foundation**: v07-01, v07-02, v07-03, v07-04, v07-05
- **Batch B. Retrieval planning and filtered FTS**: v07-06, v07-07, v07-08
- **Batch C. Context pack and answer composer**: v07-09, v07-10, v07-11
- **Batch D. tools/ask.py CLI**: v07-12, v07-13, v07-14, v07-15
- **Batch E. Documentation and final verification**: v07-16, v07-17

병렬 가능: v07-02 ↔ v07-03, v07-03 ↔ v07-04, v07-10 ↔ v07-11.

병렬 불가: v07-01 이전 v07-02~05 금지, v07-05 이전 v07-06 금지, v07-06 이전 v07-07 금지, v07-07 이전 v07-08 금지, v07-08 이전 v07-09 금지, v07-11 이전 v07-12 금지, v07-15 이전 v07-16 금지.

## Writing Rules

- 각 plan은 master plan의 한 task에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 행동 변경은 먼저 red test를 작성한다.
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다.
- LLM API를 호출하지 않는다.
- 기존 `tools/search_kb.py`, `tools/answer.py` 호환성을 유지한다.

## Completion Criteria

v0.7은 다음 조건을 모두 만족하면 완료로 본다.

- `tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json`이 valid JSON을 반환한다.
- job wiki가 있으면 primary context로 사용된다.
- job wiki가 없으면 source_summary fallback이 동작한다.
- answer에 source path 또는 source_id가 포함된다.
- context 없는 질문에 hallucination이 없다.
- 기존 v06 테스트 전체 통과한다.
- full test suite가 통과한다.

## Future Work

v0.7 완료 후 다음 버전에서 다룬다.

- v0.8: Discord Adapter (/ask, /ingest, /status)
- v0.9: Official Patchnote Watcher
- v1.0: More Derived Wiki (raids, items, systems)
- v1.1: LLM Answer Composer
