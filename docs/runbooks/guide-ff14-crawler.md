# guide.ff14.co.kr Crawler Runbook

This runbook operates the v09 official DB item pilot pipeline. It is bounded to
`guide.ff14.co.kr`, uses GET-only fetches, and does not add a scheduler,
Discord runtime, vector DB, external graph DB, market data, or LLM extraction.

## Purpose

Refresh this local item pilot pipeline:

```text
guide.ff14.co.kr official DB
-> category-map dry run
-> bounded item-pilot crawl
-> raw HTML snapshots + SQLite guide tables
-> wiki/items generated pages
-> wiki_pages/wiki_fts re-index
-> domain graph item nodes/edges
-> item-aware ask smoke
```

## Preconditions

- Work from the repo root.
- Live network smoke requires maintainer-approved crawl scope.
- Keep `--limit` small for manual smoke. Use `--limit 1` unless the maintainer
  explicitly approves a larger bounded run.
- Generated outputs are local state and are not committed:
  - `data/raw/guide_ff14/`
  - `db/ffxiv.sqlite`
  - `wiki/items/`
  - `graph/*.json`
  - `graph/GRAPH_REPORT.md`
- Unit tests and normal quality gates do not use live network.

## Step 1. Robots And Access Check

Manual/network-approved only:

```bash
python -c "from dataclasses import asdict; from src.guide_ff14.fetcher import GuideFetcher; import json; print(json.dumps(asdict(GuideFetcher().fetch_robots()), ensure_ascii=False, indent=2))"
```

Expected shape:

- JSON object has `status=ok` when robots.txt is reachable.
- `url` is `https://guide.ff14.co.kr/robots.txt`.
- The fetcher rejects non-`guide.ff14.co.kr` hosts before HTTP.

Stop if access is blocked, robots/access policy is unclear, or the maintainer
has not approved live crawl scope.

## Step 2. Category-Map Dry Run

Manual/network-approved only:

```bash
python tools/crawl_guide_ff14.py category-map --dry-run
```

Expected shape:

- JSON `status=planned`
- `root_url` is `https://guide.ff14.co.kr/lodestone/db/item`
- `categories` contains normalized official DB category URLs
- command does not mutate DB, raw files, wiki files, graph files, or crawl state

Review the category URL before using it for `item-pilot`.

## Step 3. Item Pilot Dry Run

Manual/network-approved only:

```bash
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --dry-run
```

Expected shape:

- JSON `status=planned`
- `dry_run=true`
- planned detail URLs are bounded by `--limit`
- no DB rows, raw snapshots, wiki pages, or graph files are written

## Step 4. Item Pilot Apply

Manual/network-approved only:

```bash
python tools/crawl_guide_ff14.py item-pilot --category-url "https://guide.ff14.co.kr/lodestone/db/item?category2=1&category3=110" --limit 1 --apply
```

Expected shape:

- JSON `status=ok` or `status=partial` with structured per-detail errors
- `guide_crawl_pages`, `guide_categories`, `guide_items`, and
  `guide_item_sources` are updated idempotently
- raw snapshots are written under `data/raw/guide_ff14/`
- repeated apply with the same input does not duplicate rows

Stop and inspect `errors` before increasing `--limit`.

## Step 5. Item Wiki Generation

Preview:

```bash
python tools/generate_item_wiki.py --dry-run --verbose
```

Apply:

```bash
python tools/generate_item_wiki.py --verbose
```

Expected generated files:

- `wiki/items/index.md`
- `wiki/items/categories/*.md`
- `wiki/items/*.md`
- `wiki/index.md` contains an item wiki link

Generated `wiki/items` pages are local derived output and are not committed.

## Step 6. FTS Re-Index

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

Expected shape:

- JSON `status=ok`
- `summary.item` is nonzero after item wiki pages exist
- item pages have `wiki_pages.type = item`

## Step 7. Domain Graph Refresh

Rebuild graph tables and exports:

```bash
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
```

Generate/review graph report:

```bash
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

Expected shape after item rows exist:

- graph report includes nonzero `Item` count
- item nodes link to category, equipment job, source, level, and provenance
  edges where data exists
- generated graph outputs remain local and are not committed

## Step 8. Ask Smoke

Manual/local smoke after item pages are generated and indexed:

```bash
python tools/ask.py "건브 무기 source 보여줘" --format json
python tools/ask.py "아이템 레벨 700 이상 건블레이드 보여줘" --format json
python tools/ask.py "영웅의 건블레이드 어디서 얻어?" --format json
```

Expected shape:

- JSON `status=ok`
- item questions prefer `wiki_type=item` contexts when item pages exist
- answer body includes `근거 문서`
- official guide URL appears when the item page has one
- missing acquisition data is stated explicitly instead of inferred

## Step 9. Automated Regression Gate

Run focused v09 tests:

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

Run repo gates:

```bash
git diff --check
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

## Rollback And Cleanup

If a manual smoke run produces bad local state:

- Do not commit generated outputs.
- Remove or archive local generated paths with recoverable tooling when possible.
- Re-run `python tools/init_db.py` if schema init needs to be restored.
- Re-run the relevant generator/indexer after correcting the source rows.
- If generated item pages are stale, regenerate with
  `python tools/generate_item_wiki.py --verbose` and re-run FTS indexing.
- If graph output is stale, re-run `python tools/rebuild_domain_graph.py --reset-domain-graph --verbose`.

Do not delete tracked docs or source files as cleanup for generated crawler
state.

## Completion Checklist

- [ ] maintainer-approved live scope confirmed or manual network smoke skipped
- [ ] robots/access check reviewed if live smoke was approved
- [ ] category-map dry run reviewed
- [ ] item-pilot dry run reviewed
- [ ] item-pilot apply with `--limit 1` reviewed
- [ ] item wiki generated
- [ ] FTS re-index returned `status=ok`
- [ ] graph report reviewed
- [ ] ask smoke returned `status=ok`
- [ ] focused v09 tests passed
- [ ] `python scripts/finish_task.py` passed
