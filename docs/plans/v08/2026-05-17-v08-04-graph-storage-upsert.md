# v0.8-04: Graph Storage / Upsert Helper

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 4)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Pending

## Goal

domain graph node/edge/fact를 SQLite `graph_nodes`, `graph_edges` 테이블에 안전하고 idempotent하게 저장하는 upsert helper를 구현한다. 기존 provenance graph(SourceDocument → SOURCE_OF → WikiPage)는 반드시 보존한다.

## Scope

- 기존 `graph_nodes`, `graph_edges` schema 확인
- 필요 시 additive migration (ALTER TABLE ADD COLUMN)
- 권장 index 생성
- `upsert_node()`, `upsert_edge()`, `upsert_fact()` 함수
- `get_neighbors()`, `get_nodes_by_type()`, `get_edges_by_relation()` 조회 함수
- deterministic id 생성

Out of scope:

- rebuild CLI (v08-05 책임)
- graph export (v08-06 책임)
- destructive migration 금지

## Red Test

- File: `tests/test_domain_graph_rebuild.py`
- Implementation target: graph upsert helper module
- Expected red reason: upsert helper 모듈이 존재하지 않아 `ImportError` 발생.

Contracts fixed by the tests:

- 같은 node를 두 번 upsert해도 row가 하나만 존재한다.
- 같은 edge를 두 번 upsert해도 row가 하나만 존재한다.
- Fact id가 같은 입력에서 항상 동일하다.
- provenance graph node(SourceDocument, WikiPage)가 삭제되지 않는다.

## Checklist

- [ ] 기존 DB schema 확인
  - [ ] `sqlite3 db/ffxiv.sqlite ".schema graph_nodes"`
  - [ ] `sqlite3 db/ffxiv.sqlite ".schema graph_edges"`
- [ ] graph storage helper 모듈 생성
  - [ ] additive migration 함수 (필요한 컬럼만 추가)
  - [ ] index 생성 함수
  - [ ] `upsert_node(conn, node)` 구현
  - [ ] `upsert_edge(conn, edge)` 구현
  - [ ] `upsert_fact(conn, fact)` 구현
  - [ ] `get_neighbors(conn, node_id, depth=1)` 구현
  - [ ] `get_nodes_by_type(conn, node_type)` 구현
  - [ ] `get_edges_by_relation(conn, relation_type)` 구현
- [ ] `tests/test_domain_graph_rebuild.py` 생성 (storage 중심 red tests)
  - [ ] `test_upsert_node_idempotent`
  - [ ] `test_upsert_edge_idempotent`
  - [ ] `test_fact_id_deterministic`
  - [ ] `test_provenance_graph_preserved`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_domain_graph_rebuild -v
```

## Key Decisions

- `graph_nodes` 권장 컬럼: id, type, name, canonical_name, aliases_json, properties_json, created_at, updated_at.
- `graph_edges` 권장 컬럼: id, source_node_id, target_node_id, relation_type, properties_json, source_id, confidence, created_at, updated_at.
- destructive migration은 금지. 기존 컬럼은 유지하고 필요한 컬럼만 `ALTER TABLE ADD COLUMN`.
- node id 규칙: `src:<source_id>`, `page:<slug>`, `job:<slug>`, `patch:<slug>`, `skill:<slug>`, `fact:<hash>`.
- edge id 규칙: `edge:<hash(source_node_id, relation_type, target_node_id, source_id)>`.
- fact id 규칙: `fact:<hash(source_id + subject_node_id + relation + object_node_id + normalized_fact_text)>`.

## Implementation Notes

- v08-03 relation extractor의 출력을 이 helper로 DB에 저장한다.
- 테스트는 in-memory SQLite 또는 tmp file DB를 사용한다.
- 기존 `SOURCE_OF` edge는 삭제하면 안 된다.
- v08-05 rebuild CLI가 이 helper를 호출한다.

## Agent Prompt

```text
v08 Task 4를 수행한다.
graph_nodes, graph_edges에 domain graph를 저장하는 storage/upsert helper를 구현한다.
기존 schema를 확인하고 destructive migration 없이 필요한 컬럼과 index만 추가한다.
node/edge/fact id는 deterministic해야 한다.
같은 입력을 여러 번 upsert해도 중복 row가 생기면 안 된다.
기존 SourceDocument -> SOURCE_OF -> WikiPage provenance graph는 보존한다.
```
