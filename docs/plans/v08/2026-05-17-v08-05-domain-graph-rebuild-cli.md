# v0.8-05: Domain Graph Rebuild CLI

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 5)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Pending

## Goal

source summaries를 읽어 FFXIV domain graph를 rebuild하는 `tools/rebuild_domain_graph.py` CLI를 구현한다. entity extraction → relation/fact extraction → graph upsert → export → report 전체 파이프라인을 실행한다.

## Scope

- `tools/rebuild_domain_graph.py` CLI 생성
- CLI 옵션: `--db-path`, `--wiki-root`, `--entities-dir`, `--graph-dir`, `--dry-run`, `--source-id`, `--reset-domain-graph`, `--verbose`
- source summary 로드
- entity registry 로드
- entity extraction → relation/fact extraction → node/edge upsert
- graph export 호출 (v08-06)
- graph report 호출 (v08-07)
- idempotent rebuild

Out of scope:

- graph export 로직 자체 (v08-06 책임)
- graph report 로직 자체 (v08-07 책임)
- derived wiki 생성 (v08-08 책임)

## Red Test

- File: `tests/test_domain_graph_rebuild.py`
- Implementation target: `tools/rebuild_domain_graph.py`
- Expected red reason: `tools/rebuild_domain_graph.py`가 존재하지 않아 import 실패.

Contracts fixed by the tests:

- fixture source summary에서 domain nodes가 생성된다.
- fixture source summary에서 MENTIONS edge가 생성된다.
- patch + skill + trigger에서 Fact가 생성된다.
- rebuild를 두 번 실행해도 node/edge 수가 증가하지 않는다.
- `--dry-run`은 DB를 변경하지 않는다.
- `--source-id`는 특정 source만 처리한다.
- `--reset-domain-graph`는 provenance graph를 보존한다.

## Checklist

- [ ] `tools/rebuild_domain_graph.py` 생성
  - [ ] argparse CLI 설정
  - [ ] DB 연결
  - [ ] graph schema/migration 확인
  - [ ] entity registry 로드
  - [ ] source summaries 로드
  - [ ] SourceDocument node upsert
  - [ ] WikiPage node upsert
  - [ ] Job/Patch/Skill node upsert (registry 기반)
  - [ ] source summary별 entity extraction
  - [ ] MENTIONS edge 생성
  - [ ] registry 기반 HAS_SKILL edge 생성
  - [ ] relation/fact extraction
  - [ ] Fact node upsert
  - [ ] Fact 관련 edge upsert
  - [ ] graph export 호출
  - [ ] graph report 호출
  - [ ] `--dry-run` 지원
  - [ ] `--source-id` 필터 지원
  - [ ] `--reset-domain-graph` 지원
  - [ ] `--verbose` 지원
- [ ] `tests/test_domain_graph_rebuild.py` 갱신
  - [ ] `test_rebuild_creates_domain_nodes`
  - [ ] `test_rebuild_creates_mentions_edges`
  - [ ] `test_rebuild_creates_fact_with_trigger`
  - [ ] `test_rebuild_idempotent`
  - [ ] `test_dry_run_no_db_change`
  - [ ] `test_source_id_filter`
  - [ ] `test_reset_preserves_provenance`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_domain_graph_rebuild -v
python tools/rebuild_domain_graph.py --dry-run --verbose
```

## Key Decisions

- rebuild는 repo root에서 실행한다.
- source summary 로드 우선순위: DB source_id + wiki page → file content → DB body fallback.
- `--reset-domain-graph`는 domain type node/edge만 삭제. provenance graph(SourceDocument, WikiPage, SOURCE_OF)는 보존.
- 삭제 대상 type: Job, Patch, Skill, Item, Encounter, GearSet, Fact.
- 삭제 대상 relation: MENTIONS, HAS_SKILL, SUPPORTS, VALID_IN_PATCH, AFFECTS_JOB, AFFECTS_SKILL, RELATED_TO, DERIVED_FROM.

## Implementation Notes

- v08-01~04에 의존한다 (registry, extractor, relation extractor, upsert helper).
- 테스트는 fixture source summary와 tmp DB를 사용한다.
- rebuild CLI는 v08-06 export와 v08-07 report를 마지막에 호출한다. 해당 모듈이 아직 없으면 skip하거나 stub으로 둔다.

## Agent Prompt

```text
v08 Task 5를 수행한다.
`tools/rebuild_domain_graph.py` CLI를 구현한다.
source summaries를 읽고 entity extraction, relation/fact extraction, graph upsert를 수행한다.
옵션은 --db-path, --wiki-root, --entities-dir, --graph-dir, --dry-run, --source-id, --reset-domain-graph, --verbose를 지원한다.
rebuild는 idempotent해야 하고 dry-run은 DB를 변경하지 않아야 한다.
```
