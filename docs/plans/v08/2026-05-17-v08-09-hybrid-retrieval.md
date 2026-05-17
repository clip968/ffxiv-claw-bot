# v0.8-09: Graph-aware Hybrid Retrieval

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 9)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Completed 2026-05-17

## Goal

ask pipeline에서 FTS 결과와 graph neighborhood 결과를 병합하는 hybrid retrieval을 추가한다. 기존 FTS-only 동작은 fallback으로 유지한다.

## Scope

- `load_entity_index()` 함수
- `match_query_entities()` 함수 (question → entity ids)
- `retrieve_graph_neighborhood()` 함수 (entity ids → graph neighborhood)
- `merge_retrieval_results()` 함수 (FTS + graph 결과 병합)
- `build_answer_context()` 함수
- ask pipeline에 graph-aware retrieval 연결
- FTS-only fallback 보장

Out of scope:

- ask pipeline 전체 재작성 (additive 변경만)
- Discord command 연결 (v09)
- LLM answer composer (v08 non-goal)
- 복잡한 ranking algorithm (v09)

## Red Test

- File: `tests/test_hybrid_retrieval.py`
- Implementation target: hybrid retrieval module
- Expected red reason: retrieval 함수가 존재하지 않아 `ImportError` 발생.

Contracts fixed by the tests:

- `"건브 7.5 변경점 알려줘"`에서 `job:gunbreaker`, `patch:7_5`가 match된다.
- graph neighborhood가 관련 Fact 또는 SourceDocument를 반환한다.
- FTS result와 graph result가 병합된다.
- 중복 source가 제거된다.
- graph 결과가 없어도 FTS-only fallback이 동작한다.
- FTS 결과가 없어도 graph-only context가 구성된다.

## Checklist

- [x] hybrid retrieval 모듈 생성
  - [x] `load_entity_index(graph_dir)` 구현
  - [x] `match_query_entities(question, entity_index)` 구현
  - [x] `retrieve_graph_neighborhood(conn, entity_ids, depth=2)` 구현
  - [x] `merge_retrieval_results(fts_results, graph_results, limit=8)` 구현
  - [x] `build_answer_context(merged_results)` 구현
- [x] ask pipeline 수정
  - [x] graph-aware retrieval 연결
  - [x] FTS-only fallback 유지
- [x] Ranking policy 구현
  - [x] FTS result: original FTS score
  - [x] graph result: base 1.0
  - [x] exact entity match boost: query entity matching 기반
  - [x] Fact-backed source boost: graph result score 1.4
  - [ ] derived wiki page boost: v09 ranking 확장 후보
  - [ ] patch match boost: v09 ranking 확장 후보
  - [x] source_id 중복 제거
  - [x] 최종 context 최대 8개
- [x] `tests/test_hybrid_retrieval.py` 생성
  - [x] `test_entity_match_korean_query`
  - [x] `test_graph_neighborhood_returns_facts`
  - [x] `test_merge_fts_and_graph`
  - [x] `test_dedup_sources`
  - [x] `test_fts_only_fallback`
  - [x] `test_graph_only_context`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환
- [x] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_hybrid_retrieval -v
```

## Key Decisions

- Query flow: question → match_query_entities → retrieve_graph_neighborhood → retrieve_fts_results → merge_retrieval_results → build_answer_context → existing answer generator.
- Graph neighborhood: 1-2 hop으로 제한. 우선순위: Fact → SourceDocument → WikiPage → Skill/Job/Patch → derived wiki.
- Merge policy: FTS top 5 + graph top 5 → source_id/page_id 중복 제거 → 최대 8개 context.
- graph retrieval이 실패해도 기존 FTS-only behavior는 fallback으로 남아 있어야 한다.
- v08에서는 단순 ranking으로 충분하다. 복잡한 ranking은 v09로 넘긴다.

## Implementation Notes

- v08-06의 entity_index.json을 사용하여 query entity matching을 수행한다.
- v08-04의 graph storage helper(`get_neighbors`)를 사용한다.
- 기존 ask module(`tools/ask.py` 또는 equivalent)을 확인하고 additive하게 수정한다.
- 기존 FTS 테스트가 깨지지 않아야 한다.

## Agent Prompt

```text
v08 Task 9를 수행한다.
ask pipeline에 graph-aware hybrid retrieval을 추가한다.
질문에서 entity를 match하고, graph neighborhood를 조회한 뒤, 기존 FTS result와 병합한다.
graph result가 없으면 기존 FTS-only fallback이 동작해야 한다.
`건브 7.5 변경점 알려줘` 질문에서 job:gunbreaker와 patch:7_5가 match되는 테스트를 추가한다.
```
