# CURRENT_HANDOFF

이 문서는 다음 agent/session이 가장 먼저 읽는 현재 상태 대시보드다. 과거 상세 로그는 `docs/handoff/history/`에 보관한다.

## 현재 상태

- Repository: `https://github.com/clip968/ffxiv-claw-bot`
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Branch: `main`
- Last pushed commit: see current `git log --oneline -1` after push
- Current phase: v09 guide.ff14.co.kr official DB crawler in progress
- Last completed task: v09 Task 05 item pilot crawler and CLI
- Next task: v09 Task 06 item wiki generator and FTS integration
- Current maintenance task: v09 item pilot crawler implementation

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
13. `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`
14. `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md`
15. `docs/reports/2026-05-17-v09-task-00-baseline.md`
16. `docs/plans/v09/README.md`
17. `docs/plans/v09/2026-05-17-v09-06-item-wiki-generator.md`

## v09 guide.ff14.co.kr official DB crawler

진행:

- Task 00 baseline inspection completed.
- Confirmed existing patterns:
  - SQLite schema/init uses `CREATE TABLE IF NOT EXISTS` and idempotent `ensure_*_schema(conn)` helpers.
  - Wiki indexing goes through `tools.compile_wiki.index_wiki_documents()`.
  - Graph report generation uses `tools/generate_graph_report.py`.
  - Ask retrieval remains `tools/ask.py` JSON/text CLI over graph-aware FTS context.
  - Tests use standard `unittest`, temp SQLite DBs, local fixtures, and no network dependency.
- Added generated-artifact ignore guards for `data/raw/guide_ff14/` and `wiki/items/`.
- Added baseline report `docs/reports/2026-05-17-v09-task-00-baseline.md`.
- Task 01 SQLite schema/storage completed:
  - Added `src/guide_ff14/__init__.py`, `src/guide_ff14/models.py`, and `src/guide_ff14/storage.py`.
  - Added idempotent tables `guide_crawl_pages`, `guide_categories`, `guide_items`, and `guide_item_sources`.
  - Wired `tools/init_db.py` to call `ensure_guide_ff14_schema(conn)`.
  - Added `docs/DOC_OWNERS.yml` rule `v09-guide-ff14-crawler`.
  - Added `tests/test_guide_ff14_storage.py`.
- Task 02 category map extractor completed:
  - Added fixture `tests/fixtures/guide_ff14/category_map_item_nav.html`.
  - Added `src/guide_ff14/category_map.py`.
  - Added `tests/test_guide_ff14_category_map.py`.
  - Parser extracts `fnOpenLeftMenu` guide DB URLs, normalizes to `https://guide.ff14.co.kr`, preserves Korean labels, excludes `javascript:` pseudo-URLs, and splits category/filter query params.
- Task 03 polite fetcher completed:
  - Added `src/guide_ff14/fetcher.py`.
  - Added `tests/test_guide_ff14_fetcher.py`.
  - Fetcher allows only `guide.ff14.co.kr`, uses GET only, supports injectable session/sleep/timeout/delay, returns structured `FetchResult`, hashes successful bodies, and fetches robots through GET.
- Task 04 item detail extractor completed:
  - Added fixture `tests/fixtures/guide_ff14/item_detail_gunblade.html`.
  - Added `src/guide_ff14/item_extractor.py`.
  - Added `tests/test_guide_ff14_item_extractor.py`.
  - Extractor parses detail id, Korean name, category/subcategory, item/equip levels, jobs, stats, description/source text, hash, raw path, and missing optional-field coverage without network or LLM calls.
- Task 05 item pilot crawler and CLI completed:
  - Added fixture `tests/fixtures/guide_ff14/item_category_gunblade.html`.
  - Added `src/guide_ff14/crawler.py`.
  - Added `tools/crawl_guide_ff14.py`.
  - Added `tests/test_guide_ff14_crawler.py`.
  - `item-pilot --dry-run` fetches the category page through an injected fetcher, discovers bounded detail URLs, and does not create DB/raw outputs.
  - `item-pilot --apply` stores crawl state and item rows idempotently, saves raw snapshots, records detail failures as partial errors, and emits required JSON keys.
- Added `docs/plans/v09/` in the same style as `docs/plans/v08/`:
  - `README.md` includes feature map, red-test map, scope/non-goals, entrypoints, verification, and completion criteria.
  - Task files `v09-00` through `v09-10` mirror the v08 task structure with Spec, Status, Goal, Scope, Red Test, Checklist, Verification, Implementation Notes, and Agent Prompt sections.

검증:

- `git status --short`: inspected before and after preflight cleanup.
- `find docs -maxdepth 3 -type f | sort`: inspected.
- `find tools -maxdepth 2 -type f | sort`: inspected.
- `find tests -maxdepth 2 -type f | sort`: inspected.
- `git diff --check`: OK for Task 00 changes.
- `python scripts/check_docs_freshness.py --all`: OK for Task 00 changes.
- Red check before Task 01 implementation: `python -m unittest tests.test_guide_ff14_storage -v` failed with missing `src.guide_ff14` module.
- Task 01 focused green: `python -m unittest tests.test_guide_ff14_storage -v` -> 5 tests OK.
- `python tools/init_db.py`: OK; initialized `db/ffxiv.sqlite` with v09 tables.
- Task 01 `git diff --check`: OK.
- Task 01 docs freshness: OK.
- Red check before Task 02 implementation: `python -m unittest tests.test_guide_ff14_category_map -v` failed with missing `src.guide_ff14.category_map`.
- Task 02 focused green: `python -m unittest tests.test_guide_ff14_category_map -v` -> 6 tests OK.
- Red check before Task 03 implementation: `python -m unittest tests.test_guide_ff14_fetcher -v` failed with missing `src.guide_ff14.fetcher`.
- Task 03 focused green: `python -m unittest tests.test_guide_ff14_fetcher -v` -> 6 tests OK.
- Red check before Task 04 implementation: `python -m unittest tests.test_guide_ff14_item_extractor -v` failed with missing `src.guide_ff14.item_extractor`.
- Task 04 focused green: `python -m unittest tests.test_guide_ff14_item_extractor -v` -> 8 tests OK.
- Red check before Task 05 implementation: `python -m unittest tests.test_guide_ff14_crawler -v` failed with missing `src.guide_ff14.crawler` and `tools.crawl_guide_ff14`.
- Task 05 focused green: `python -m unittest tests.test_guide_ff14_crawler -v` -> 8 tests OK.
- v09 plan folder freshness update: `python scripts/check_docs_freshness.py --all` -> OK.

다음 작업:

- Task 06: add `wiki/items` generator and FTS indexing with temp DB/wiki tests.

아직 하지 말 것:

- Live guide.ff14.co.kr network smoke without maintainer-approved crawl scope.
- Quest/recipe/gathering expansion before item pilot quality gates pass.
- Scheduler, Discord runtime, vector DB, external graph DB, broad crawl, or LLM extraction.

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

## v08.5 precision hardening

완료:

- Added `tests/test_v08_5_precision_regression.py` with red-first coverage for:
  - official job guide cross-job nav/menu removal
  - official job guide source_summary job metadata
  - Gunbreaker/Paladin job-specific context filtering
  - `title:`, `Job Actions`, `Recast`, `Cast`, `Range`, `Radius` structural evidence noise
  - Continuation answer filtering for unrelated Solution Nine and leve client lines
- Added `src/source_processing/job_guide.py` helper for official job guide detection and cleanup.
- Updated HTML extraction, source summary scanning, graph rebuild, FTS indexing, graph retrieval, ask result policy, and answer composition.
- Rebuilt local graph/wiki/FTS outputs without crawling new sources.
- Added `QUALITY_REPORT.md` with red test, rebuild counts, ask checks, and focused/full test results.

검증:

- Red check before implementation: `python -m unittest tests.test_v08_5_precision_regression -v` failed as expected with 5 failures and 1 error.
- `python tools/rebuild_domain_graph.py --reset-domain-graph --verbose`: `status=ok`, `sources=31`, `facts=19`, export `nodes=105`, export `edges=396`, report `warnings=1`.
- `python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph`: `status=ok`, `warnings=1`.
- `python tools/generate_derived_wiki.py --verbose`: `status=ok`, generated 5 job pages, 3 patch pages, and 4 skill pages.
- `index_wiki_documents()`: `status=ok`, `indexed=43` (`source_summary=31`, `job=5`, `patch=3`, `skill=4`).
- SQLite counts: `sources=29`, `wiki_pages=43`, `wiki_fts=43`, `graph_nodes=105`, `graph_edges=487`.
- Actual ask 8 checks: all `status=ok`; Gunbreaker/Paladin cross-job job guide contamination removed; Gunbreaker 7.5 answer has no Black Mage title evidence; Continuation answer has no Solution Nine or leve client evidence.
- Focused v08.5 tests: `python -m unittest tests.test_v08_5_precision_regression tests.test_v08_5_real_graph_population tests.test_v08_5_real_derived_wiki tests.test_v08_5_fts_visibility tests.test_v08_5_answer_quality -v` -> 29 tests OK.
- v06 focused regression: `python -m unittest tests.test_v06_extractors tests.test_v06_fts_indexing -v` -> 39 tests OK.
- v07 focused regression: `python -m unittest tests.test_v07_query_parser tests.test_v07_retrieval tests.test_v07_context_builder tests.test_v07_answer_composer tests.test_v07_ask_cli -v` -> 51 tests OK.
- v08 focused regression: `python -m unittest tests.test_v08_e2e tests.test_hybrid_retrieval tests.test_domain_graph_rebuild tests.test_graph_report tests.test_derived_wiki -v` -> 43 tests OK.
- Full unittest discovery: `python -m unittest discover -s tests -p "test_*.py"` -> 367 tests OK.

최종 gate:

- `python scripts/check_docs_freshness.py --all`: OK (`changed files=18`, `code files=11`, `docs files=6`, `doc owner rules=15`).
- `python scripts/finish_task.py`: OK (`367 tests OK`, docs freshness OK, Notion handoff dry-run OK).

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

- wait for maintainer scope; next candidate is v09 official guide DB crawler

아직 하지 말 것:

- v09 구현과 v10 이후 기능을 maintainer 요청 없이 앞당기지 않는다.
- v09 official guide DB crawler is specified in `docs/specs/0011-guide-ff14-official-db-crawler.md`; v10 log/notebook namespace expansion remains future work.
- BIS/raid namespace expansion, broad crawling/polling, vector DB, graph DB, and LLM API integration remain out of scope until explicitly requested.

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

- v09 구현과 v10 이후 기능을 maintainer 요청 없이 앞당기지 않는다.

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
