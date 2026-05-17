# v0.8 Feature Plans

v0.8 FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval의 feature별 plan을 보관한다.

v0.8의 목표는 현재의 FTS 기반 RAG + 얕은 provenance graph를 FFXIV 도메인 entity graph 기반 hybrid retrieval로 확장하는 것이다.

v0.8 완료 후 목표 파이프라인:

```text
user question
  -> entity matcher (alias → canonical node id)
  -> graph neighborhood retrieval (1-2 hop)
  -> FTS search
  -> evidence merge/rank
  -> grounded answer context
```

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-17-v08-implementation.md`에 있다.

구현 계약은 `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`를 따른다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 01 | 2026-05-17-v08-01-entity-registry.md | FFXIV entity registry 추가 (jobs, skills, patches) | Completed 2026-05-17 |
| 02 | 2026-05-17-v08-02-entity-extractor.md | source summary에서 entity 추출 | Completed 2026-05-17 |
| 03 | 2026-05-17-v08-03-relation-fact-extractor.md | entity 기반 relation/fact 생성 | Completed 2026-05-17 |
| 04 | 2026-05-17-v08-04-graph-storage-upsert.md | graph node/edge/fact DB upsert helper | Completed 2026-05-17 |
| 05 | 2026-05-17-v08-05-domain-graph-rebuild-cli.md | domain graph rebuild CLI | Completed 2026-05-17 |
| 06 | 2026-05-17-v08-06-graph-export.md | graph export (JSON 산출물) | Completed 2026-05-17 |
| 07 | 2026-05-17-v08-07-graph-report.md | GRAPH_REPORT.md 생성 | Completed 2026-05-17 |
| 08 | 2026-05-17-v08-08-derived-wiki-generator.md | graph 기반 derived wiki 생성 | Pending |
| 09 | 2026-05-17-v08-09-hybrid-retrieval.md | graph-aware hybrid retrieval | Pending |
| 10 | 2026-05-17-v08-10-e2e-smoke-test.md | end-to-end smoke test | Pending |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 01 | `tests/test_entity_extractor.py` | `data/ffxiv_entities/*.json`, entity registry loader |
| 02 | `tests/test_entity_extractor.py` | entity extractor (rule-based) |
| 03 | `tests/test_relation_extractor.py` | relation/fact extractor |
| 04 | `tests/test_domain_graph_rebuild.py` | graph upsert helpers |
| 05 | `tests/test_domain_graph_rebuild.py` | `tools/rebuild_domain_graph.py` |
| 06 | `tests/test_graph_report.py` | graph export (JSON) |
| 07 | `tests/test_graph_report.py` | `graph/GRAPH_REPORT.md` |
| 08 | `tests/test_derived_wiki.py` | `tools/generate_derived_wiki.py` |
| 09 | `tests/test_hybrid_retrieval.py` | hybrid retrieval helpers |
| 10 | `tests/test_v08_e2e.py` | E2E integration |

## v0.8 Scope

v0.8에서 구현하는 것:

- `data/ffxiv_entities/` entity registry (jobs, skills, patches)
- rule-based entity extractor (alias → canonical node id)
- relation/fact extractor (MENTIONS, HAS_SKILL, SUPPORTS, VALID_IN_PATCH, AFFECTS_JOB, AFFECTS_SKILL)
- graph storage/upsert helper (idempotent node/edge/fact upsert)
- `tools/rebuild_domain_graph.py` CLI
- graph export (`graph/domain_graph.json`, `graph/entity_index.json`, `graph/nodes.json`, `graph/edges.json`)
- `graph/GRAPH_REPORT.md` 생성
- derived wiki 생성 (`wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`)
- ask pipeline에 graph-aware hybrid retrieval 추가
- end-to-end smoke test

## v0.8 Non-Goals

v0.8에서는 다음을 구현하지 않는다.

- 공식 FFXIV 패치노트 실시간 크롤러
- Discord command 전체 개편
- BIS, opener, rotation 전체 자동 생성
- 모든 FFXIV 아이템/음식/마테리아 ontology 완성
- LLM 기반 extractor의 production-grade 완성
- 복잡한 graph visualization HTML 구현
- community detection 기반 Graphify clone 구현
- graph DB 도입
- vector DB 도입

## Entrypoint Policy

v0.8에서 추가되는 사용자 대면 entrypoint:

```bash
python tools/rebuild_domain_graph.py --db-path db/ffxiv.sqlite --wiki-root wiki --entities-dir data/ffxiv_entities --graph-dir graph
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/rebuild_domain_graph.py --source-id local_a5f56616236f --verbose
python tools/generate_derived_wiki.py --db-path db/ffxiv.sqlite --wiki-root wiki --graph-dir graph --types jobs,patches,skills
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

기존 v0.7 entrypoint는 변경하지 않는다:

```bash
python tools/ask.py <question> --format json
python tools/ask.py <question> --format text
python tools/search_kb.py <query>
python tools/answer.py <question>
```

## Verification

각 task 완료 후 다음을 실행한다.

v08 focused tests:

```bash
python -m unittest tests.test_entity_extractor -v
python -m unittest tests.test_relation_extractor -v
python -m unittest tests.test_domain_graph_rebuild -v
python -m unittest tests.test_derived_wiki -v
python -m unittest tests.test_graph_report -v
python -m unittest tests.test_hybrid_retrieval -v
python -m unittest tests.test_v08_e2e -v
```

기존 v0.7 regression:

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
v08-01 -> v08-02 -> v08-03 -> v08-04 -> v08-05
  -> v08-06 -> v08-07
  -> v08-08
  -> v08-09
  -> v08-10
```

Batch 단위:

- **Batch A. Entity foundation**: v08-01, v08-02, v08-03
- **Batch B. Graph storage and rebuild**: v08-04, v08-05
- **Batch C. Export and report**: v08-06, v08-07
- **Batch D. Derived wiki**: v08-08
- **Batch E. Hybrid retrieval**: v08-09
- **Batch F. E2E verification**: v08-10

병렬 가능: v08-06 ↔ v08-07 (export와 report는 동시 진행 가능).

병렬 불가: v08-01 이전 v08-02 금지, v08-02 이전 v08-03 금지, v08-03 이전 v08-04 금지, v08-04 이전 v08-05 금지, v08-05 이전 v08-06~08 금지, v08-08 이전 v08-09 금지, v08-09 이전 v08-10 금지.

## Writing Rules

- 각 plan은 master plan의 한 task에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 행동 변경은 먼저 red test를 작성한다.
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다.
- LLM API를 호출하지 않는다.
- 기존 `tools/ask.py`, `tools/search_kb.py`, `tools/answer.py` 호환성을 유지한다.

## Completion Criteria

v0.8은 다음 조건을 모두 만족하면 완료로 본다.

- `graph_nodes`에 `Job`, `Patch`, `Skill`, `Fact` node가 생성된다.
- `graph_edges`에 `MENTIONS`, `HAS_SKILL`, `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL`, `DERIVED_FROM` edge가 생성된다.
- domain graph rebuild가 idempotent하다.
- `graph/nodes.json`, `graph/edges.json`, `graph/domain_graph.json`, `graph/entity_index.json` 생성.
- `graph/GRAPH_REPORT.md`에 node count, edge count, top entities, quality warnings 포함.
- `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md` 최소 1개 이상 생성.
- 각 derived wiki에 related sources 포함.
- 질문에서 entity를 match하고 graph neighborhood retrieval을 수행한다.
- graph result와 FTS result를 병합한다.
- graph result가 없어도 FTS-only fallback이 작동한다.
- 기존 v07 테스트 전체 통과.
- full test suite 통과.

## Future Work

v0.8 완료 후 다음 버전에서 다룬다.

- v0.9: Discord command에서 graph-aware answer 노출
- v1.0: graph path explanation, source quality scoring
- v1.1: 공식 패치노트 crawler, patch freshness policy
- v1.2: item / gearset / food / materia ontology 확장
- v1.3: LLM-assisted relation extraction, graph visualization
