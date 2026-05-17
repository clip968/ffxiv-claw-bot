# CURRENT_HANDOFF

이 문서는 다음 agent/session이 가장 먼저 읽는 현재 상태 대시보드다. 과거 상세 로그는 `docs/handoff/history/`에 보관한다.

## 현재 상태

- Repository: `https://github.com/clip968/ffxiv-claw-bot`
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Branch: `main`
- Last pushed commit: see current `git log --oneline -1` after push
- Current phase: v0.8.5 Managed Wiki Knowledge Base Activation completed
- Last completed task: OpenClaw use-case skill routing and skill-set tests
- Next task: wait for maintainer scope; v09 namespace expansion is only future work
- Current maintenance task: none

## 먼저 읽을 문서

1. `docs/WORKFLOW.md`
2. `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`
3. `docs/plans/2026-05-17-v08_5_implementation.md`
4. `docs/plans/v08_5/README.md`
5. `docs/specs/0010-openclaw-usecase-skill-routing.md`
6. `docs/plans/2026-05-17-openclaw-usecase-skill-set.md`
7. `docs/skills/ffxiv-openclaw-router.md`
8. `docs/plans/v08_5/2026-05-17-v08_5-01-source-summary-audit.md`
9. `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`
10. `tests/test_v08_e2e.py`
11. `src/retrieval/hybrid.py`
12. `tools/ask.py`

## OpenClaw use-case skill routing

완료:

- Added `docs/specs/0010-openclaw-usecase-skill-routing.md` as the OpenClaw use-case routing contract.
- Added `docs/plans/2026-05-17-openclaw-usecase-skill-set.md` as the implementation/verification record.
- Added router skill `docs/skills/ffxiv-openclaw-router.md`.
- Added use-case skills:
  - `docs/skills/ffxiv-ask-kb.md`
  - `docs/skills/ffxiv-kb-refresh.md`
  - `docs/skills/ffxiv-notion-status.md`
- Strengthened existing `docs/skills/ffxiv-source-processing.md` boundaries for KB questions, direct ingest calls, and binary attachments.
- Added machine-readable routing manifest `docs/skills/openclaw-usecase-routing.json`.
- Added `tests/test_openclaw_skills.py` to lock the use-case-to-skill contract.

범위:

- This is repo-side skill/routing insurance for common OpenClaw requests.
- It does not implement an OpenClaw runtime adapter. A future runtime must explicitly load `docs/skills/openclaw-usecase-routing.json` or the skill docs before executing requests.
- Latest/live web information without a provided source remains unsupported; ask for a source first.

검증:

- `python -m unittest tests.test_openclaw_skills -v`: 6 tests OK
- `python -m unittest tests.test_v05_process_source tests.test_v04_openclaw_notion_control tests.test_v04_status_notification -v`: 39 tests OK
- `git diff --check`: OK
- `python scripts/check_docs_freshness.py --all`: OK
- `python scripts/finish_task.py`: 361 tests OK, docs freshness OK, Notion handoff dry-run OK

## v08.5 진행 상황

완료:

- v08.5-00: baseline verification
- v08.5-01: `docs/reports/2026-05-17-v08_5-source-audit.md` source summary audit
- v08.5-02: real source summary domain graph rebuild, `tests/test_v08_5_real_graph_population.py`; `graph/domain_graph.json` and `graph/entity_index.json` are verified local generated outputs and are ignored by Git
- v08.5-03: `docs/reports/2026-05-17-v08_5-graph-report-review.md` graph report validation
- v08.5-04: graph-derived wiki generation, `tests/test_v08_5_real_derived_wiki.py`; `wiki/jobs`, `wiki/patches`, and `wiki/skills` are verified local generated outputs and are ignored by Git
- v08.5-05: FTS reindexing, `tests/test_v08_5_fts_visibility.py`; `index_wiki_documents()` indexed 38 pages (`source_summary=26`, `job=5`, `patch=3`, `skill=4`) and ask smoke returned generated wiki contexts for `job_gunbreaker`, `patch_7_5`, and `skill_no_mercy`
- v08.5-06: answer quality, `tests/test_v08_5_answer_quality.py`; `compose_answer()` now returns structured `요약`, `관련 항목`, `확인된 내용`, `근거 문서`, `확실도`, `주의` sections instead of raw source dumps
- v08.5-07: v08.5 regression tests consolidation; focused v08.5 tests are `real_graph_population` 5 OK, `real_derived_wiki` 6 OK, `fts_visibility` 6 OK, and `answer_quality` 6 OK
- v08.5-08: documentation/runbook update; added `docs/runbooks/domain-graph-refresh.md` and refreshed README/specs/runbooks/handoff for the v08.5 graph/wiki/FTS/ask workflow
- v08.5-09: final verification; pipeline smoke, ask smoke, graph/wiki counts, full unittest, docs freshness, and finish_task all passed

다음 작업:

- wait for maintainer scope

아직 하지 말 것:

- v09 이후 기능을 maintainer 요청 없이 앞당기지 않는다.
- BIS/raid/item namespace expansion, crawling/polling, vector DB, graph DB, and LLM API integration remain out of scope until explicitly requested.

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

v08.5 완료 시점 검증:

OpenClaw use-case skill routing maintenance 검증:

```bash
python -m unittest tests.test_openclaw_skills -v
python -m unittest tests.test_v05_process_source tests.test_v04_openclaw_notion_control tests.test_v04_status_notification -v
git diff --check
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

결과:

- OpenClaw skill routing tests: 6 tests OK
- source-processing / Notion boundary regression tests: 39 tests OK
- `git diff --check`: OK
- docs freshness: OK
- `finish_task.py`: 361 tests OK, docs freshness OK, Notion handoff dry-run OK

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

결과:

- domain graph dry-run: `status=ok`, `planned_sources=26`, `planned_registry_nodes=12`
- graph report: `status=ok`, `warnings=1`
- graph-derived wiki dry-run: `status=ok`, 12 pages planned (`jobs=5`, `patches=3`, `skills=4`)
- graph nodes: `Fact=14`, `Job=5`, `Patch=3`, `Skill=4`, `SourceDocument=26`, `WikiPage=38`
- graph edges: `AFFECTS_JOB=59`, `AFFECTS_SKILL=4`, `DERIVED_FROM=77`, `HAS_SKILL=4`, `MENTIONS=198`, `SOURCE_OF=46`, `SUPPORTS=14`, `VALID_IN_PATCH=14`
- wiki pages: `source_summary=26`, `job=5`, `patch=3`, `skill=4`
- ask smoke: 4 representative queries returned `status=ok`, non-empty contexts, structured answer sections, and no raw source dump marker
- full unittest discovery: 355 tests OK
- docs freshness: OK
- `finish_task.py`: 355 tests OK, docs freshness OK, Notion handoff dry-run OK

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

- v08.5 is complete.
- OpenClaw use-case skill routing is complete.
- Generated local outputs under `db/`, `graph/`, `wiki/jobs/`, `wiki/patches/`, and `wiki/skills/` should stay uncommitted unless a future maintainer scope explicitly changes that policy.
- Push after each completed task per maintainer instruction.

## 운영 원칙

- `docs/`가 source of truth다. Notion은 mirror/index/control layer일 뿐이다.
- `CURRENT_HANDOFF.md`에는 현재 상태만 남긴다.
- 완료된 상세 작업 로그는 `docs/handoff/history/` 또는 각 task plan에 남긴다.
- 코드 변경이 있으면 관련 spec/runbook/plan과 handoff를 함께 갱신한다.
- 기존 사용자 변경을 임의로 revert하지 않는다.

## 다음 agent에게

v08.5 is complete. OpenClaw use-case skill routing is the latest maintenance task. Start new work only from explicit maintainer scope.
