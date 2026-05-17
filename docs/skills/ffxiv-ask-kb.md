# ffxiv-ask-kb

## Purpose

Use this skill when the user asks OpenClaw to answer, search, explain, compare,
or show source evidence from the current FFXIV KB.

## Trigger

Examples:

- "건브 7.5 변경점 알려줘."
- "No Mercy 관련 변경 있어?"
- "7.5에서 어떤 직업이 언급됐어?"
- "건브 관련 source 보여줘."

Do not use this skill to save a new source, rebuild the KB, update Notion, or
find latest info from the web.

## Command

Always use JSON output first:

```bash
python tools/ask.py "<question>" --format json
```

Optional diagnostic mode:

```bash
python tools/ask.py "<question>" --format json --debug
```

## Output Handling

Parse stdout as JSON and inspect:

- `status`
- `contexts`
- `contexts[].wiki_type`
- `contexts[].path`
- `contexts[].source_ids`
- `answer.body`
- `answer.confidence`
- `answer.sources`

If `status=ok` and `contexts` is non-empty, answer from `answer.body` and cite
the relevant paths/source ids.

If contexts is empty, say the current KB did not find relevant context and ask
whether the user wants to provide a source.

## Guardrails

- Do not answer from memory when the user asked the KB.
- Do not call an LLM API to fill missing facts.
- Do not infer changes not present in `contexts`, `source_ids`, or
  `answer.sources`.
- Do not run `process_source.py` unless the user is adding a new source.
