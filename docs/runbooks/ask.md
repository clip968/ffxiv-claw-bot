# Ask Pipeline Runbook

`tools/ask.py` is the grounded ask entrypoint. It connects the knowledge base
outputs to a deterministic question-answering path, and uses the v0.8 domain
graph when generated graph exports are available.

Flow:

```text
question
-> parse_query()
-> build_retrieval_plan()
-> execute_retrieval_plan()
-> execute_graph_aware_retrieval() when graph/entity_index.json exists
-> build_context_pack()
-> compose_answer()
-> JSON or text stdout
```

The command does not crawl, poll, call Discord, or call an LLM.

## CLI Examples

JSON output:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json
```

Text output:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format text
```

Debug output:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --debug
```

Custom DB/root:

```bash
python tools/ask.py "GNB change history" --db-path db/ffxiv.sqlite --root-path . --graph-dir graph
```

Limit context count:

```bash
python tools/ask.py "GNB change history" --limit 3
```

## JSON Output

Normal JSON output has stable top-level keys:

```json
{
  "status": "ok",
  "question": "7.x 건브레이커 변경 이력 알려줘",
  "contexts": [],
  "answer": {
    "format": "text",
    "body": "현재 KB에서 관련 KB 문서를 찾지 못했습니다.\ncontext에 없는 내용은 추정하지 않았습니다.\n\n확실도:\nN/A",
    "confidence": "N/A",
    "sources": []
  },
  "actions": []
}
```

Error output:

```json
{
  "status": "error",
  "question": "",
  "error_stage": "parse",
  "error_message": "question must not be empty",
  "actions": []
}
```

## Text Output

`--format text` prints `answer.body` only. It does not wrap the answer in JSON.

No-context example:

```text
현재 KB에서 관련 KB 문서를 찾지 못했습니다.
context에 없는 내용은 추정하지 않았습니다.

확실도:
N/A
```

Grounded context output contains:

```text
핵심 답변

요약
- ...

관련 항목
- Job: ...
- Patch: ...
- Skill: ...

확인된 내용
- ...

근거 문서
- wiki/jobs/gunbreaker.md
- patch_7_0

확실도
source_grounded

주의
- context에 없는 내용은 추정하지 않았습니다.
```

## Debug Mode

`--debug` adds these fields to JSON output:

- `parsed_query`
- `retrieval_plan`

Debug mode is intended for local verification and agent handoff. Text mode does
not expose debug fields.

## Retrieval Policy

Job change history queries use the job catalog aliases to build an FTS OR query.

Primary target:

```text
wiki_type=job
topic=<job-slug>
```

Fallback targets:

```text
wiki_type=source_summary
wiki_type=None
```

If a primary target returns results, fallback targets are skipped. If primary
returns no results, fallback targets run in priority order. Results are
deduplicated by `page_id` and limited by `--limit`.

## Graph-Aware Retrieval

When `graph/entity_index.json` exists, the ask pipeline adds graph-aware
retrieval after the FTS retrieval plan:

```text
question
-> entity_index alias match
-> graph neighborhood retrieval
-> FTS and graph result merge
-> context pack
```

Graph retrieval is additive. If the graph index is missing, no entity alias
matches the question, or SQLite graph access fails, the pipeline returns the
original FTS results unchanged.

Merge behavior:

- FTS results keep their original order and score.
- Fact-backed graph results use a stronger score than mention-only graph
  results.
- Results are deduplicated by `page_id`, and direct source summary results are
  deduplicated by `source_id`.
- Derived job pages may mention source ids, but those references do not hide the
  original graph source summary context.
- Final context candidates are capped at the graph-aware retrieval limit.

If `graph/entity_index.json` is absent, ask still works as an FTS-only grounded
answer path. In that mode, entity-page fallback and graph neighborhood facts are
not available.

v08.5 smoke queries:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

JSON smoke checks:

- `status` is `ok`
- `contexts` is non-empty for known entity queries
- `answer.body` contains `요약`, `관련 항목`, `근거 문서`, and `주의`

## Job Wiki First

When `wiki/jobs/<job>.md` exists and is indexed, job change history questions
should return that job wiki as the first context.

Example verified by tests:

```text
question: 7.x 건브레이커 변경 이력 알려줘
first context: wiki/jobs/gunbreaker.md
```

## Source Summary Fallback

When no matching job wiki exists, the ask pipeline searches source summaries.

Example verified by tests:

```text
question: 7.x 건브레이커 변경 이력 알려줘
first context type: source_summary
```

Older summary rows may use `wiki_type=summary`; the generic fallback can still
return them, but newly indexed source summary pages use `source_summary`.

## No-Context Behavior

If no relevant context is found, the answer must not invent facts. It returns a
no-context message and `confidence=N/A`.

## Answer Composition

`compose_answer()` is deterministic and does not call an LLM. It uses the
retrieved context metadata to classify related `Job`, `Patch`, and `Skill`
pages, extracts a small set of evidence lines from context excerpts, and then
renders these sections:

- `요약`
- `관련 항목`
- `확인된 내용`
- `근거 문서`
- `확실도`
- `주의`

The answer body must not append full source bodies or whole generated wiki
documents. Source paths and source ids belong in `근거 문서`; uncertainty about
sparse context belongs in `주의`.

## Known Limitations

- No crawling, polling, official patchnote watcher, scheduler, or Discord command.
- No LLM generation and no vector/embedding search.
- Numeric patch range parsing only. Expansion names are not mapped in v0.7.
- Deterministic answer composition extracts short evidence lines only; answer
  quality still depends on the quality of generated wiki pages and source
  summaries.
- Graph-aware retrieval is additive and depends on generated v0.8 graph exports.

## Verification

Focused v0.7 CLI tests:

```bash
python -m unittest tests.test_v07_ask_cli -v
```

Focused v0.8 hybrid retrieval tests:

```bash
python -m unittest tests.test_hybrid_retrieval -v
python -m unittest tests.test_v08_e2e -v
```

Focused v0.8.5 answer quality tests:

```bash
python -m unittest tests.test_v08_5_answer_quality -v
```

Full completion gate:

```bash
python scripts/finish_task.py
```
