# Implementation Plan — v09 guide.ff14.co.kr Official DB Crawler

Source spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

Current status:

- Task 00: completed on 2026-05-17; see `docs/reports/2026-05-17-v09-task-00-baseline.md`.
- Task 01: completed on 2026-05-17; added `src/guide_ff14` schema/storage and `tests/test_guide_ff14_storage.py`.
- Task 02: completed on 2026-05-17; added category-map fixture, parser, and tests.
- Task 03: completed on 2026-05-17; added safe fetcher and fake-client tests.
- Task 04: completed on 2026-05-17; added item detail fixture, extractor, and tests.
- Task 05: next.

This document splits v09 into task-sized implementation units. Each task is intended to be handed to an agent as a bounded unit of work. Do not collapse the tasks into one broad implementation pass. The intended workflow is:

1. Read the relevant spec and current repository files first.
2. Write or update the red test before implementation when behavior changes.
3. Run the targeted test and confirm it fails for the expected behavioral reason, not due to syntax/import errors.
4. Implement the smallest code change that satisfies that task.
5. Re-run the targeted tests and any affected regression tests.
6. Update docs/runbook only when behavior or commands changed.
7. Stop at the task boundary and report changed files, tests run, and remaining risks.

## Non-negotiable v09 constraints

- Scope is only `guide.ff14.co.kr` official DB crawling.
- Allowed host list must contain only `guide.ff14.co.kr`.
- Use GET for availability/fetching. Do not use HEAD because guide pages may reset HEAD requests.
- Do not crawl arbitrary external links.
- Do not add scheduler, Discord runtime, vector DB, external graph DB, market board data, LLM extraction, or broad full-site crawling.
- Do not expand to quest/recipe/gathering implementation until the item pilot quality gate passes.
- Unit tests must not require network access.
- Live network checks belong only in the runbook/manual smoke section.
- Generated raw HTML, SQLite DB artifacts, generated wiki pages, graph output, and local crawl snapshots must not be committed unless a later spec explicitly changes that policy.
- Dry-run commands must not mutate DB, raw files, wiki files, graph files, or crawl state.
- Apply commands must be idempotent: repeated runs must not duplicate categories, crawl pages, item rows, item source rows, wiki page records, graph nodes, or graph edges.

## Expected task sequence

Recommended order:

1. Task 00 — Baseline repo inspection and guardrails
2. Task 01 — SQLite schema and storage layer
3. Task 02 — Category map extractor
4. Task 03 — Polite fetcher and robots snapshot handling
5. Task 04 — Item detail extractor
6. Task 05 — Item pilot crawler and CLI
7. Task 06 — Item wiki generator and FTS integration
8. Task 07 — Domain graph item extension
9. Task 08 — Item-aware retrieval and ask smoke behavior
10. Task 09 — Runbook, quality gate, and final finish workflow
11. Task 10 — Expansion-gate documentation only

Each task below contains a task prompt that can be copied into an agent. Keep the task prompt intact unless the repository has already implemented part of the task.

---

# Task 00 — Baseline repo inspection and guardrails

## Goal

Establish the current repo state before touching code. Confirm where DB initialization, wiki indexing, graph report generation, ask retrieval, docs freshness, and finish workflow currently live.

## Expected files to inspect

- `README.md`
- `CLAUDE.md` or equivalent project instructions if present
- `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`
- existing `docs/specs/`, `docs/plans/`, `docs/runbooks/`
- existing `tools/compile_wiki.py`
- existing `tools/generate_derived_wiki.py`
- existing `tools/generate_graph_report.py`
- existing `tools/ask.py`
- DB initialization/migration code, wherever it currently lives
- existing tests under `tests/`
- `.gitignore`

## Red test requirement

No new red test is required in this task. This task is inspection-only. If the repository has no guard for generated crawler artifacts, add a red check only after confirming the current `.gitignore` does not already cover them.

## Implementation requirements

- Do not change product code unless a missing `.gitignore` guard is clearly found.
- Identify the canonical migration/init entrypoint.
- Identify whether generated wiki pages are committed today or treated as generated output.
- Identify the current pattern for JSON CLI output.
- Identify the current test style: unittest, pytest compatibility, fixture location, temp DB pattern.
- Identify whether `scripts/finish_task.py` and `scripts/check_docs_freshness.py` exist and how they are expected to be run.

## Verification commands

Run only commands that are safe in the current repo. Minimum:

    git status --short
    find docs -maxdepth 3 -type f | sort
    find tools -maxdepth 2 -type f | sort
    find tests -maxdepth 2 -type f | sort

If PowerShell is used, use PowerShell equivalents instead of Unix `find`.

## Done criteria

- A short baseline report exists in the task result.
- No broad implementation has started.
- Any repo-specific deviations from this implementation plan are listed.

## Agent prompt

You are implementing v09 for the ffxiv bot repo. Start with inspection only. Read `docs/specs/0011-v09-guide-ff14-official-db-crawler.md` and the existing workflow docs. Do not implement crawler code yet. Identify the current DB migration/init style, wiki indexing style, graph report style, ask retrieval style, test fixture style, and finish workflow. Check `.gitignore` for generated crawler/raw/db/wiki/graph artifacts. Produce a concise baseline report with exact files inspected, current patterns found, and any deviations that future tasks must respect. Do not modify code except for a clearly missing generated-artifact ignore rule, and only if the repo pattern supports that change.

---

# Task 01 — SQLite schema and storage layer

## Goal

Add durable, idempotent SQLite support for v09 crawl state and structured item records.

## Primary deliverables

- `src/guide_ff14/__init__.py`
- `src/guide_ff14/models.py`
- `src/guide_ff14/storage.py`
- migration/init updates in the existing DB initialization location
- tests for schema creation and idempotent upserts

## Schema to add

Required tables:

- `guide_crawl_pages`
- `guide_categories`
- `guide_items`

Optional but recommended now if storage pattern is clear:

- `guide_item_sources`

Follow the schema from SPEC 0011 exactly unless repo constraints require minor adaptation. Required storage behavior:

- create tables idempotently
- upsert crawl pages by canonical URL
- upsert categories by id or URL without duplication
- upsert items by official detail id and unique URL
- optionally upsert item sources by stable deterministic id
- preserve `created_at` on updates
- update `updated_at` on updates
- store JSON fields as text with valid JSON defaults

## Red test requirement

Create or update tests before implementation. If the repo already has DB test conventions, follow them. If not, add a focused test file such as:

- `tests/test_guide_ff14_storage.py`

Required red tests:

1. `init_guide_ff14_schema` creates all required tables in a temp SQLite DB.
2. Upserting the same crawl page twice results in one row and updates status/hash.
3. Upserting the same category twice results in one row and preserves a unique URL.
4. Upserting the same item twice results in one row and valid JSON fields.
5. `created_at` does not change on update, while `updated_at` does.

The initial red failure should be missing functions/tables or failing behavior, not import errors caused by bad module paths.

## Implementation requirements

- Use dataclasses or simple typed dictionaries consistently with the repo style.
- Keep storage deterministic and free of network calls.
- Keep JSON serialization centralized.
- Use official detail id from item URL as `guide_items.id`.
- Do not introduce ORM dependencies unless the repo already uses one.
- Do not modify existing v08.5 source-summary tables except through existing migration conventions.

## Verification commands

    python -m unittest tests.test_guide_ff14_storage -v

If the repo does not want a separate storage test file, run the equivalent targeted unittest module.

## Done criteria

- Temp DB tests pass.
- Running schema init twice is safe.
- No network required.
- No generated DB artifact is committed.

## Agent prompt

Implement only the v09 SQLite schema and storage layer. First write red tests for table creation and idempotent upserts using a temp SQLite DB. Confirm the tests fail for missing schema/storage behavior. Then add `src/guide_ff14/models.py` and `src/guide_ff14/storage.py`, and wire schema creation into the existing DB initialization/migration style. Add tables for `guide_crawl_pages`, `guide_categories`, `guide_items`, and `guide_item_sources` if straightforward. Preserve `created_at`, update `updated_at`, serialize JSON fields deterministically, and avoid any network dependency. Run the targeted storage tests and report changed files.

---

# Task 02 — Category map extractor

## Goal

Parse official DB category URLs from guide page HTML, especially `fnOpenLeftMenu(..., '<url>')` calls, and normalize them into structured category records.

## Primary deliverables

- `src/guide_ff14/category_map.py`
- fixtures under the repo’s existing fixture directory, for example:
  - `tests/fixtures/guide_ff14/category_map_item_nav.html`
- `tests/test_guide_ff14_category_map.py`

## Required behavior

- Parse `fnOpenLeftMenu(..., '/lodestone/db/item?category2=1&category3=110')` style URLs.
- Extract top-level DB types:
  - `item`
  - `quest`
  - `duty`
  - `achievement`
  - `recipe`
  - `gathering`
  - `shop`
  - `text_command`
- Extract nested item categories where present.
- Normalize relative URLs to absolute `https://guide.ff14.co.kr/...` URLs.
- Extract query params such as `category2`, `category3`, `min_gear_lv`, `max_gear_lv`, `min_item_lv`, `max_item_lv` into structured fields or `filters_json`.
- Do not include `javascript:` pseudo-URLs as final URLs.
- Preserve Korean labels.
- Keep parser deterministic and non-networked.

## Red test requirement

Write red tests first in `tests/test_guide_ff14_category_map.py`.

Required red tests:

1. Representative `fnOpenLeftMenu` snippets produce normalized absolute URLs.
2. Top-level DB roots are recognized as the correct `db_type` values.
3. Gunbreaker weapon category URL with `category2=1&category3=110` is extracted.
4. JavaScript pseudo-URLs are excluded from output.
5. Query params are parsed into `category2`, `category3`, and filters.
6. Korean category labels survive without mojibake.

## Implementation requirements

- Use BeautifulSoup only if it already exists as a dependency or is already used by the repo. Otherwise prefer standard library regex + `html` + `urllib.parse` for this narrow parser.
- Do not execute scripts.
- Produce stable category ids. Recommended format: `guide:{db_type}:{category2}:{category3}` when category params exist, otherwise a slug/hash from normalized URL.
- Preserve input order.
- Make the parser usable by the future crawler and by tests from raw HTML strings.

## Verification commands

    python -m unittest tests.test_guide_ff14_category_map -v

## Done criteria

- Category parser tests pass.
- No network usage in tests.
- No crawler CLI implementation is added in this task.

## Agent prompt

Implement only the guide.ff14.co.kr category map parser. First add fixture-based red tests in `tests/test_guide_ff14_category_map.py` covering `fnOpenLeftMenu` URL extraction, top-level DB type detection, Gunbreaker category `category2=1&category3=110`, JavaScript pseudo-URL exclusion, query param parsing, and Korean label preservation. Confirm the red tests fail for missing parser behavior. Then implement `src/guide_ff14/category_map.py` as a deterministic parser from HTML string to structured category records. Do not add network calls or crawler CLI code. Run the targeted category map tests.

---

# Task 03 — Polite fetcher and robots snapshot handling

## Goal

Add a safe fetcher abstraction used by the crawler. It must restrict host access, use GET, capture robots metadata, tolerate connection reset errors, and support dry-run planning without mutation.

## Primary deliverables

- `src/guide_ff14/fetcher.py`
- tests, likely in:
  - `tests/test_guide_ff14_crawler.py`
  - or `tests/test_guide_ff14_fetcher.py` if the repo prefers smaller modules

## Required behavior

- Allowed host list: only `guide.ff14.co.kr`.
- Reject any URL outside the allowed host before any HTTP request.
- Use GET, not HEAD.
- Configurable delay between requests.
- Configurable timeout.
- Configurable max page limit or a caller-visible mechanism to enforce it.
- Store or return fetched robots snapshot metadata for `https://guide.ff14.co.kr/robots.txt`.
- Return structured fetch results containing:
  - URL
  - HTTP status
  - final URL if redirected
  - text/html body when successful
  - encoding if known
  - content hash
  - error string when failed
- Connection resets and request exceptions must return an error result instead of crashing the whole batch.

## Red test requirement

Write red tests first with fake HTTP/session objects. Unit tests must not use network.

Required red tests:

1. Non-allowed host URL is rejected before fake session `.get()` is called.
2. Fetcher uses `.get()`, not `.head()`.
3. Successful HTML response returns status, body, and content hash.
4. Exception during GET returns an error result, not an uncaught exception.
5. Robots snapshot fetch uses GET and returns text/status metadata.
6. Configured delay is injectable or can be disabled in tests.

## Implementation requirements

- Avoid hard dependency on `requests` if the repo already uses another HTTP layer. Use current repo convention.
- If using `requests`, inject the session/client so tests can use fakes.
- Keep raw snapshot writing out of the fetcher unless repo style strongly prefers it. Storage/snapshot writing can live in crawler/storage.
- Do not make live requests in tests.

## Verification commands

    python -m unittest tests.test_guide_ff14_crawler -v

or, if split:

    python -m unittest tests.test_guide_ff14_fetcher -v

## Done criteria

- Fetcher behavior is unit-tested without network.
- Host guard is enforced before HTTP.
- GET-only behavior is test-covered.
- No crawler CLI yet unless the repo already had a minimal CLI shell.

## Agent prompt

Implement only the safe fetcher layer for v09. First write red tests with fake HTTP clients proving that only `guide.ff14.co.kr` is allowed, disallowed hosts are rejected before HTTP, GET is used instead of HEAD, successful HTML responses return content hashes, GET exceptions are returned as structured errors, and robots snapshot retrieval uses GET. Then implement `src/guide_ff14/fetcher.py` with injectable session/client and configurable delay/timeout. Do not perform live network calls in tests and do not implement the full crawler CLI in this task.

---

# Task 04 — Item detail extractor

## Goal

Extract structured item records from one official item detail HTML fixture without inferring missing game facts.

## Primary deliverables

- `src/guide_ff14/item_extractor.py`
- fixture, for example:
  - `tests/fixtures/guide_ff14/item_detail_gunblade.html`
- `tests/test_guide_ff14_item_extractor.py`

## Required extracted fields

Required for pilot when visible:

- item id from canonical/detail URL
- item name
- canonical URL
- category
- subcategory
- item level
- equip level
- job restrictions
- stats
- description
- source/acquisition text
- content hash
- raw path

If a field is absent, store `None`, `{}`, or `[]` as appropriate. Do not infer missing game facts.

## Red test requirement

Write fixture-based red tests first.

Required red tests:

1. Extracts official detail id such as `5398978e726` from URL.
2. Extracts item name and preserves Korean text.
3. Extracts item level and equip level when present.
4. Extracts job restrictions into a list when present.
5. Extracts stats into JSON-compatible dict when present.
6. Missing optional fields do not fail extraction.
7. Nav/menu/search/footer/script noise is not included in description/source text.
8. Script tags are not executed or treated as trusted content.
9. Output includes content hash and raw path.

## Implementation requirements

- Parser must be deterministic and HTML-structure-aware.
- Prefer exact selectors/patterns based on fixture and current guide HTML.
- Add extraction coverage reporting: either return coverage metadata or include a helper that lists missing optional fields.
- Keep item model compatible with Task 01 storage.
- Do not add live network calls.
- Do not call LLM APIs.

## Verification commands

    python -m unittest tests.test_guide_ff14_item_extractor -v

## Done criteria

- Extractor tests pass against local fixture.
- Parser preserves Korean text.
- Parser tolerates absent optional fields.
- No network required.

## Agent prompt

Implement only the item detail extractor. First add a local HTML fixture and red tests in `tests/test_guide_ff14_item_extractor.py` covering item id, name, canonical URL, item/equip level, jobs, stats, optional missing fields, noise stripping, Korean text preservation, and content hash/raw path. Confirm the tests fail for missing extractor behavior. Then implement `src/guide_ff14/item_extractor.py` as a deterministic parser that never infers missing game facts and never uses network or LLM extraction. Run the targeted extractor tests.

---

# Task 05 — Item pilot crawler and CLI

## Goal

Implement the bounded item pilot crawl flow and `tools/crawl_guide_ff14.py` entrypoint.

## Primary deliverables

- `src/guide_ff14/crawler.py`
- `tools/crawl_guide_ff14.py`
- crawler tests in `tests/test_guide_ff14_crawler.py`

## CLI contract

Commands to support:

    python tools/crawl_guide_ff14.py category-map --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 30 --apply

Optional but recommended options:

- `--db-path db/ffxiv.sqlite`
- `--raw-dir data/raw/guide_ff14`
- `--delay-seconds 1.0`
- `--timeout-seconds 20`
- `--json` or default JSON output
- `--verbose`

## Required behavior

- `category-map --dry-run` fetches/plans only the DB roots needed to extract categories and emits JSON result.
- `item-pilot --dry-run` reports planned category/detail URLs without DB mutation or raw snapshot writes.
- `item-pilot --apply`:
  - fetches category page
  - discovers up to `--limit` item detail links
  - fetches detail pages
  - saves raw snapshots
  - extracts item rows
  - stores crawl page state
  - stores item rows
  - records failed pages without aborting whole batch unless category page fails
- Re-running `--apply` must not duplicate rows.
- JSON output must include:
  - `status`
  - `category_url`
  - `planned_urls`
  - `fetched`
  - `parsed`
  - `skipped`
  - `errors`
  - `next_action`

## Red test requirement

Write red tests first using fake fetcher/storage and local HTML fixtures. Do not use network.

Required red tests:

1. `item-pilot --dry-run` returns planned URLs and does not call storage mutation methods.
2. `item-pilot --apply --limit 1` fetches one detail page and stores one item.
3. Re-running apply with same item does not duplicate item rows in temp DB.
4. Category page failure returns status/error and does not attempt detail parsing.
5. Detail page failure is recorded in errors but does not abort remaining detail pages.
6. Discovered detail URLs are normalized to absolute guide URLs and limited by `--limit`.
7. JSON output contains all required keys.

## Implementation requirements

- Reuse Task 02 category parser.
- Reuse Task 03 fetcher.
- Reuse Task 04 item extractor.
- Reuse Task 01 storage.
- Raw snapshot path should be deterministic and based on URL/detail id/content hash.
- Use content hash to skip unchanged pages where possible.
- Do not crawl beyond the supplied category URL and discovered item detail links.
- Do not implement quest/recipe/gathering crawl in this task.

## Verification commands

    python -m unittest tests.test_guide_ff14_crawler -v

Manual smoke is not required for this task, but the CLI should be ready for the runbook.

## Done criteria

- Crawler tests pass without network.
- CLI exists and prints structured JSON.
- Dry-run is non-mutating.
- Apply is idempotent.

## Agent prompt

Implement only the v09 item pilot crawler and CLI. First add red tests in `tests/test_guide_ff14_crawler.py` using fake fetcher/storage and fixtures. Cover non-mutating dry-run, apply with `--limit 1`, idempotent re-run, category failure, detail failure, URL normalization/limit, and required JSON keys. Confirm tests fail for missing crawler behavior. Then implement `src/guide_ff14/crawler.py` and `tools/crawl_guide_ff14.py` by composing the existing storage, fetcher, category parser, and item extractor. Do not implement quest/recipe/gathering crawling. Do not use network in tests. Run the targeted crawler tests.

---

# Task 06 — Item wiki generator and FTS integration

## Goal

Generate `wiki/items` derived pages from structured `guide_items` records and index them into the existing wiki/FTS system.

## Primary deliverables

- `src/derived_wiki/item_wiki_generator.py`
- `tools/generate_item_wiki.py`
- `tests/test_guide_ff14_item_wiki.py`
- update to wiki indexing integration if required

## Generated paths

- `wiki/items/index.md`
- `wiki/items/categories/<category_slug>.md`
- `wiki/items/<item_slug_or_id>.md`

## Minimum item page content

- title
- official URL
- category
- item level / equip level
- allowed jobs if available
- stats if available
- acquisition/source if available
- related source document or raw/source provenance
- confidence/staleness note

## Required behavior

- `python tools/generate_item_wiki.py --dry-run --verbose` lists planned pages without writing files or DB records.
- `python tools/generate_item_wiki.py --verbose` writes pages.
- Generated item pages are indexed in `wiki_pages` with type `item`.
- Generated item pages are indexed in `wiki_fts`.
- `wiki/index.md` links to `wiki/items/index.md`.
- Generation is idempotent.

## Red test requirement

Write red tests first using a temp DB and temp wiki directory.

Required red tests:

1. Dry-run returns planned paths and writes nothing.
2. Apply writes `wiki/items/index.md`, a category page, and an item page.
3. Item page includes official guide URL and item level/equip level when present.
4. Missing acquisition data results in an explicit “current KB has no acquisition data” style note rather than invented facts.
5. Apply indexes item pages into `wiki_pages` with type `item`.
6. Apply indexes item pages into `wiki_fts` or calls the existing wiki indexing function correctly.
7. Re-running generator does not duplicate wiki DB records.
8. `wiki/index.md` gains or preserves the link to `wiki/items/index.md`.

## Implementation requirements

- Reuse existing wiki page/indexing conventions.
- Keep generator independent before adding any unified `generate_derived_wiki.py --kind items` hook.
- Do not add the optional unified hook in this task unless all independent generator tests pass and the change is trivial.
- Do not commit generated wiki output unless repo policy says generated wiki pages are committed.

## Verification commands

    python -m unittest tests.test_guide_ff14_item_wiki -v

If the repo has a full wiki indexing regression test, also run the relevant existing test module.

## Done criteria

- Item wiki tests pass.
- Dry-run is non-mutating.
- Apply is idempotent.
- FTS/indexing integration is verified.

## Agent prompt

Implement only the item derived wiki generator. First write red tests in `tests/test_guide_ff14_item_wiki.py` using temp DB and temp wiki directories. Cover dry-run non-mutation, generated index/category/item pages, official URL/provenance, missing acquisition note, `wiki_pages` type `item`, FTS indexing, idempotent re-run, and `wiki/index.md` link behavior. Confirm the tests fail for missing item wiki behavior. Then implement `src/derived_wiki/item_wiki_generator.py` and `tools/generate_item_wiki.py` using existing wiki indexing conventions. Do not add quest/recipe/gathering wiki generation. Run the targeted item wiki tests.

---

# Task 07 — Domain graph item extension

## Goal

Extend the existing domain graph generation/report path so item records become graph nodes and provenance-linked edges.

## Primary deliverables

- updates to existing graph rebuild/report code
- tests for item graph generation, either in an existing graph test module or a new focused module

## Required nodes

- `Item`
- `ItemCategory`
- `EquipmentJob`
- `ItemSource`

## Required edges

- `ITEM_IN_CATEGORY`
- `EQUIPPABLE_BY_JOB`
- `HAS_ITEM_LEVEL`
- `HAS_EQUIP_LEVEL`
- `OBTAINED_FROM`
- `DERIVED_FROM`

## Required behavior

- Graph report includes non-zero `Item` count after item pilot data exists.
- Item nodes link to official guide/detail provenance.
- Item wiki pages link back to official guide URL/source id when available.
- Missing optional fields do not block graph generation.
- Re-running graph generation does not duplicate item nodes or edges.

## Red test requirement

Write red tests first against a temp DB/graph output.

Required red tests:

1. Given one `guide_items` row, graph generation creates one `Item` node.
2. Given category data, graph generation creates `ItemCategory` and `ITEM_IN_CATEGORY`.
3. Given `jobs_json`, graph generation creates `EquipmentJob` and `EQUIPPABLE_BY_JOB`.
4. Given `item_level` and `equip_level`, graph generation creates corresponding level edges or facts in the existing graph style.
5. Given `source_json` or `guide_item_sources`, graph generation creates `ItemSource` and `OBTAINED_FROM` when data exists.
6. `DERIVED_FROM` links item graph data to guide source/detail provenance.
7. Graph report includes `Item` count.
8. Re-running is idempotent.

## Implementation requirements

- Use the existing graph data model and conventions. Do not introduce an external graph DB.
- If the existing graph uses generic node/edge tables/files, extend those rather than creating a parallel item graph.
- Preserve v08.5 job/patch/skill graph behavior.
- Do not require live crawl in tests.

## Verification commands

Run the new/updated graph tests. Then run existing graph tests if available. Example:

    python -m unittest tests.test_guide_ff14_item_graph -v
    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph

The second command may be manual/local if it writes generated graph files.

## Done criteria

- Item graph tests pass.
- Existing graph behavior is not regressed.
- Graph report can show item counts when item rows exist.

## Agent prompt

Implement only the item extension for the existing domain graph. First write red tests using temp DB/graph output that prove one item row creates an `Item` node, category/job/source/level/provenance edges are emitted when data exists, graph report includes `Item` count, and re-running is idempotent. Confirm the tests fail for missing item graph behavior. Then extend the existing graph generation/report code using the current graph conventions. Do not add an external graph DB and do not alter quest/recipe/gathering. Run the targeted graph tests and any existing graph regression tests.

---

# Task 08 — Item-aware retrieval and ask smoke behavior

## Goal

Make `tools/ask.py` prefer generated item wiki pages for item-related questions after item pages exist, without causing unrelated job guides to dominate item queries.

## Primary deliverables

- update to existing retrieval/ranking logic used by `tools/ask.py`
- `tests/test_guide_ff14_item_retrieval.py`

## Example questions

- `건브 100레벨 무기 뭐 있어?`
- `아이템 레벨 700 이상 건블레이드 보여줘`
- `이 아이템 어디서 얻어?`
- `건브 무기 source 보여줘`

## Required behavior

- Item title/category queries return item wiki pages before broad source summaries.
- Job + item category queries do not return unrelated job guide pages first.
- Item answers include official guide source URL when available.
- If acquisition/source data is absent, answer explicitly says current KB has no acquisition data rather than inventing acquisition.
- Existing job/patch/skill questions should continue to work.

## Red test requirement

Write red tests first with a small temp wiki/FTS dataset. Do not require live crawl.

Required red tests:

1. Query containing `아이템`, `무기`, `건블레이드`, or an item title ranks `wiki_pages.type = item` above source summaries.
2. Query `건브 무기` does not rank Black Mage or unrelated job guide above relevant item pages when item pages exist.
3. Answer payload includes official URL/provenance from the item wiki page.
4. Missing acquisition data produces an explicit absence statement.
5. Existing non-item job guide query still returns job wiki/source context.
6. JSON output format remains backward-compatible.

## Implementation requirements

- Prefer small ranking boosts/filters over a separate retrieval stack.
- Keep item behavior conditional on item pages existing.
- Do not hard-code one item id as the only answer path.
- Avoid raw HTML dumps in answers.
- Do not add LLM extraction or vector DB.

## Verification commands

    python -m unittest tests.test_guide_ff14_item_retrieval -v

Also run any existing ask/retrieval tests.

## Done criteria

- Item retrieval tests pass.
- Existing ask behavior is not regressed.
- Answers remain grounded in generated wiki/source context.

## Agent prompt

Implement only item-aware retrieval behavior for `tools/ask.py`. First write red tests in `tests/test_guide_ff14_item_retrieval.py` using a small temp wiki/FTS dataset. Cover item page ranking for item/weapon/gunblade queries, preventing unrelated job guide dominance, official URL provenance in answer output, explicit missing-acquisition wording, unchanged non-item job queries, and backward-compatible JSON output. Confirm the tests fail for missing item retrieval behavior. Then minimally adjust the existing retrieval/ranking logic. Do not add vector DB, LLM extraction, or raw HTML dumping. Run the targeted retrieval tests and existing ask tests.

---

# Task 09 — Runbook, quality gate, and final finish workflow

## Goal

Document the v09 operating procedure and run the final task completion workflow.

## Primary deliverables

- `docs/runbooks/guide-ff14-crawler.md`
- any required updates to `docs/specs/0011-v09-guide-ff14-official-db-crawler.md` status if the repo workflow expects status updates
- final task report

## Required runbook sections

- robots/access check
- category-map dry run
- item pilot dry run
- item pilot apply with `--limit 1`
- item wiki generation
- FTS reindex
- graph report
- ask smoke
- rollback/cleanup notes

## Manual smoke commands

These commands should be documented as manual/network-approved only:

    python tools/crawl_guide_ff14.py category-map --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --apply
    python tools/generate_item_wiki.py --verbose
    python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
    python tools/ask.py "건브 무기 source 보여줘" --format json

## Red test requirement

No new product red test is required if Tasks 01-08 already created the behavioral coverage. However, docs freshness should fail if docs are stale under the repo’s existing workflow. If there is an existing docs freshness test, run it before and after runbook changes.

## Verification commands

Required final gate:

    python -m unittest tests.test_guide_ff14_category_map -v
    python -m unittest tests.test_guide_ff14_item_extractor -v
    python -m unittest tests.test_guide_ff14_crawler -v
    python -m unittest tests.test_guide_ff14_item_wiki -v
    python -m unittest tests.test_guide_ff14_item_retrieval -v
    python scripts/check_docs_freshness.py --all
    python scripts/finish_task.py

If Task 01 or Task 07 added additional test modules, include them too:

    python -m unittest tests.test_guide_ff14_storage -v
    python -m unittest tests.test_guide_ff14_item_graph -v

## Done criteria

- Runbook exists and is specific enough to operate v09 safely.
- Quality gate commands are documented.
- Final report lists all tests run and whether manual smoke was skipped or executed.
- `scripts/finish_task.py` completes successfully, or any failure is explained with exact output.

## Agent prompt

Finalize v09 documentation and quality gates. Add `docs/runbooks/guide-ff14-crawler.md` with sections for robots/access check, category-map dry run, item pilot dry run, item pilot apply with `--limit 1`, item wiki generation, FTS reindex, graph report, ask smoke, and rollback/cleanup notes. Document that live network smoke requires maintainer-approved crawl scope. Then run all required v09 unit tests, docs freshness, and `scripts/finish_task.py`. Do not implement new product behavior in this task unless a test or docs freshness failure reveals a small missed integration. Report changed files, tests run, manual smoke status, and remaining risks.

---

# Task 10 — Expansion-gate documentation only

## Goal

Document the next expansion tracks without implementing them. This task exists to prevent accidental over-expansion during v09.

## Scope

Allowed:

- Documentation placeholders for quest/recipe/gathering expansion.
- A short future-plan section in the runbook or spec.
- Explicit gate statement that expansion is blocked until item pilot passes.

Not allowed:

- `guide_quests` implementation
- `guide_recipes` implementation
- `guide_gathering_entries` implementation
- quest/recipe/gathering crawler modes
- quest/recipe/gathering wiki generators
- quest/recipe/gathering graph emitters

## Required future expansion outline

Quest expansion will eventually add:

- `guide_quests`
- `Quest`
- `QuestIssuer`
- `QuestLocation`
- `QuestReward`
- `REQUIRES_QUEST`
- `UNLOCKS_CONTENT`

Recipe expansion will eventually add:

- `guide_recipes`
- `Recipe`
- `CraftingJob`
- `Ingredient`
- `PRODUCES_ITEM`
- `REQUIRES_INGREDIENT`

Gathering expansion will eventually add:

- `guide_gathering_entries`
- `GatheringEntry`
- `GatheringNode`
- `GatheringJob`
- `Zone`
- `FOUND_AT_NODE`
- `GATHERED_BY`

## Red test requirement

No red test is required because this task should not implement behavior. If an agent tries to implement expansion behavior, stop and revert it.

## Verification commands

    git diff -- docs
    python scripts/check_docs_freshness.py --all

Run unit tests only if docs tooling requires it.

## Done criteria

- Expansion is documented as future work only.
- No new quest/recipe/gathering code exists.
- Item pilot gate remains the hard prerequisite.

## Agent prompt

Document only the v09 expansion gate. Add or refine docs stating that quest/recipe/gathering expansion is future work and must not start until all item pilot quality gates pass. Include the intended future entities and edges, but do not implement any quest, recipe, or gathering schema, crawler, extractor, wiki generator, graph logic, or retrieval behavior. Run docs freshness if available and report changed docs only.

---

# Cross-task red test policy

Use this policy for every implementation task:

- A red test is required whenever a task introduces new behavior, changes behavior, or fixes a known regression.
- A red test is not required for pure inspection or docs-only tasks.
- A red test must fail for the expected reason before implementation.
- Do not count syntax errors, import errors from wrong paths, or broken fixtures as valid red failures.
- Prefer small fixture-driven unit tests over live integration tests.
- Network behavior must be represented with fake clients in unit tests.
- Manual network smoke belongs in `docs/runbooks/guide-ff14-crawler.md` only.
- Each task should finish with a short report:
  - changed files
  - tests added
  - red failure observed
  - implementation summary
  - tests passing
  - risks/limitations

# Existing workflow policy to preserve

The implementation should preserve the project’s existing docs-first workflow:

- Treat the spec as the source of truth.
- Do not silently change scope.
- Before coding, inspect existing docs and repo conventions.
- Use task-sized commits or task-sized handoffs.
- Keep generated artifacts out of commits unless the repo explicitly tracks them.
- For every task, run the smallest targeted tests first, then broader gates.
- Keep `implementation.md` and the spec aligned when behavior changes.
- Run `python scripts/check_docs_freshness.py --all` before marking the work complete.
- Run `python scripts/finish_task.py` at the final quality gate.

# Final v09 quality gate

Run before marking v09 complete:

    python -m unittest tests.test_guide_ff14_category_map -v
    python -m unittest tests.test_guide_ff14_item_extractor -v
    python -m unittest tests.test_guide_ff14_crawler -v
    python -m unittest tests.test_guide_ff14_item_wiki -v
    python -m unittest tests.test_guide_ff14_item_retrieval -v
    python scripts/check_docs_freshness.py --all
    python scripts/finish_task.py

Also run these if added:

    python -m unittest tests.test_guide_ff14_storage -v
    python -m unittest tests.test_guide_ff14_fetcher -v
    python -m unittest tests.test_guide_ff14_item_graph -v

Manual network smoke only after maintainer approval:

    python tools/crawl_guide_ff14.py category-map --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --dry-run
    python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --apply
    python tools/generate_item_wiki.py --verbose
    python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
    python tools/ask.py "건브 무기 source 보여줘" --format json

# Completion criteria

v09 is complete only when:

- Category map extraction works against fixtures and live dry-run.
- Item pilot crawl can fetch and parse a bounded item category.
- Structured item rows are stored in SQLite.
- `wiki/items` derived wiki exists.
- Item pages are searchable through FTS.
- Graph report includes item entities.
- Ask can answer item lookup questions with official guide provenance.
- No broad raw HTML dump appears in answers.
- Quest/recipe/gathering expansion remains blocked until item pilot quality gates pass.
