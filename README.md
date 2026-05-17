# ffxiv-claw-bot

파이널판타지14 전용 로컬 지식 베이스와 OpenClaw/Discord agent를 위한 repo다. 원본 자료는 로컬 저장소에 보관하고, repo는 처리 pipeline, SQLite FTS, graph, derived wiki 문서를 관리한다.

## Current Pipeline

기본 source of truth:

- 원본 파일 저장소: `/mnt/d/ffixiv-bot-storage`
- 구현/문서 계약: `docs/`
- 로컬 DB: `db/ffxiv.sqlite`
- source summary: `wiki/source_summaries/`
- domain graph export/report: `graph/`
- graph-derived wiki: `wiki/jobs/`, `wiki/patches/`, `wiki/skills/`
- ask entrypoint: `tools/ask.py`

v08.5 managed wiki KB pipeline:

```text
local source / URL / queued source
-> source summary generation
-> wiki/source_summaries/ audit
-> tools/rebuild_domain_graph.py --reset-domain-graph
-> graph nodes/edges and graph export/report
-> tools/generate_derived_wiki.py
-> wiki/jobs, wiki/patches, wiki/skills, wiki/index.md
-> tools.compile_wiki.index_wiki_documents()
-> tools/ask.py graph-aware grounded answer
```

`db/ffxiv.sqlite`, generated graph JSON/report files, and generated per-entity
wiki pages are local derived state. Do not commit them unless a future spec
explicitly changes that policy.

## Legacy Source Processing Pipeline

v0.6 pipeline:

```text
local source / URL / queued source
-> tools/process_source.py
-> extractor registry for local files
-> Local Storage ingest
-> source summary, FTS, graph rebuild
-> optional derived wiki generation
-> optional derived wiki FTS indexing
```

## Source Formats

Local file sources are normalized through `src/source_processing/`.

Supported extensions:

- `.txt`
- `.md`
- `.html`
- `.htm`
- `.csv`
- `.xlsx`

Unsupported extensions fail with `status=error` and `error_stage=extract`. PDF, DOCX, image OCR, scanned PDF OCR, scheduler/daemon behavior, and LLM-based derived summaries are not part of v0.6.

## Common Commands

Process one source:

```bash
python tools/process_source.py --apply --source-type markdown_file --category patch_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/patch.md"
python tools/process_source.py --apply --source-type binary_attachment --category bis_sheets --local-path "/mnt/d/ffixiv-bot-storage/incoming/bis.xlsx"
python tools/process_source.py --apply --source-type url --category patch_notes --url "https://na.finalfantasyxiv.com/lodestone/..."
```

Process queued sources:

```bash
python tools/process_pending_sources.py --dry-run --limit 10
python tools/process_pending_sources.py --limit 10
python tools/process_pending_sources.py --retry-errors --max-retry 3 --limit 10
python tools/process_pending_sources.py --build-derived-wiki --limit 10
```

Generate derived wiki:

```bash
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/generate_derived_wiki.py --verbose
```

Index source summaries and generated wiki files into FTS from Python:

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

Ask the local KB:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

Legacy v0.6 job wiki commands remain available:

```bash
python tools/generate_job_wiki.py --job gunbreaker
python tools/generate_job_wiki.py --all
python tools/generate_derived_wiki.py --kind jobs
```

## Documentation

Start with:

- `docs/WORKFLOW.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`
- `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`
- `docs/runbooks/domain-graph-refresh.md`
- `docs/runbooks/ask.md`
- `docs/runbooks/generate-derived-wiki.md`
- `docs/runbooks/process-source.md`
- `docs/runbooks/process-pending-sources.md`

Before finishing a task:

```bash
python scripts/check_docs_freshness.py --all
python -m unittest discover -s tests -p "test_*.py"
python scripts/finish_task.py
```
