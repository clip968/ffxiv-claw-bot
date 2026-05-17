# SPEC 0011 / v09 - guide.ff14.co.kr Official DB Crawler

## Status

In progress

Version mapping: this spec owns the v09 implementation track.

## Purpose

Build the v09 scoped crawler and wiki pipeline for the Korean official FFXIV
guide site:

- https://guide.ff14.co.kr/
- https://guide.ff14.co.kr/lodestone/db/item
- https://guide.ff14.co.kr/lodestone/db/quest
- https://guide.ff14.co.kr/lodestone/db/duty
- https://guide.ff14.co.kr/lodestone/db/achievement
- https://guide.ff14.co.kr/lodestone/db/recipe
- https://guide.ff14.co.kr/lodestone/db/gathering
- https://guide.ff14.co.kr/lodestone/db/shop
- https://guide.ff14.co.kr/lodestone/db/text_command

The goal is not broad web crawling. The goal is a controlled official DB
crawler that can discover category URLs, pilot one item category, extract
detail pages into structured SQLite records, generate `wiki/items`, and then
expand to quest/recipe/gathering only after quality gates pass.

## Background

The current v08.5 RAG Wiki pipeline can already process source summaries,
rebuild a domain graph, generate derived wiki pages, index FTS, and answer
with grounded context.

However, large official DB domains such as items, quests, recipes, and
gathering logs should not be ingested as flat source summaries only. They need
structured crawler state, detail extractors, dedicated SQLite tables, and
namespace-specific derived wiki generation.

Manual inspection of `guide.ff14.co.kr` found:

- `robots.txt` currently only includes a Bingbot-specific disallow for
  `/lodestone/search`.
- normal GET requests for DB pages return HTML.
- HEAD requests may reset connections; crawler implementation should use GET
  and tolerate connection resets.
- the DB left navigation exposes category URLs inside JavaScript calls such as
  `fnOpenLeftMenu(..., '/lodestone/db/item?category2=1&category3=110')`.
- `/lodestone/db/item` currently exposes item detail links like
  `/lodestone/db/item/5398978e726`.

This spec turns that observation into an implementation contract.

## Scope

In scope:

- guide.ff14.co.kr crawler spec
- category map extractor
- item category pilot crawler
- item detail extractor
- SQLite schema additions for crawl state and item records
- `wiki/items` derived wiki generation
- FTS indexing for item derived wiki
- graph/entity extension for items
- quality gate before expanding to quest/recipe/gathering
- runbook and tests

Out of scope:

- silent full-site crawl
- scheduler/polling daemon
- Discord slash command runtime
- external search engine dependency
- LLM API extraction
- vector DB
- external graph DB
- quest/recipe/gathering full crawl before item pilot passes
- live market board data
- current-price or player-state data
- bypassing access controls, rate limits, or anti-bot protections

## Safety And Crawl Policy

The crawler must be polite and resumable.

Requirements:

- Use an explicit allowed host list containing only `guide.ff14.co.kr`.
- Do not crawl arbitrary external links.
- Respect `robots.txt` and record the fetched robots snapshot.
- Use GET, not HEAD, for page availability checks because HEAD may reset.
- Use a configurable delay between requests.
- Use a configurable max page limit.
- Store crawl status so interrupted runs can resume.
- Deduplicate by canonical URL and detail ID.
- Store content hash and skip unchanged pages.
- Save raw HTML snapshots under a derived raw directory.
- Do not push generated raw/db/wiki outputs unless a later spec changes policy.
- Stop and report if response status, encoding, or HTML structure changes
  enough to break extractors.

## Architecture

Target flow:

```text
guide.ff14.co.kr DB index/category page
  -> category map extractor
  -> scoped category URL list
  -> item pilot crawler
  -> raw HTML snapshots
  -> item detail link discovery
  -> item detail extractor
  -> SQLite crawl/item tables
  -> domain graph item nodes/edges
  -> wiki/items derived pages
  -> FTS index
  -> ask smoke and precision tests
```

## New Tools

### tools/crawl_guide_ff14.py

Official DB crawler entrypoint.

Modes:

```bash
python tools/crawl_guide_ff14.py category-map --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --apply
```

Responsibilities:

- fetch only allowed host URLs
- save raw snapshots
- discover category/detail URLs
- update crawl state
- emit JSON result

### tools/generate_item_wiki.py

Generate item derived wiki from structured item records.

Example:

```bash
python tools/generate_item_wiki.py --dry-run --verbose
python tools/generate_item_wiki.py --verbose
```

### Optional Future Unified Hook

After item pilot is stable, `tools/generate_derived_wiki.py` may support:

```bash
python tools/generate_derived_wiki.py --kind items
```

Do not add this until item generation works independently.

## New Packages

Suggested structure:

```text
src/guide_ff14/
  __init__.py
  models.py
  fetcher.py
  category_map.py
  crawler.py
  item_extractor.py
  storage.py

src/derived_wiki/
  item_wiki_generator.py
```

## SQLite Schema

Add migration logic through the existing DB initialization/update style.

### guide_crawl_pages

Stores fetched pages and crawl state.

Fields:

- `url TEXT PRIMARY KEY`
- `kind TEXT NOT NULL`
  - `category_index`
  - `category_page`
  - `detail_page`
- `domain TEXT NOT NULL DEFAULT 'guide.ff14.co.kr'`
- `status TEXT NOT NULL`
  - `pending`
  - `fetched`
  - `parsed`
  - `error`
  - `skipped`
- `http_status INTEGER`
- `content_hash TEXT`
- `raw_path TEXT`
- `last_error TEXT`
- `fetched_at TEXT`
- `parsed_at TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

### guide_categories

Stores discovered DB category URLs.

Fields:

- `id TEXT PRIMARY KEY`
- `db_type TEXT NOT NULL`
  - `item`
  - `quest`
  - `duty`
  - `achievement`
  - `recipe`
  - `gathering`
  - `shop`
  - `text_command`
- `label TEXT NOT NULL`
- `url TEXT NOT NULL UNIQUE`
- `parent_id TEXT`
- `category2 TEXT`
- `category3 TEXT`
- `filters_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

### guide_items

Stores structured item records from item detail pages.

Fields:

- `id TEXT PRIMARY KEY`
  - use official detail id from URL, e.g. `5398978e726`
- `name TEXT NOT NULL`
- `name_ko TEXT`
- `url TEXT NOT NULL UNIQUE`
- `category TEXT`
- `subcategory TEXT`
- `item_level INTEGER`
- `equip_level INTEGER`
- `rarity TEXT`
- `is_unique INTEGER NOT NULL DEFAULT 0`
- `is_untradable INTEGER NOT NULL DEFAULT 0`
- `jobs_json TEXT NOT NULL DEFAULT '[]'`
- `stats_json TEXT NOT NULL DEFAULT '{}'`
- `source_json TEXT NOT NULL DEFAULT '{}'`
- `description TEXT`
- `patch TEXT`
- `content_hash TEXT NOT NULL`
- `raw_path TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

### guide_item_sources

Optional normalized source/vendor/acquisition table.

Fields:

- `id TEXT PRIMARY KEY`
- `item_id TEXT NOT NULL`
- `source_type TEXT NOT NULL`
  - `vendor`
  - `duty`
  - `quest`
  - `recipe`
  - `gathering`
  - `achievement`
  - `unknown`
- `source_name TEXT`
- `source_url TEXT`
- `properties_json TEXT NOT NULL DEFAULT '{}'`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

## Category Map Extractor

The category extractor must parse `fnOpenLeftMenu(..., '<url>')` style links.

Input:

- HTML from `https://guide.ff14.co.kr/lodestone/db/item` or other DB roots.

Output:

- ordered category records with:
  - label text
  - db type
  - URL path/query
  - parent relationship when inferable
  - query params such as `category2`, `category3`, `min_gear_lv`,
    `max_gear_lv`, `min_item_lv`, `max_item_lv`

Acceptance criteria:

- Extracts top-level DB types:
  - item
  - quest
  - duty
  - achievement
  - recipe
  - gathering
  - shop
  - text_command
- Extracts nested item categories such as weapon categories.
- Normalizes relative URLs to absolute guide URLs.
- Does not include JavaScript pseudo-URLs as final URLs.
- Unit tests cover representative `fnOpenLeftMenu` snippets.

## Item Pilot Crawl

Pilot category recommendation:

```text
/lodestone/db/item?category2=1&category3=110
```

Reason:

- `category3=110` appears to be Gunbreaker gunblade category.
- It is directly relevant to the existing job/patch corpus.
- It is bounded enough for a pilot.

Pilot behavior:

- Fetch the category page.
- Discover up to `--limit` item detail links.
- Fetch detail pages.
- Store raw snapshots.
- Extract structured item rows.
- Record failed pages without aborting the whole batch unless the category page
  itself fails.

Acceptance criteria:

- Dry run reports planned category/detail URLs without DB mutation.
- Apply run stores crawl pages and item rows.
- Re-running apply does not duplicate item rows.
- `--limit 1` is enough for a fast smoke test.
- JSON output includes:
  - `status`
  - `category_url`
  - `planned_urls`
  - `fetched`
  - `parsed`
  - `skipped`
  - `errors`
  - `next_action`

## Item Detail Extractor

The extractor must be deterministic and HTML-structure-aware.

Required fields for pilot:

- item id
- item name
- canonical URL
- category/subcategory when visible
- item level when visible
- equip level when visible
- job restrictions when visible
- stats when visible
- description when visible
- source/acquisition text when visible
- content hash
- raw path

Do not infer missing game facts. If a field is absent, store null or empty
structured JSON and report extraction coverage.

Acceptance criteria:

- Unit fixture with one saved guide item detail page parses required fields.
- Missing optional fields do not fail extraction.
- Parser strips nav/menu/search/footer noise.
- Parser preserves Korean item text.
- Parser does not execute scripts.

## Domain Graph Extension

Add item domain nodes and edges.

Nodes:

- `Item`
- `ItemCategory`
- `EquipmentJob`
- `ItemSource`

Edges:

- `ITEM_IN_CATEGORY`
- `EQUIPPABLE_BY_JOB`
- `HAS_ITEM_LEVEL`
- `HAS_EQUIP_LEVEL`
- `OBTAINED_FROM`
- `DERIVED_FROM`

Graph report must include item counts after the pilot.

Acceptance criteria:

- graph report shows non-zero `Item` count after pilot apply.
- item nodes link to source/detail page provenance.
- item wiki pages link back to official guide URL/source id.

## Derived Wiki: wiki/items

Generated paths:

```text
wiki/items/index.md
wiki/items/categories/<category_slug>.md
wiki/items/<item_slug_or_id>.md
```

Minimum page content:

- title
- official URL
- category
- item level / equip level
- allowed jobs if available
- stats if available
- acquisition/source if available
- related source document
- confidence/staleness note

Acceptance criteria:

- generator dry-run lists planned pages.
- generator apply writes item pages.
- generated item pages are indexed in `wiki_pages` with type `item`.
- generated item pages are indexed in `wiki_fts`.
- `wiki/index.md` links to `wiki/items/index.md`.

## Retrieval And Ask Integration

Add item-aware ask behavior only after item pages are generated.

Example questions:

```bash
python tools/ask.py "건브 100레벨 무기 뭐 있어?" --format json
python tools/ask.py "아이템 레벨 700 이상 건블레이드 보여줘" --format json
python tools/ask.py "이 아이템 어디서 얻어?" --format json
```

Acceptance criteria:

- item title searches return item wiki pages before broad source summaries.
- job + item category queries do not return unrelated job guide pages first.
- item answers include official guide source URL.
- if acquisition is absent, answer says the current KB has no acquisition data.

## Expansion Gate

Do not expand to quest/recipe/gathering until all item pilot gates pass.

Required item pilot gates:

- category map tests pass
- item detail extractor tests pass
- item pilot crawl dry-run/apply smoke pass
- item derived wiki generated and FTS-indexed
- graph report shows item nodes/edges
- representative ask smoke passes
- no broad raw HTML dump in answers
- docs/runbook updated

After item pilot:

### Quest Expansion

Add:

- `guide_quests`
- `Quest`
- `QuestIssuer`
- `QuestLocation`
- `QuestReward`
- `REQUIRES_QUEST`
- `UNLOCKS_CONTENT`

### Recipe Expansion

Add:

- `guide_recipes`
- `Recipe`
- `CraftingJob`
- `Ingredient`
- `PRODUCES_ITEM`
- `REQUIRES_INGREDIENT`

### Gathering Expansion

Add:

- `guide_gathering_entries`
- `GatheringEntry`
- `GatheringNode`
- `GatheringJob`
- `Zone`
- `FOUND_AT_NODE`
- `GATHERED_BY`

## Tests

Required tests:

- `tests/test_guide_ff14_storage.py`
- `tests/test_guide_ff14_category_map.py`
- `tests/test_guide_ff14_item_extractor.py`
- `tests/test_guide_ff14_crawler.py`
- `tests/test_guide_ff14_item_wiki.py`
- `tests/test_guide_ff14_item_retrieval.py`

Test expectations:

- use local fixtures for parser/extractor tests
- do not require network in normal unittest
- network smoke can be manual/runbook-only
- use tiny `--limit 1` pilot for optional integration smoke

## Runbook

Add:

```text
docs/runbooks/guide-ff14-crawler.md
```

Required sections:

- robots/access check
- category-map dry run
- item pilot dry run
- item pilot apply with `--limit 1`
- item wiki generation
- FTS reindex
- graph report
- ask smoke
- rollback/cleanup notes

## Quality Gates

Before marking this spec complete:

```bash
python -m unittest tests.test_guide_ff14_category_map -v
python -m unittest tests.test_guide_ff14_storage -v
python -m unittest tests.test_guide_ff14_item_extractor -v
python -m unittest tests.test_guide_ff14_crawler -v
python -m unittest tests.test_guide_ff14_item_wiki -v
python -m unittest tests.test_guide_ff14_item_retrieval -v
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

Manual smoke, only when network is available and maintainer has approved crawl
scope:

```bash
python tools/crawl_guide_ff14.py category-map --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --dry-run
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --apply
python tools/generate_item_wiki.py --verbose
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/ask.py "건브 무기 source 보여줘" --format json
```

## Success Criteria

This spec is complete when:

- category map extraction works against fixtures and live dry-run
- item pilot crawl can fetch and parse a bounded item category
- structured item rows are stored in SQLite
- `wiki/items` derived wiki exists
- item pages are searchable through FTS
- graph report includes item entities
- ask can answer item lookup questions with official guide provenance
- quest/recipe/gathering expansion is documented but not executed before item
  pilot quality gates pass
