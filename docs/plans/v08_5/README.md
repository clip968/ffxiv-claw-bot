# v0.8.5 Feature Plans

v0.8.5 Managed Wiki Knowledge Base Activation의 task별 plan을 보관한다.

v0.8.5는 새 기능 확장이 아니다. v08에서 구현된 domain graph, graph-derived wiki, hybrid retrieval 엔진을 실제 `wiki/source_summaries/` 데이터에 적용하고, RAG Wiki로서 사용 가능한 답변 품질과 운영 절차를 확보하는 단계다.

v0.8.5 완료 후 목표 파이프라인:

```text
wiki/source_summaries/
  -> source audit
  -> rebuild_domain_graph.py --reset-domain-graph
  -> db/ffxiv.sqlite graph_nodes / graph_edges population
  -> graph/nodes.json, graph/edges.json, graph/domain_graph.json, graph/entity_index.json
  -> graph/GRAPH_REPORT.md validation
  -> generate_derived_wiki.py
  -> wiki/jobs, wiki/patches, wiki/skills
  -> compile_wiki / SQLite FTS re-index
  -> ask.py topic-based grounded answer
```

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-17-v08_5_implementation.md`에 있다.

구현 계약은 `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`를 따른다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 00 | 2026-05-17-v08_5-00-baseline-verification.md | v08 baseline 테스트 통과 확인 | Completed 2026-05-17 |
| 01 | 2026-05-17-v08_5-01-source-summary-audit.md | source summary audit 및 문서화 | Completed 2026-05-17 |
| 02 | 2026-05-17-v08_5-02-domain-graph-rebuild.md | 실제 source summary 기반 domain graph rebuild | Completed 2026-05-17 |
| 03 | 2026-05-17-v08_5-03-graph-report-validation.md | GRAPH_REPORT.md 생성 및 검증 | Completed 2026-05-17 |
| 04 | 2026-05-17-v08_5-04-derived-wiki-generation.md | graph-derived wiki 실제 생성 | Completed 2026-05-17 |
| 05 | 2026-05-17-v08_5-05-fts-reindexing.md | derived wiki SQLite FTS 재색인 | Completed 2026-05-17 |
| 06 | 2026-05-17-v08_5-06-answer-quality.md | ask 답변 품질 개선 (source dump → 구조화 요약) | Pending |
| 07 | 2026-05-17-v08_5-07-v08_5-tests.md | v08.5 regression tests 추가 | Pending |
| 08 | 2026-05-17-v08_5-08-documentation-runbook.md | documentation 및 runbook 갱신 | Pending |
| 09 | 2026-05-17-v08_5-09-final-verification.md | 최종 regression 및 handoff 갱신 | Pending |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 02 | `tests/test_v08_5_real_graph_population.py` | 실제 source summary 기반 graph population |
| 04 | `tests/test_v08_5_real_derived_wiki.py` | 실제 derived wiki 생성 검증 |
| 05 | `tests/test_v08_5_fts_visibility.py` | generated wiki FTS visibility |
| 06 | `tests/test_v08_5_answer_quality.py` | ask answer 구조화 품질 |

## v0.8.5 Scope

v0.8.5에서 수행하는 것:

- `wiki/source_summaries/` audit 및 FFXIV 데이터 검증
- 실제 source summary 기반 domain graph rebuild
- `GRAPH_REPORT.md` 품질 검증
- `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md` 실제 생성
- generated wiki SQLite FTS 재색인
- `ask.py` 답변 품질 개선 (source dump → 구조화 요약)
- v08.5 regression tests 추가
- README, specs README, runbook, handoff 문서 갱신

## v0.8.5 Non-Goals

v0.8.5에서는 다음을 구현하지 않는다.

- 공식 패치노트 crawler
- polling / scheduler
- Discord slash command 개편
- vector DB
- graph DB
- LLM API 기반 extractor
- GraphRAG community detection
- BIS / raid / item namespace 확장
- ask pipeline 전체 재작성

## Entrypoint Policy

v0.8.5에서 사용하는 entrypoint:

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/generate_derived_wiki.py --verbose
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
```

기존 v0.7/v0.8 entrypoint는 변경하지 않는다:

```bash
python tools/ask.py <question> --format json
python tools/ask.py <question> --format text
python tools/search_kb.py <query>
python tools/answer.py <question>
```

## Verification

각 task 완료 후 다음을 실행한다.

v08.5 focused tests:

```bash
python -m unittest tests.test_v08_5_real_graph_population -v
python -m unittest tests.test_v08_5_real_derived_wiki -v
python -m unittest tests.test_v08_5_fts_visibility -v
python -m unittest tests.test_v08_5_answer_quality -v
```

기존 v08 regression:

```bash
python -m unittest tests.test_v08_e2e -v
python -m unittest tests.test_hybrid_retrieval -v
python -m unittest tests.test_derived_wiki -v
python -m unittest tests.test_graph_report -v
python -m unittest tests.test_domain_graph_rebuild -v
```

기존 v07 regression:

```bash
python -m unittest tests.test_v07_query_parser -v
python -m unittest tests.test_v07_retrieval -v
python -m unittest tests.test_v07_context_builder -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 권장 구현 순서

```text
v08_5-00 -> v08_5-01 -> v08_5-02 -> v08_5-03 -> v08_5-04
  -> v08_5-05 -> v08_5-06 -> v08_5-07
  -> v08_5-08 -> v08_5-09
```

Batch 단위:

- **Batch A. Baseline & audit**: v08_5-00, v08_5-01
- **Batch B. Graph activation**: v08_5-02, v08_5-03
- **Batch C. Wiki activation**: v08_5-04, v08_5-05
- **Batch D. Answer quality**: v08_5-06
- **Batch E. Tests**: v08_5-07
- **Batch F. Documentation & final**: v08_5-08, v08_5-09

병렬 불가: 이 순서를 반드시 지켜야 한다. graph가 비어 있으면 derived wiki 생성도 의미가 없고, derived wiki가 없으면 FTS 검증도 의미가 없다.

## Writing Rules

- 각 plan은 master plan의 한 task에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 행동 변경은 먼저 red test를 작성한다.
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다.
- LLM API를 호출하지 않는다.
- 기존 `tools/ask.py`, `tools/search_kb.py`, `tools/answer.py` 호환성을 유지한다.

## Completion Criteria

v0.8.5는 다음 조건을 모두 만족하면 완료로 본다.

- source summary audit가 문서화된다.
- `graph_nodes`에 `Job`, `Patch`, `Skill`, `Fact` node가 실제 source 기반으로 생성된다.
- `graph_edges`에 `MENTIONS`, `SUPPORTS`, `VALID_IN_PATCH` 등이 생성된다.
- `GRAPH_REPORT.md`에서 모든 node/edge count가 0이 아니다.
- `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`에 최소 1개 이상 생성.
- generated wiki가 SQLite FTS에 색인된다.
- ask 답변이 source dump가 아니라 구조화 요약이다.
- v08.5 regression tests가 통과한다.
- 기존 v06/v07/v08 테스트 전체 통과.
- README, runbook, handoff가 현재 pipeline을 반영한다.
- `finish_task.py`가 통과한다.

## Future Work

v0.8.5 완료 후 다음 버전에서 다룬다.

- BIS namespace
- raid/encounter namespace
- item/gearset namespace
- official patch note source workflow
- stronger relation extraction
- answer evaluation harness
- vector search integration
- graph community summary
