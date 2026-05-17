# Domain Graph Refresh Runbook

This runbook refreshes the v08.5 managed wiki KB from local source summaries.
It does not crawl external sites, call an LLM, or publish generated graph/wiki
artifacts.

## Purpose

Refresh this pipeline:

```text
wiki/source_summaries/
-> source summary audit
-> domain graph rebuild
-> graph export and report
-> graph-derived wiki generation
-> SQLite FTS re-index
-> ask smoke tests
-> regression gate
```

## Preconditions

- Work from the repo root.
- `wiki/source_summaries/*.md` exists and has been reviewed for source quality.
- `data/ffxiv_entities/*.json` contains the entity registry.
- `db/ffxiv.sqlite` is local state and is not committed.
- Generated graph/wiki outputs under `graph/`, `wiki/jobs/`, `wiki/patches/`,
  and `wiki/skills/` are local derived outputs and are not committed.

## Step 1. Source Summary Audit

Check source summary volume and obvious contamination before rebuilding:

```bash
python -c "from pathlib import Path; files=sorted(Path('wiki/source_summaries').glob('*.md')); print(len(files)); [print(path) for path in files[:10]]"
```

For v08.5 activation, the recorded audit is:

- `docs/reports/2026-05-17-v08_5-source-audit.md`
- 26 source summaries
- 20 usable FFXIV summaries
- 6 too-short/review summaries
- 0 non-FFXIV contamination
- 0 duplicate content hashes

## Step 2. Dry-Run Rebuild

Preview the rebuild before mutating graph tables:

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
```

Expected shape:

- JSON `status=ok`
- planned source count is nonzero
- planned registry node count is nonzero

## Step 3. Reset Rebuild

Rebuild the graph tables and exports from source summaries:

```bash
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
```

v08.5 activation snapshot:

- sources: 26
- facts: 14
- graph nodes: 78
- graph edges: 339
- node types include `Job`, `Patch`, `Skill`, `Fact`, `SourceDocument`, `WikiPage`
- edge types include `MENTIONS`, `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL`

Run the rebuild twice when checking idempotency. Node and edge counts should
remain stable.

## Step 4. Graph Report

Generate the graph report:

```bash
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

Review `graph/GRAPH_REPORT.md` locally. The report is generated output and is
not committed.

v08.5 report review:

- `docs/reports/2026-05-17-v08_5-graph-report-review.md`
- report status: `ok`
- warning: 2 entities without mentions (`skill:fight_or_flight`, `skill:no_mercy`)

## Step 5. Derived Wiki Generation

Preview generated wiki pages:

```bash
python tools/generate_derived_wiki.py --dry-run --verbose
```

Generate pages:

```bash
python tools/generate_derived_wiki.py --verbose
```

Expected generated directories:

- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`
- `wiki/index.md`

`wiki/index.md` is tracked as the generated wiki index. The per-entity generated
pages are local derived outputs and are ignored by Git.

## Step 6. FTS Re-Index

Index source summaries and generated wiki pages into SQLite FTS:

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

v08.5 activation snapshot:

- indexed: 38
- source summaries: 26
- jobs: 5
- patches: 3
- skills: 4

## Step 7. Ask Smoke Tests

Run representative ask checks:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

Expected shape:

- JSON `status=ok`
- `contexts` is non-empty for known entities
- `answer.body` starts with structured sections such as `요약`, `관련 항목`,
  `확인된 내용`, `근거 문서`, and `주의`

## Step 8. Regression

Focused v08.5 tests:

```bash
python -m unittest tests.test_v08_5_real_graph_population -v
python -m unittest tests.test_v08_5_real_derived_wiki -v
python -m unittest tests.test_v08_5_fts_visibility -v
python -m unittest tests.test_v08_5_answer_quality -v
```

Full completion gate:

```bash
python scripts/finish_task.py
```

## Troubleshooting

Dry-run reports zero sources:

- Confirm `wiki/source_summaries/*.md` exists.
- Confirm the command is running from repo root or pass `--wiki-root`.

Graph report has missing entity warnings:

- Review whether the entity is in the registry but not mentioned by current
  source summaries.
- Do not fabricate source mentions to silence warnings.

Ask returns no contexts:

- Re-run FTS re-index.
- Confirm `graph/entity_index.json` exists for graph-aware entity matching.
- Confirm generated pages are present locally under `wiki/jobs`, `wiki/patches`,
  and `wiki/skills`.

Answer body looks like raw source dump:

- Run `python -m unittest tests.test_v08_5_answer_quality -v`.
- Check `src/answering/composer.py`.

## Completion Checklist

- [ ] source summary audit reviewed
- [ ] dry-run rebuild returned `status=ok`
- [ ] reset rebuild returned `status=ok`
- [ ] graph report reviewed
- [ ] derived wiki generated
- [ ] FTS re-index returned `status=ok`
- [ ] ask smoke tests returned `status=ok`
- [ ] focused v08.5 tests passed
- [ ] `python scripts/finish_task.py` passed
