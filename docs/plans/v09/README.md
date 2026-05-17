# v09 Feature Plans

v09 guide.ff14.co.kr Official DB Crawler + Item Pilot의 feature별 plan을 보관한다.

v09의 목표는 official guide DB를 무작정 source summary로 넣지 않고, bounded crawler state, structured item rows, `wiki/items`, FTS, graph, ask provenance까지 이어지는 item pilot pipeline을 만드는 것이다.

v09 완료 후 목표 파이프라인:

```text
guide.ff14.co.kr category/detail pages
  -> safe fetcher
  -> item pilot crawler
  -> raw snapshot + SQLite guide tables
  -> wiki/items derived pages
  -> wiki_pages/wiki_fts
  -> item graph nodes/edges
  -> item-aware ask context
```

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md`에 있다.

구현 계약은 `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`를 따른다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 00 | 2026-05-17-v09-00-baseline-guardrails.md | repo baseline inspection and generated-artifact guardrails | Completed 2026-05-17 |
| 01 | 2026-05-17-v09-01-storage-schema.md | SQLite guide crawl/item schema and storage | Completed 2026-05-17 |
| 02 | 2026-05-17-v09-02-category-map.md | `fnOpenLeftMenu` category map parser | Completed 2026-05-17 |
| 03 | 2026-05-17-v09-03-fetcher.md | safe GET-only guide fetcher and robots snapshot | Completed 2026-05-17 |
| 04 | 2026-05-17-v09-04-item-extractor.md | deterministic item detail extractor | Completed 2026-05-17 |
| 05 | 2026-05-17-v09-05-item-pilot-crawler.md | bounded item pilot crawler and CLI | Completed 2026-05-17 |
| 06 | 2026-05-17-v09-06-item-wiki-generator.md | `wiki/items` derived wiki and FTS indexing | Completed 2026-05-17 |
| 07 | 2026-05-17-v09-07-item-graph.md | domain graph item nodes/edges/report | Completed 2026-05-17 |
| 08 | 2026-05-17-v09-08-item-retrieval.md | item-aware ask retrieval behavior | Completed 2026-05-17 |
| 09 | 2026-05-17-v09-09-runbook-quality-gate.md | runbook and final quality gate | In Progress |
| 10 | 2026-05-17-v09-10-expansion-gate.md | quest/recipe/gathering expansion gate docs only | Pending |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 00 | none | baseline report, `.gitignore` guardrails |
| 01 | `tests/test_guide_ff14_storage.py` | `src/guide_ff14/models.py`, `src/guide_ff14/storage.py` |
| 02 | `tests/test_guide_ff14_category_map.py` | `src/guide_ff14/category_map.py` |
| 03 | `tests/test_guide_ff14_fetcher.py` | `src/guide_ff14/fetcher.py` |
| 04 | `tests/test_guide_ff14_item_extractor.py` | `src/guide_ff14/item_extractor.py` |
| 05 | `tests/test_guide_ff14_crawler.py` | `src/guide_ff14/crawler.py`, `tools/crawl_guide_ff14.py` |
| 06 | `tests/test_guide_ff14_item_wiki.py` | `src/derived_wiki/item_wiki_generator.py`, `tools/generate_item_wiki.py` |
| 07 | `tests/test_guide_ff14_item_graph.py` | existing domain graph rebuild/report code |
| 08 | `tests/test_guide_ff14_item_retrieval.py` | existing retrieval/ask ranking logic |
| 09 | docs freshness | `docs/runbooks/guide-ff14-crawler.md` |
| 10 | docs freshness | spec/runbook future expansion gate docs |

## v09 Scope

v09에서 구현하는 것:

- allowed-host crawler guard for `guide.ff14.co.kr` only
- GET-only fetcher and robots snapshot handling
- category map parser for official DB nav URLs
- bounded item category pilot crawl
- item detail extractor
- SQLite tables: `guide_crawl_pages`, `guide_categories`, `guide_items`, `guide_item_sources`
- `wiki/items` derived wiki generation
- item wiki FTS indexing
- item graph nodes/edges in existing graph tables
- item-aware ask retrieval and grounded answer provenance
- runbook and quality gates

## v09 Non-Goals

v09에서는 다음을 구현하지 않는다.

- silent full-site crawl
- arbitrary external link crawling
- scheduler/polling daemon
- Discord runtime
- external search engine dependency
- LLM extraction
- vector DB or external graph DB
- market board/current-price/player-state data
- quest/recipe/gathering implementation before item pilot gates pass

## Entrypoint Policy

v09에서 추가되는 사용자 대면 entrypoint:

```bash
python tools/crawl_guide_ff14.py category-map --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --apply
python tools/generate_item_wiki.py --dry-run --verbose
python tools/generate_item_wiki.py --verbose
```

기존 ask entrypoint는 호환성을 유지한다:

```bash
python tools/ask.py <question> --format json
python tools/ask.py <question> --format text
```

## Verification

v09 focused tests:

```bash
python -m unittest tests.test_guide_ff14_storage -v
python -m unittest tests.test_guide_ff14_category_map -v
python -m unittest tests.test_guide_ff14_fetcher -v
python -m unittest tests.test_guide_ff14_item_extractor -v
python -m unittest tests.test_guide_ff14_crawler -v
python -m unittest tests.test_guide_ff14_item_wiki -v
python -m unittest tests.test_guide_ff14_item_graph -v
python -m unittest tests.test_guide_ff14_item_retrieval -v
```

Completion gates:

```bash
git diff --check
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

Manual network smoke is runbook-only and requires maintainer-approved crawl scope.

## 권장 구현 순서

```text
v09-00 -> v09-01 -> v09-02 -> v09-03 -> v09-04
  -> v09-05 -> v09-06 -> v09-07 -> v09-08
  -> v09-09 -> v09-10
```

## Writing Rules

- 각 plan은 master plan의 한 task에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 행동 변경은 먼저 red test를 작성한다.
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다.
- Unit tests must not use live network.
- LLM API를 호출하지 않는다.
- generated raw HTML, DB artifacts, generated wiki pages, and graph outputs are not committed.

## Completion Criteria

v09는 다음 조건을 모두 만족하면 완료로 본다.

- category map extraction works against fixtures and live dry-run.
- item pilot crawl can fetch and parse a bounded item category.
- structured item rows are stored in SQLite.
- `wiki/items` derived wiki exists.
- item pages are searchable through FTS.
- graph report includes item entities.
- ask can answer item lookup questions with official guide provenance.
- no broad raw HTML dump appears in answers.
- quest/recipe/gathering expansion remains blocked until item pilot quality gates pass.
