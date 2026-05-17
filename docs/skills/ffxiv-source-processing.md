# ffxiv-source-processing

## Purpose

Use this skill when the user asks OpenClaw to add a provided source to the FFXIV Knowledge Base. OpenClaw owns interpretation and reporting; `python tools/process_source.py` owns repo execution.

## Trigger

Use this skill when the request includes a source and an intent to save, ingest, index, or reflect it in the KB.

Examples:

- "이 URL을 patch_notes로 저장하고 KB에 반영해줘."
- "이 로컬 markdown 파일을 raid_guides로 ingest해줘."
- "이 텍스트 메모를 personal_notes로 저장하고 검색 가능하게 만들어줘."

Do not use this skill for broad crawling, scheduled polling, search-engine lookup, Discord slash command runtime, or vector/embedding work.
Do not use this skill for KB questions; use `ffxiv-ask-kb` instead.

## Source Type Rules

- URL input: use `source_type=url` and pass `--url`.
- Direct text memo: use `source_type=text_note` and pass `--body`.
- Local `.md` file: use `source_type=markdown_file` and pass `--local-path`.
- Local `.txt` file: use `source_type=plain_text_file` and pass `--local-path`.
- Other local attachments: use `source_type=binary_attachment` and pass `--local-path` only when the extension is supported by the extractor registry.

## Category Rules

Supported categories:

- `urls`
- `documents`
- `sheets`
- `patch_notes`
- `raid_guides`
- `job_guides`
- `static_docs`
- `macros`
- `bis_sheets`
- `personal_notes`

Infer obvious categories from the user's wording:

- patch notes, release notes, update notes -> `patch_notes`
- raid guides, encounter guides, fight notes -> `raid_guides`
- job or rotation guides -> `job_guides`
- macros -> `macros`
- personal notes, reminders, private notes -> `personal_notes`

Do not silently default ambiguous content to `personal_notes`.

## Ambiguity Handling

Ask a clarifying question before calling `process_source.py` when:

- category is unclear
- the text could be either a URL or a normal note
- a file path does not exist
- source type cannot be determined
- the user asks to "find the latest info" but does not provide a source

If the user clearly provides category and source input, run without extra confirmation.

## Command Construction

Prefer `python tools/process_source.py` over calling individual ingest, rebuild, graph, or status tools. Do not call tools/ingest_local.py directly for normal OpenClaw source-processing requests.

Text note:

```bash
python tools/process_source.py \
  --apply \
  --source-type text_note \
  --category personal_notes \
  --title "P12S Reprisal note" \
  --body "Use Reprisal before raidwide."
```

URL:

```bash
python tools/process_source.py \
  --apply \
  --source-type url \
  --category patch_notes \
  --url "https://example.com/ffxiv/patch-note"
```

Markdown file:

```bash
python tools/process_source.py \
  --apply \
  --source-type markdown_file \
  --category raid_guides \
  --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"
```

Binary/table attachment:

```bash
python tools/process_source.py \
  --apply \
  --source-type binary_attachment \
  --category bis_sheets \
  --local-path "/mnt/d/ffixiv-bot-storage/incoming/bis.xlsx"
```

Dry run:

```bash
python tools/process_source.py \
  --dry-run \
  --source-type text_note \
  --category personal_notes \
  --title "Dry run note" \
  --body "This should not be persisted."
```

## Output Handling

Parse stdout as JSON. Report the short result to the user:

- `status`
- `source_id`
- `category`
- `graph_status`
- `wiki_path`
- `summary.next_action`

If the result includes `notion_update`, OpenClaw may use that payload to update the Notion source/status database. Never put full source body, raw HTML, attachment bytes, or large binary data into Notion.

If `status=error`, report `summary.message`, `summary.next_action`, and the first failed action error. Use individual repo tools only for diagnosis after `process_source.py` fails.
