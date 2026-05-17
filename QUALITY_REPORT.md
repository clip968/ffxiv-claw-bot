# v08.5 Precision Hardening Quality Report

Date: 2026-05-17

## Scope

- No additional source crawling was performed.
- Official job guide extraction now removes cross-job nav/menu text and records job metadata.
- Official job guide source summaries are tagged with job metadata during indexing and graph rebuild.
- `parsed.job` queries hard-filter other official job guide source summaries.
- Job change questions prefer patch/fact context ahead of official job guide source summaries.
- Answer evidence extraction removes structural and unrelated patch-menu noise.

## Red Test

Command:

```bash
python -m unittest tests.test_v08_5_precision_regression -v
```

Expected red result before implementation:

- 6 tests executed
- 5 failures, 1 error
- Failures covered missing official job metadata, cross-job job guide context, and composer noise such as `title:`, `Recast`, `Solution Nine`, and leve client lines.

## Rebuild And Counts

Commands:

```bash
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --verbose
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

Results:

- domain graph rebuild: `status=ok`, `sources=31`, `facts=19`, export `nodes=105`, export `edges=396`, report `warnings=1`
- graph report: `status=ok`, `warnings=1`
- derived wiki: `status=ok`, generated 5 jobs, 3 patches, 4 skills
- FTS re-index: `status=ok`, `indexed=43`
- wiki pages: `source_summary=31`, `job=5`, `patch=3`, `skill=4`
- SQLite counts: `sources=29`, `wiki_pages=43`, `wiki_fts=43`, `graph_nodes=105`, `graph_edges=487`

## Actual Ask Checks

All eight checks used `python tools/ask.py <query> --format json`.

| Query | Status | Contexts | Precision result |
|---|---:|---:|---|
| `Gunbreaker 스킬 알려줘` | ok | 8 | no Black Mage job guide context |
| `Paladin 스킬 알려줘` | ok | 8 | no Black Mage/Gunbreaker job guide context |
| `건브 7.5 변경점` | ok | 7 | answer has no `title: Official FFXIV Job Guide - Black Mage` |
| `Continuation 관련 변경 있어?` | ok | 4 | answer has no Solution Nine or leve client noise |
| `건브 7.5 변경점 알려줘` | ok | 7 | patch/fact context first |
| `No Mercy 관련 변경 있어?` | ok | 2 | no cross-job guide contamination |
| `7.5에서 어떤 직업이 언급됐어?` | ok | 8 | broad patch/job query returns contexts |
| `건브 관련 source 보여줘` | ok | 8 | no Black Mage job guide context |

## Automated Tests

Commands:

```bash
python -m unittest tests.test_v08_5_precision_regression tests.test_v08_5_real_graph_population tests.test_v08_5_real_derived_wiki tests.test_v08_5_fts_visibility tests.test_v08_5_answer_quality -v
python -m unittest tests.test_v06_extractors tests.test_v06_fts_indexing -v
python -m unittest tests.test_v07_query_parser tests.test_v07_retrieval tests.test_v07_context_builder tests.test_v07_answer_composer tests.test_v07_ask_cli -v
python -m unittest tests.test_v08_e2e tests.test_hybrid_retrieval tests.test_domain_graph_rebuild tests.test_graph_report tests.test_derived_wiki -v
python -m unittest discover -s tests -p "test_*.py"
```

Results:

- v08.5 focused precision/regression: 29 tests OK
- v06 extractor/FTS regression: 39 tests OK
- v07 ask pipeline regression: 51 tests OK
- v08 graph/retrieval regression: 43 tests OK
- full unittest discovery: 367 tests OK

## Final Gate

Commands:

```bash
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

Results:

- docs freshness: OK (`changed files=18`, `code files=11`, `docs files=6`, `doc owner rules=15`)
- finish task: OK (`367 tests OK`, docs freshness OK, Notion handoff dry-run OK)
