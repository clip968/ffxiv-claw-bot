# CURRENT_HANDOFF

이 문서는 다음 agent/session이 가장 먼저 읽는 현재 상태 대시보드다. 과거 상세 로그는 `docs/handoff/history/`에 보관한다.

## 현재 상태

- Repository: `https://github.com/clip968/ffxiv-claw-bot`
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Branch: `main`
- Last pushed commit: see current `git log --oneline -1` after push
- Current phase: v0.8.5 Managed Wiki Knowledge Base Activation in progress
- Last completed task: v08.5-06 answer quality
- Next task: v08.5-07 v08.5 regression tests consolidation
- Current maintenance task: none

## 먼저 읽을 문서

1. `docs/WORKFLOW.md`
2. `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`
3. `docs/plans/2026-05-17-v08_5_implementation.md`
4. `docs/plans/v08_5/README.md`
5. `docs/plans/v08_5/2026-05-17-v08_5-01-source-summary-audit.md`
6. `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`
7. `tests/test_v08_e2e.py`
8. `src/retrieval/hybrid.py`
9. `tools/ask.py`

## v08.5 진행 상황

완료:

- v08.5-00: baseline verification
- v08.5-01: `docs/reports/2026-05-17-v08_5-source-audit.md` source summary audit
- v08.5-02: real source summary domain graph rebuild, `tests/test_v08_5_real_graph_population.py`; `graph/domain_graph.json` and `graph/entity_index.json` are verified local generated outputs and are ignored by Git
- v08.5-03: `docs/reports/2026-05-17-v08_5-graph-report-review.md` graph report validation
- v08.5-04: graph-derived wiki generation, `tests/test_v08_5_real_derived_wiki.py`; `wiki/jobs`, `wiki/patches`, and `wiki/skills` are verified local generated outputs and are ignored by Git
- v08.5-05: FTS reindexing, `tests/test_v08_5_fts_visibility.py`; `index_wiki_documents()` indexed 38 pages (`source_summary=26`, `job=5`, `patch=3`, `skill=4`) and ask smoke returned generated wiki contexts for `job_gunbreaker`, `patch_7_5`, and `skill_no_mercy`
- v08.5-06: answer quality, `tests/test_v08_5_answer_quality.py`; `compose_answer()` now returns structured `요약`, `관련 항목`, `확인된 내용`, `근거 문서`, `확실도`, `주의` sections instead of raw source dumps

다음 작업:

- v08.5-07: v08.5 regression tests consolidation

아직 하지 말 것:

- v09 이후 기능을 maintainer 요청 없이 앞당기지 않는다.

필요할 때만 과거 상세 로그를 읽는다.

- `docs/handoff/history/2026-05-17-current-handoff.md`

## v08 진행 상황

완료:

- v08-01: `data/ffxiv_entities/` registry JSON and `src/domain_graph/entity_registry.py`
- v08-02: `src/domain_graph/entity_extractor.py` rule-based extractor
- v08-03: `src/domain_graph/relation_extractor.py` relation/fact extractor
- v08-04: `src/domain_graph/storage.py` graph storage/upsert helper
- v08-05: `tools/rebuild_domain_graph.py` domain graph rebuild CLI
- v08-06: `src/domain_graph/export.py` graph JSON export
- v08-07: `src/domain_graph/report.py` graph report
- v08-08: `src/domain_graph/derived_wiki.py` graph-derived wiki generator
- v08-09: `src/retrieval/hybrid.py` graph-aware hybrid retrieval
- v08-10: `tests/test_v08_e2e.py` end-to-end smoke test

다음 작업:

- none; wait for maintainer scope

아직 하지 말 것:

- v09 이후 기능을 maintainer 요청 없이 앞당기지 않는다.

## v07 진행 상황

완료:

- v07-01: `ParsedQuery`, `normalize_query()`, `extract_terms()`
- v07-02: `detect_job()` job detector
- v07-03: `parse_patch_range()` numeric patch range parser
- v07-04: `detect_intent()` deterministic intent detector
- v07-05: `parse_query()` integration
- v07-06: `RetrievalTarget`, `RetrievalPlan`, `build_retrieval_plan()`
- v07-07: `SearchResult`, `search_wiki()` filtered FTS search
- v07-08: `execute_retrieval_plan()` primary/fallback execution
- v07-09: `ContextDocument`, `AskContextPack`, `build_context_pack()`
- v07-10: `collect_sources()`, `confidence_for_context_count()`
- v07-11: `Answer`, `compose_answer()`
- v07-12: `tools/ask.py` JSON CLI skeleton
- v07-13: `tools/ask.py --format text` body-only output
- v07-14: job wiki first E2E
- v07-15: source summary fallback E2E
- v07-16: `docs/runbooks/ask.md` and v07 docs refresh
- v07-17: full regression verification

다음 작업:

- v07 is complete. Start v08 only if the maintainer explicitly opens that scope.

아직 하지 말 것:

- crawling
- polling/scheduler
- Discord slash command
- LLM API 호출
- vector/embedding search
- raid/item/system derived wiki generation

## 현재 검증 스냅샷

v08-10 완료 시점 검증:

```bash
python -m unittest tests.test_entity_extractor -v
python -m unittest tests.test_relation_extractor -v
python -m unittest tests.test_domain_graph_rebuild -v
python -m unittest tests.test_graph_report -v
python -m unittest tests.test_derived_wiki -v
python -m unittest tests.test_hybrid_retrieval -v
python -m unittest tests.test_v08_e2e -v
python -m unittest tests.test_v07_ask_cli tests.test_v07_retrieval -v
python -m unittest tests.test_v06_job_wiki_generator -v
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/rebuild_domain_graph.py --dry-run --verbose
```

결과:

- 9 tests OK
- 7 tests OK
- 11 tests OK
- graph export/report 11 tests OK
- derived wiki 8 tests OK
- hybrid retrieval 7 tests OK
- v08 E2E smoke 6 tests OK
- v07 ask/retrieval regression 17 tests OK
- v06 derived wiki regression 28 tests OK
- graph report CLI returned JSON `status=ok`
- graph-derived wiki dry-run returned JSON `status=ok`
- dry-run JSON returned `status=ok`

이전 v07-17 완료 시점 검증:

v07-17 완료 시점 검증:

```bash
python -m unittest tests.test_v07_query_parser -v
python -m unittest tests.test_v07_retrieval -v
python -m unittest tests.test_v07_context_builder -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v
python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json
```

결과:

- v07 tests: 19 + 10 + 5 + 10 + 7 tests OK
- v06 regression: 32 + 11 + 28 + 7 tests OK
- full unittest discovery: 272 tests OK
- docs freshness: OK
- smoke JSON returned and parsed as valid JSON
- `finish_task.py`: 272 tests OK, docs freshness OK, Notion handoff dry-run OK

## 현재 작업트리 주의사항

v08-10 완료 커밋 전에는 다음 변경이 포함되어야 한다.

```text
src/retrieval/hybrid.py
tests/test_hybrid_retrieval.py
tests/test_v08_e2e.py
docs/runbooks/ask.md
docs/handoff/CURRENT_HANDOFF.md
docs/plans/2026-05-17-v08-implementation.md
docs/plans/v08/2026-05-17-v08-10-e2e-smoke-test.md
docs/plans/v08/README.md
docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md
```

## 운영 원칙

- `docs/`가 source of truth다. Notion은 mirror/index/control layer일 뿐이다.
- `CURRENT_HANDOFF.md`에는 현재 상태만 남긴다.
- 완료된 상세 작업 로그는 `docs/handoff/history/` 또는 각 task plan에 남긴다.
- 코드 변경이 있으면 관련 spec/runbook/plan과 handoff를 함께 갱신한다.
- 기존 사용자 변경을 임의로 revert하지 않는다.

## 다음 agent에게

v08 is complete through task 10. Start new work only from explicit maintainer scope.
