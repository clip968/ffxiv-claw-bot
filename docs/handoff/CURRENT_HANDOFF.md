# CURRENT_HANDOFF

이 문서는 다음 agent/session이 가장 먼저 읽는 현재 상태 대시보드다. 과거 상세 로그는 `docs/handoff/history/`에 보관한다.

## 현재 상태

- Repository: `https://github.com/clip968/ffxiv-claw-bot`
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Branch: `main`
- Last pushed commit: see current `git log --oneline -1` after push
- Current phase: v0.8 Domain Graphify Layer in progress
- Last completed task: v08-02 entity extractor
- Next task: v08-03 relation/fact extractor
- Current maintenance task: none

## 먼저 읽을 문서

1. `docs/WORKFLOW.md`
2. `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`
3. `docs/plans/2026-05-17-v08-implementation.md`
4. `docs/plans/v08/README.md`
5. `docs/plans/v08/2026-05-17-v08-02-entity-extractor.md`
6. `src/domain_graph/entity_registry.py`
7. `src/domain_graph/entity_extractor.py`
8. `tests/test_entity_extractor.py`

필요할 때만 과거 상세 로그를 읽는다.

- `docs/handoff/history/2026-05-17-current-handoff.md`

## v08 진행 상황

완료:

- v08-01: `data/ffxiv_entities/` registry JSON and `src/domain_graph/entity_registry.py`
- v08-02: `src/domain_graph/entity_extractor.py` rule-based extractor

다음 작업:

- v08-03: relation/fact extractor

아직 하지 말 것:

- v08-04 이후 storage/rebuild/retrieval 구현을 v08-03 완료 전 앞당기지 않는다.

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

v08-01 완료 시점 검증:

```bash
python -m unittest tests.test_entity_extractor -v
```

결과:

- 9 tests OK

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

v08-01 완료 커밋 전에는 다음 변경이 포함되어야 한다.

```text
src/domain_graph/__init__.py
src/domain_graph/entity_extractor.py
tests/test_entity_extractor.py
docs/handoff/CURRENT_HANDOFF.md
docs/plans/v08/2026-05-17-v08-02-entity-extractor.md
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

v08 scope is open by maintainer request. Continue with v08-03 after v08-02 is committed and pushed.
