# ffxiv-kb-refresh

## Purpose

Use this skill when the user asks OpenClaw to refresh, rebuild, regenerate, or
validate the local FFXIV KB graph/wiki/search pipeline.

## Trigger

Examples:

- "KB 최신화해줘."
- "domain graph 다시 빌드해줘."
- "derived wiki 재생성하고 FTS까지 반영해줘."
- "지금 source summaries 기준으로 ask가 되게 갱신해줘."

Do not use this skill for a normal KB question or for adding one source. Use
`ffxiv-ask-kb` or `ffxiv-source-processing` instead.

## Required Sequence

Preview graph rebuild:

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
```

Apply graph rebuild:

```bash
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
```

Generate graph report:

```bash
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

Preview derived wiki:

```bash
python tools/generate_derived_wiki.py --dry-run --verbose
```

Apply derived wiki:

```bash
python tools/generate_derived_wiki.py --verbose
```

Re-index FTS:

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

Run ask smoke:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
```

## Guardrails

- Do not commit generated graph/wiki outputs under `graph/`, `wiki/jobs/`,
  `wiki/patches/`, or `wiki/skills`.
- `wiki/index.md` may be tracked when the generator updates it.
- Do not crawl, schedule, or call an LLM API.
- If a step fails, stop and report the failed command, stage, and next action.

## Verification

```bash
python -m unittest tests.test_v08_5_real_graph_population tests.test_v08_5_real_derived_wiki tests.test_v08_5_fts_visibility tests.test_v08_5_answer_quality -v
python scripts/finish_task.py
```
