# Spec 0004: v0.5 Source Processing Pipeline

## 1. Goal

v0.5의 목표는 OpenClaw가 FFXIV Knowledge Base에 source를 추가할 때, 여러 도구를 수동으로 이어 붙이지 않고 안정적으로 처리할 수 있는 source processing pipeline을 고정하는 것이다.

v0.5는 다음 두 층을 함께 정의한다.

1. OpenClaw Skill Layer  
   사용자의 요청을 해석하고, source type/category/title/body/url/file path를 결정하며, 처리 workflow를 호출한다.

2. Repo Execution Layer  
   실제 ingest, rebuild, FTS 갱신, graph build, status 계산, Notion update payload 생성을 코드와 테스트로 보장한다.

v0.5의 최종 목표는 다음 요청을 OpenClaw가 안정적으로 처리할 수 있게 만드는 것이다.

```text
이 URL을 patch_notes로 저장하고 KB에 반영해줘.
이 로컬 markdown 파일을 raid_guides로 ingest해줘.
이 텍스트 메모를 personal_notes로 저장하고 검색 가능하게 만들어줘.
```

v0.5는 완전 자동 크롤러가 아니다.  
사용자가 URL, 파일 경로, 텍스트 본문 같은 입력 source를 제공했을 때, 그것을 Knowledge Base에 반영하는 단일 처리 흐름을 만드는 단계다.

---

## 2. Non-Goals

v0.5에서는 다음을 구현하지 않는다.

- Notion DB polling loop
- Notion에서 `Status = New` 항목을 자동 감시하는 trigger loop
- allowlist crawler
- arbitrary web crawling
- scheduler 또는 daemon
- Discord slash command runtime
- vector DB
- embedding pipeline
- Google Drive 기본 경로 복구
- repo 내부에 원본 파일을 저장하는 구조
- Notion을 원본 파일 저장소로 사용하는 구조

위 항목은 v0.6 Automation Loop 이후의 범위다.

---

## 3. Background

현재 v0.4에서는 다음 기능들이 이미 분리된 도구로 존재한다.

- Local Storage ingest
- raw/local_storage snapshot 생성
- SQLite sources DB 등록
- wiki summary 생성
- FTS rebuild
- graph build
- Notion status payload 생성
- Notion DB read/write

하지만 현재 문제는 각 기능이 독립적으로 존재한다는 점이다.

현재 수동 흐름은 대략 다음과 같다.

```text
사용자 요청
→ OpenClaw가 source type 판단
→ ingest_local.py 실행
→ source_id 확인
→ local_rebuild.py 실행
→ graph 상태 확인
→ status_notification.py로 payload 생성
→ Notion API update
→ 사용자에게 결과 보고
```

이 흐름은 동작할 수 있지만, OpenClaw가 매번 여러 단계를 올바른 순서로 호출해야 하므로 실패 가능성이 높다.

v0.5는 이 흐름을 다음처럼 안정화한다.

```text
사용자 요청
→ OpenClaw Source Processing Skill
→ process_source.py
→ ingest
→ rebuild
→ status 계산
→ Notion update payload 생성
→ OpenClaw가 Notion update 및 결과 보고
```

---

## 4. Design Principle

v0.5의 핵심 원칙은 다음이다.

```text
OpenClaw = 판단
process_source.py = 실행
```

OpenClaw는 사용자의 자연어 요청을 해석한다.

예를 들어 다음을 판단한다.

- source type이 URL인지, 파일인지, 텍스트 메모인지
- category가 무엇인지
- title을 어떻게 정리할지
- 사용자가 제공한 정보가 충분한지
- 모호하면 질문해야 하는지
- 실행 결과를 사용자에게 어떻게 요약할지

반면 `process_source.py`는 판단을 최소화한다.  
입력받은 request를 검증하고, 정해진 pipeline을 실행한 뒤, machine-readable JSON을 반환한다.

---

## 5. Supported Source Types

v0.5에서 지원해야 하는 source type은 다음이다.

| Source Type | 설명 | 입력 |
|---|---|---|
| `text_note` | 사용자가 직접 제공한 짧은 텍스트 메모 | `--body` |
| `markdown_file` | 로컬 markdown 파일 | `--local-path` |
| `plain_text_file` | 로컬 plain text 파일 | `--local-path` |
| `url` | 웹 URL | `--url` |
| `binary_attachment` | PDF, 이미지, 기타 첨부 파일 | v0.5에서는 contract만 유지하고 완전 처리는 선택 사항 |

v0.5의 필수 완료 범위는 `text_note`, `markdown_file`, `plain_text_file`, `url`이다.

`binary_attachment`는 기존 ingest path와 충돌하지 않도록 schema는 유지하되, PDF parsing/OCR/문서 추출 자동화는 v0.5 범위가 아니다.

---

## 6. Categories

v0.5 pipeline은 다음 category를 기본으로 지원한다.

```text
urls
documents
sheets
patch_notes
raid_guides
job_guides
static_docs
macros
bis_sheets
personal_notes
```

OpenClaw skill은 사용자의 요청에서 category를 추론할 수 있다.

예시:

| 사용자 요청 | category |
|---|---|
| “이 패치노트 저장해줘” | `patch_notes` |
| “이 공략 문서 넣어줘” | `raid_guides` |
| “이 직업 가이드 저장해줘” | `job_guides` |
| “이 매크로 저장해줘” | `macros` |
| “이건 내 메모로 저장해줘” | `personal_notes` |

단, category가 애매한 경우 OpenClaw는 임의로 `personal_notes`에 넣지 말고 사용자에게 확인해야 한다.

---

## 7. Storage Model

v0.5는 v0.4의 Local Storage 구조를 유지한다.

원본 파일 저장소의 기준 경로는 다음이다.

```text
/mnt/d/ffixiv-bot-storage
```

repo 내부는 code와 derived artifacts 중심으로 유지한다.

```text
repo/
  db/ffxiv.sqlite
  raw/local_storage/...
  wiki/source_summaries/...
  graph/nodes.json
  graph/edges.json
```

외부 Local Storage는 원본 source 보관을 담당한다.

```text
/mnt/d/ffixiv-bot-storage/
  incoming/
  sources/
    urls/
    documents/
    sheets/
    patch_notes/
    raid_guides/
    job_guides/
    static_docs/
    macros/
    bis_sheets/
    personal_notes/
  exports/
  manifests/
  archive/
```

v0.5에서 Google Drive는 기본 저장소가 아니다.

---

## 8. OpenClaw Skill Layer

### 8.1 Skill Name

추천 skill 이름:

```text
ffxiv-source-processing
```

### 8.2 Skill Responsibility

OpenClaw Source Processing Skill은 다음을 담당한다.

1. 사용자 요청에서 source 입력을 식별한다.
2. source type을 결정한다.
3. category를 결정한다.
4. title을 생성하거나 정리한다.
5. 필요한 인자를 구성한다.
6. `process_source.py`를 호출한다.
7. 결과 JSON을 읽는다.
8. Notion update가 필요한 경우 Notion API를 호출한다.
9. 사용자에게 처리 결과를 요약한다.

### 8.3 Skill Input Rules

#### URL 요청

사용자가 URL을 제공하면 기본적으로 `source_type=url`로 처리한다.

```text
이 URL을 patch_notes로 저장해줘.
https://...
```

OpenClaw는 다음 request를 구성한다.

```text
source_type=url
category=patch_notes
url=https://...
title=사용자 제공 title 또는 fetch 결과 title
```

#### 텍스트 메모 요청

사용자가 본문을 직접 제공하면 `source_type=text_note`로 처리한다.

```text
이 내용을 personal_notes로 저장해줘:
P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다.
```

OpenClaw는 다음 request를 구성한다.

```text
source_type=text_note
category=personal_notes
body=...
title=요약 title
```

#### 파일 경로 요청

사용자가 로컬 파일 경로를 제공하면 확장자에 따라 처리한다.

| 확장자 | source_type |
|---|---|
| `.md` | `markdown_file` |
| `.txt` | `plain_text_file` |
| 기타 | `binary_attachment` 또는 사용자 확인 |

예시:

```text
/mnt/d/ffixiv-bot-storage/incoming/p12s-guide.md 이걸 raid_guides로 넣어줘.
```

OpenClaw는 다음 request를 구성한다.

```text
source_type=markdown_file
category=raid_guides
local_path=/mnt/d/ffixiv-bot-storage/incoming/p12s-guide.md
```

### 8.4 Ambiguity Handling

다음 경우에는 OpenClaw가 바로 실행하지 않고 질문해야 한다.

- category가 불명확한 경우
- URL인지 일반 텍스트인지 애매한 경우
- 파일 경로가 존재하지 않는 경우
- source type을 결정할 수 없는 경우
- 사용자가 “최신 정보 찾아서 넣어줘”처럼 source를 제공하지 않은 경우

단, 사용자가 명확히 category를 제공했으면 추가 질문 없이 실행한다.

---

## 9. Repo Execution Layer

### 9.1 New Entrypoint

v0.5에서 추가할 공식 entrypoint는 다음이다.

```text
tools/process_source.py
```

이 파일은 source 하나를 처리하는 공식 실행 단위다.

### 9.2 CLI Examples

URL 처리:

```bash
python tools/process_source.py \
  --apply \
  --source-type url \
  --category patch_notes \
  --url "https://example.com/ffxiv/patch-note" \
  --title "Patch Note"
```

텍스트 메모 처리:

```bash
python tools/process_source.py \
  --apply \
  --source-type text_note \
  --category personal_notes \
  --title "P12S mitigation note" \
  --body "Use Reprisal before raidwide."
```

markdown file 처리:

```bash
python tools/process_source.py \
  --apply \
  --source-type markdown_file \
  --category raid_guides \
  --title "P12S raid guide" \
  --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"
```

dry-run:

```bash
python tools/process_source.py \
  --dry-run \
  --source-type text_note \
  --category personal_notes \
  --title "Dry run note" \
  --body "This should not be persisted."
```

### 9.3 Required CLI Arguments

공통 인자:

| Argument | Required | 설명 |
|---|---:|---|
| `--apply` 또는 `--dry-run` | yes | 실제 반영 여부 |
| `--source-type` | yes | source type |
| `--category` | yes | storage category |
| `--title` | no | source title |
| `--storage-root` | no | 기본값 `/mnt/d/ffixiv-bot-storage` |
| `--db-path` | no | 기본값 `db/ffxiv.sqlite` |
| `--notion-page-id` | no | Notion row와 연결할 경우 사용 |

source type별 인자:

| Source Type | Required |
|---|---|
| `text_note` | `--body` |
| `markdown_file` | `--local-path` |
| `plain_text_file` | `--local-path` |
| `url` | `--url` |

---

## 10. Pipeline Steps

`process_source.py`는 다음 순서로 실행한다.

```text
1. Parse CLI arguments
2. Validate request
3. Normalize input
4. If source_type=url, fetch URL content
5. Ingest into Local Storage
6. Register source in SQLite DB
7. Rebuild wiki summary
8. Rebuild FTS
9. Build graph
10. Build Notion status update payload
11. Print final JSON result
```

### 10.1 Request Validation

검증 실패 시 아무 파일도 쓰지 않고 `status=error`를 반환한다.

검증 항목:

- source_type이 지원되는 값인지
- category가 지원되는 값인지
- 필수 인자가 존재하는지
- `--apply`와 `--dry-run`이 동시에 지정되지 않았는지
- 파일 입력의 경우 파일이 존재하는지
- URL 입력의 경우 URL 형식이 유효한지

### 10.2 URL Fetch

`source_type=url`인 경우 URL을 fetch한다.

URL fetch의 책임은 다음이다.

- HTTP GET 수행
- status code 확인
- content-type 확인
- HTML/text content 추출
- title 추출 시도
- fetch 결과를 Local Storage ingest 가능한 body로 변환

v0.5에서는 arbitrary crawling을 하지 않는다.  
사용자가 제공한 URL 하나만 fetch한다.

URL fetch 실패 시 ingest를 진행하지 않고 `status=error`를 반환한다.

v0.5-05 구현 기준:

- `tools.fetch_url.fetch_single_url()`이 단일 URL fetch를 담당한다.
- `text/html`은 HTML title과 visible text로 변환한다.
- `text/plain`, `application/json`, `+json`은 text body로 저장한다.
- 지원하지 않는 content-type, HTTP 오류, 빈 body는 fetch error로 처리한다.
- `process_source.py --apply --source-type url`은 fetch 결과 body를 `tools.ingest_local.ingest_source(source_type="url", ...)`로 전달한다.
- URL fetch 성공 후 rebuild는 v05-06 전까지 `skipped`로 남긴다.
- crawler, scheduler, search engine, sitemap, recursive crawling은 v05-05 범위가 아니다.

### 10.3 Local Ingest

Local ingest는 기존 `ingest_local.py`의 로직을 재사용해야 한다.

`process_source.py`가 별도 storage 규칙을 재정의해서는 안 된다.

Local ingest 성공 시 다음 값이 생성되어야 한다.

- `source_id`
- `canonical_path`
- `raw_path`
- `content_hash`
- `category`
- `source_type`

v0.5-04 구현 기준:

- `text_note`, `markdown_file`, `plain_text_file` apply는 `tools.ingest_local.ingest_source()`를 재사용한다.
- 세 local text source type의 canonical path는 `sources/{category}/{title_slug}.md`다.
- `plain_text_file` 입력도 canonical Local Storage path와 raw snapshot은 `.md` 확장자를 사용한다.
- v0.5-04에서는 rebuild를 실행하지 않는다. Local ingest 성공 시 `rebuild` action은 `skipped`/`v05-06_not_implemented`, ingest 실패 시 `skipped`/`upstream_ingest_error`가 된다.

### 10.4 Rebuild

v05-06 implementation note: after any successful `text_note`, `markdown_file`, `plain_text_file`, or `url` ingest, `process_source.py` calls `tools.local_rebuild.rebuild_after_ingest()`. The final JSON records `compile_wiki`, `index_fts`, and `build_graph` actions. A graph success sets `graph_status=built`; graph failure sets `graph_status=failed` and overall `status=partial`.

ingest 성공 후 rebuild를 수행한다.

rebuild는 기존 `local_rebuild.py`, `compile_wiki.py`, `build_graph.py`의 기존 로직을 재사용해야 한다.

rebuild 결과는 다음 상태 중 하나여야 한다.

| 상태 | 의미 |
|---|---|
| `built` | graph build 성공 |
| `pending` | 아직 graph build 전 |
| `failed` | graph build 실패 |
| `skipped` | dry-run 또는 중복 등으로 생략 |

### 10.5 Notion Status Payload

v05-07 implementation note: `process_source.py` builds the payload locally with `tools.status_notification.build_notion_status_update()`, adds `Last Processed`, and appends a `build_notion_payload` action. This does not call Notion.

v0.5에서 `process_source.py`는 Notion API를 직접 호출하지 않아도 된다.

다만 최종 JSON에 `notion_update` payload를 포함해야 한다.

OpenClaw는 이 payload를 읽고 Notion DB를 갱신한다.

Notion payload에는 다음 정보가 포함될 수 있다.

- Status
- Graph Status
- Source ID
- Local Source Path
- Wiki Path
- Last Processed
- Last Error
- Next Action

다음 정보는 Notion payload에 넣지 않는다.

- 원문 body 전체
- 대형 attachment data
- raw binary content
- 민감한 local absolute path 중 노출 불필요한 값

---

## 11. Output Contract

`process_source.py`는 항상 JSON을 stdout으로 출력한다.

성공 예시:

```json
{
  "status": "ok",
  "source_id": "local_abc123",
  "source_type": "text_note",
  "category": "personal_notes",
  "title": "P12S mitigation note",
  "local_source_path": "sources/personal_notes/p12s_mitigation_note.md",
  "raw_path": "raw/local_storage/personal_notes/p12s_mitigation_note__local_abc123.md",
  "wiki_path": "wiki/source_summaries/local_abc123.md",
  "graph_status": "built",
  "actions": [
    {
      "name": "validate_request",
      "status": "ok"
    },
    {
      "name": "ingest_local",
      "status": "ok"
    },
    {
      "name": "rebuild_wiki",
      "status": "ok"
    },
    {
      "name": "rebuild_fts",
      "status": "ok"
    },
    {
      "name": "build_graph",
      "status": "ok"
    },
    {
      "name": "build_notion_update",
      "status": "ok"
    }
  ],
  "notion_update": {
    "Status": "Graph Built",
    "Graph Status": "Built",
    "Source ID": "local_abc123",
    "Wiki Path": "wiki/source_summaries/local_abc123.md"
  },
  "summary": {
    "message": "Source processed successfully.",
    "next_action": "Ready for search and answer."
  }
}
```

부분 실패 예시:

```json
{
  "status": "partial",
  "source_id": "local_abc123",
  "source_type": "text_note",
  "category": "personal_notes",
  "title": "P12S mitigation note",
  "local_source_path": "sources/personal_notes/p12s_mitigation_note.md",
  "raw_path": "raw/local_storage/personal_notes/p12s_mitigation_note__local_abc123.md",
  "wiki_path": "wiki/source_summaries/local_abc123.md",
  "graph_status": "failed",
  "actions": [
    {
      "name": "validate_request",
      "status": "ok"
    },
    {
      "name": "ingest_local",
      "status": "ok"
    },
    {
      "name": "rebuild_wiki",
      "status": "ok"
    },
    {
      "name": "rebuild_fts",
      "status": "ok"
    },
    {
      "name": "build_graph",
      "status": "error",
      "error": "Graph build failed."
    }
  ],
  "notion_update": {
    "Status": "Indexed",
    "Graph Status": "Failed",
    "Source ID": "local_abc123",
    "Last Error": "Graph build failed.",
    "Next Action": "Retry graph build."
  },
  "summary": {
    "message": "Source was ingested and indexed, but graph build failed.",
    "next_action": "Retry graph build."
  }
}
```

검증 실패 예시:

```json
{
  "status": "error",
  "source_id": null,
  "source_type": "url",
  "category": "patch_notes",
  "title": null,
  "graph_status": "skipped",
  "actions": [
    {
      "name": "validate_request",
      "status": "error",
      "error": "Missing required argument: --url"
    }
  ],
  "notion_update": {
    "Status": "Error",
    "Graph Status": "Skipped",
    "Last Error": "Missing required argument: --url",
    "Next Action": "Provide a valid URL."
  },
  "summary": {
    "message": "Request validation failed.",
    "next_action": "Provide a valid URL."
  }
}
```

---

## 12. Status Semantics

Top-level `status`는 다음 중 하나다.

| status | 의미 |
|---|---|
| `ok` | ingest, rebuild, FTS, graph, payload 생성 모두 성공 |
| `partial` | source는 저장됐지만 일부 후속 단계 실패 |
| `error` | source 처리 실패 |
| `skipped` | dry-run, dedupe, 또는 정책상 생략 |

Notion status mapping은 다음을 따른다.

| Internal Result | Notion Status | Graph Status |
|---|---|---|
| `ok` + graph built | `Graph Built` | `Built` |
| `ok` + graph pending | `Indexed` | `Pending` |
| `partial` + graph failed | `Indexed` 또는 `Partial` | `Failed` |
| `error` before ingest | `Error` | `Skipped` |
| `skipped` | `Skipped` | `Skipped` |

---

## 13. Dry Run Semantics

`--dry-run`은 다음을 보장해야 한다.

- Local Storage에 파일을 쓰지 않는다.
- SQLite DB를 변경하지 않는다.
- wiki summary를 생성하지 않는다.
- FTS를 변경하지 않는다.
- graph를 변경하지 않는다.
- Notion API를 호출하지 않는다.
- 단, 어떤 작업이 수행될 예정인지 JSON으로 반환한다.

dry-run 결과 예시:

```json
{
  "status": "skipped",
  "dry_run": true,
  "source_type": "text_note",
  "category": "personal_notes",
  "title": "Dry run note",
  "graph_status": "skipped",
  "actions": [
    {
      "name": "validate_request",
      "status": "ok"
    },
    {
      "name": "ingest_local",
      "status": "skipped",
      "reason": "dry_run"
    },
    {
      "name": "rebuild",
      "status": "skipped",
      "reason": "dry_run"
    }
  ],
  "summary": {
    "message": "Dry run completed. No files or database rows were written."
  }
}
```

---

## 14. Error Handling

v0.5는 실패 위치에 따라 동작을 명확히 나눈다.

### 14.1 Validation Error

검증 단계에서 실패하면 아무 작업도 하지 않는다.

예시:

- source type 누락
- category 누락
- body 누락
- local path 없음
- URL 없음

결과:

```text
status=error
source_id=null
graph_status=skipped
```

### 14.2 Fetch Error

URL fetch 실패 시 ingest하지 않는다.

예시:

- HTTP 404
- timeout
- unsupported content type
- empty response

결과:

```text
status=error
source_id=null
graph_status=skipped
```

### 14.3 Ingest Error

ingest 실패 시 rebuild하지 않는다.

결과:

```text
status=error
source_id=null 또는 partial source_id
graph_status=skipped
```

### 14.4 Rebuild Error

ingest는 성공했지만 rebuild가 실패하면 partial로 처리한다.

결과:

```text
status=partial
source_id=존재
graph_status=failed 또는 pending
```

### 14.5 Notion Payload Error

Notion payload 생성 실패는 source 처리 결과와 분리한다.

source ingest/rebuild가 성공했으면 source 자체는 성공으로 간주하되, payload 생성 실패는 action에 기록한다.

결과:

```text
status=partial
source_id=존재
graph_status=built 또는 pending
```

---

## 15. Dedupe Policy

v0.5는 content hash 또는 URL 기반 중복 감지를 고려해야 한다.

최소 요구사항:

- 같은 content hash가 이미 존재하면 중복으로 판단할 수 있어야 한다.
- 같은 URL이 이미 존재하면 중복으로 판단할 수 있어야 한다.
- 중복 정책은 `skip`, `reuse`, `rebuild` 중 하나로 확장 가능해야 한다.

v0.5 기본 정책은 다음 중 하나로 선택한다.

```text
기본값: skip
```

중복이면 새 source를 만들지 않고 다음을 반환한다.

```text
status=skipped
reason=duplicate
existing_source_id=...
```

단, 기존 repo의 ingest dedupe 정책이 이미 있다면 그 정책을 우선한다.  
`process_source.py`는 기존 dedupe 규칙을 재정의하지 않는다.

---

## 16. URL Policy

v0.5에서 URL 처리의 범위는 다음으로 제한한다.

허용:

- 사용자가 직접 제공한 단일 URL fetch
- HTML 또는 text content fetch
- title 추출
- main text 추출
- Local Storage로 저장
- KB rebuild

금지:

- 검색 엔진 사용
- 링크 재귀 탐색
- sitemap crawling
- 사이트 전체 crawling
- scheduler 기반 자동 fetch
- 비허용 content type 다운로드
- 로그인 필요한 페이지 처리
- Cloudflare 우회
- paywall 우회

URL 처리 실패 시 명확한 error를 반환한다.

---

## 17. Notion Integration Contract

v0.5에서 Notion은 control/status/index layer다.

Notion은 다음을 저장한다.

- source title
- category
- status
- source ID
- local source path
- wiki path
- graph status
- last processed
- last error
- next action

Notion은 다음을 저장하지 않는다.

- 원본 파일 전체
- 대형 본문 전체
- binary attachment
- crawler output dump
- raw HTML 전체

`process_source.py`는 Notion API를 직접 호출하지 않아도 된다.  
대신 `notion_update` payload를 생성한다.

OpenClaw skill은 이 payload를 사용해 Notion DB를 업데이트한다.

---

## 18. Search and Answer After Processing

v0.5 처리 완료 후, 사용자는 다음 명령으로 검색 가능해야 한다.

```bash
python tools/search_kb.py "P12S"
```

또는 답변 context pack을 생성할 수 있어야 한다.

```bash
python tools/answer.py "P12S mitigation" --format text
```

v0.5의 성공 기준은 source가 단순히 저장되는 것이 아니다.  
저장된 source가 wiki/FTS/graph pipeline을 통과해 검색과 답변에 반영되어야 한다.

---

## 19. Required Files

v0.5에서 추가 또는 수정할 파일은 다음이다.

### New Files

```text
docs/specs/0004-v05-source-processing-pipeline.md
docs/plans/v05/2026-05-16-v05-source-processing-pipeline.md
docs/runbooks/process-source.md
tools/process_source.py
tests/test_v05_process_source.py
```

URL helper를 분리할 경우:

```text
tools/fetch_url.py
tests/test_v05_fetch_url.py
```

OpenClaw skill을 repo에 문서화할 경우:

```text
docs/skills/ffxiv-source-processing.md
```

### Updated Files

```text
docs/handoff/CURRENT_HANDOFF.md
docs/WORKFLOW.md
agent.md
CLAUDE.md
```

필요한 경우:

```text
tools/ingest_local.py
tools/local_rebuild.py
tools/status_notification.py
```

단, 기존 함수 재사용이 우선이며, 기존 동작을 깨는 방식으로 수정해서는 안 된다.

---

## 20. Test Plan

### 20.1 Unit Tests

필수 테스트:

```text
test_process_text_note_ok
test_process_markdown_file_ok
test_process_plain_text_file_ok
test_process_url_ok
test_process_dry_run_does_not_write
test_process_missing_body_returns_error
test_process_missing_url_returns_error
test_process_missing_local_path_returns_error
test_process_file_not_found_returns_error
test_process_ingest_error_skips_rebuild
test_process_rebuild_error_returns_partial
test_process_graph_failure_sets_graph_status_failed
test_process_notion_payload_excludes_body
test_process_duplicate_source_returns_skipped_or_reuse
```

### 20.2 Integration Tests

가능하면 다음 integration test를 추가한다.

```text
test_process_text_note_e2e_creates_source_wiki_fts_graph
test_process_url_e2e_creates_source_wiki_fts_graph
```

단, 네트워크 의존 테스트는 mock 또는 fixture를 사용해야 한다.  
외부 실제 URL에 의존하는 테스트는 flaky하므로 기본 테스트에 넣지 않는다.

### 20.3 Regression Tests

기존 v0.4 테스트는 모두 통과해야 한다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

문서 freshness check가 있다면 다음도 실행한다.

```bash
python scripts/check_docs_freshness.py --all
```

작업 종료 스크립트가 있다면 다음도 실행한다.

```bash
python scripts/finish_task.py --skip-notion-dry-run
```

---

## 21. Acceptance Criteria

v0.5는 다음 조건을 모두 만족해야 완료로 본다.

### Functional Acceptance

- `process_source.py`가 존재한다.
- `text_note`를 처리할 수 있다.
- `markdown_file`을 처리할 수 있다.
- `plain_text_file`을 처리할 수 있다.
- `url`을 처리할 수 있다.
- 처리 결과가 Local Storage에 저장된다.
- `sources` DB에 등록된다.
- wiki summary가 생성된다.
- FTS가 갱신된다.
- graph build가 실행된다.
- Notion update payload가 생성된다.
- 최종 결과가 JSON으로 출력된다.

### Safety Acceptance

- dry-run은 파일/DB/graph/wiki를 변경하지 않는다.
- body 전문이 Notion payload에 들어가지 않는다.
- URL fetch는 단일 URL만 처리한다.
- crawler나 scheduler가 들어가지 않는다.
- Google Drive가 기본 path로 복구되지 않는다.
- Notion이 원본 파일 저장소가 되지 않는다.

### Operational Acceptance

- OpenClaw skill 문서가 존재한다.
- 사용자가 URL/file/text를 제공했을 때 OpenClaw가 어떤 명령을 실행해야 하는지 문서화되어 있다.
- 실패 시 사용자가 다음에 무엇을 해야 하는지 `summary.next_action`으로 알 수 있다.
- handoff 문서에 v0.5 사용법과 남은 제한이 기록되어 있다.

---

## 22. OpenClaw Skill Contract

OpenClaw는 source 처리 요청을 받으면 다음 순서를 따른다.

```text
1. 사용자 요청에서 source를 식별한다.
2. source_type을 결정한다.
3. category를 결정한다.
4. title을 정리한다.
5. 필요한 인자를 확인한다.
6. process_source.py를 호출한다.
7. stdout JSON을 파싱한다.
8. notion_update가 있으면 Notion DB를 갱신한다.
9. 사용자에게 status, source_id, graph_status, next_action을 요약한다.
```

OpenClaw는 `process_source.py`가 있는 경우 기존 개별 tool 호출보다 `process_source.py`를 우선 사용한다.

단, `process_source.py`가 실패했을 때 원인을 분석하기 위해 개별 tool을 읽거나 진단할 수 있다.

---

## 23. Example User Flows

### 23.1 URL 저장

사용자:

```text
이 URL을 patch_notes로 저장하고 KB에 반영해줘.
https://example.com/ffxiv/patch-note
```

OpenClaw 실행:

```bash
python tools/process_source.py \
  --apply \
  --source-type url \
  --category patch_notes \
  --url "https://example.com/ffxiv/patch-note"
```

사용자에게 보고:

```text
처리 완료.
source_id: local_abc123
status: ok
graph_status: built
wiki_path: wiki/source_summaries/local_abc123.md
Notion 상태는 Graph Built로 갱신했습니다.
```

### 23.2 텍스트 메모 저장

사용자:

```text
이 내용을 personal_notes로 저장해줘.
P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다.
```

OpenClaw 실행:

```bash
python tools/process_source.py \
  --apply \
  --source-type text_note \
  --category personal_notes \
  --title "P12S Reprisal note" \
  --body "P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다."
```

### 23.3 로컬 파일 저장

사용자:

```text
/mnt/d/ffixiv-bot-storage/incoming/p12s.md 이걸 raid_guides로 넣어줘.
```

OpenClaw 실행:

```bash
python tools/process_source.py \
  --apply \
  --source-type markdown_file \
  --category raid_guides \
  --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"
```

---

## 24. Implementation Tasks

v0.5는 task 단위로 다음처럼 쪼갠다.

### v0.5-01: Spec and Plan

- 이 spec 작성
- v0.5 plan 작성
- scope/non-goals 고정
- 기존 v0.4 문서와 충돌 여부 확인

### v0.5-02: OpenClaw Skill Draft

- `docs/skills/ffxiv-source-processing.md` 작성
- source type 판단 규칙 작성
- category 판단 규칙 작성
- ambiguity handling 작성
- `process_source.py` 우선 호출 규칙 작성

### v0.5-03: process_source.py Skeleton

- CLI argument parsing
- request validation
- output JSON skeleton
- dry-run support
- action log 구조 도입

### v0.5-04: Local Source Integration

- `text_note` 처리
- `markdown_file` 처리
- `plain_text_file` 처리
- 기존 `ingest_local.py` 재사용

### v0.5-05: URL Integration

- URL fetch helper 구현 또는 기존 `ingest_url.py`와 통합
- 단일 URL fetch
- title 추출
- body 추출
- Local Storage ingest로 연결

### v0.5-06: Rebuild Integration

- wiki rebuild
- FTS rebuild
- graph build
- partial failure handling

### v0.5-07: Notion Payload Integration

- 기존 `status_notification.py` 재사용
- payload contract 고정
- body/attachment exclusion 보장

### v0.5-08: Tests and Runbook

- unit tests 작성
- integration tests 작성
- `docs/runbooks/process-source.md` 작성
- `docs/handoff/CURRENT_HANDOFF.md` 갱신

---

## 25. Verification Commands

작업 완료 전 다음 명령을 실행한다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

가능하면 다음도 실행한다.

```bash
python scripts/check_docs_freshness.py --all
```

```bash
python scripts/finish_task.py --skip-notion-dry-run
```

수동 smoke test:

```bash
python tools/process_source.py \
  --dry-run \
  --source-type text_note \
  --category personal_notes \
  --title "Smoke test" \
  --body "This is a dry-run smoke test."
```

실제 apply smoke test:

```bash
python tools/process_source.py \
  --apply \
  --source-type text_note \
  --category personal_notes \
  --title "Smoke test apply" \
  --body "This is an apply smoke test."
```

검색 확인:

```bash
python tools/search_kb.py "Smoke test"
```

답변 확인:

```bash
python tools/answer.py "Smoke test" --format text
```

---

## 26. Completion Report Format

OpenClaw는 v0.5 작업 완료 후 다음 형식으로만 보고한다.

```text
1. 추가/수정한 파일

2. 새 CLI 사용 예시

3. 통과한 테스트

4. 남은 제한 사항
```

보고에서 장황한 설명은 생략한다.  
실패한 테스트가 있으면 실패 내용을 숨기지 말고 그대로 보고한다.

---

## 27. Future Work

v0.5 완료 후 v0.6에서 다음을 진행한다.

- Notion queue schema 고정
- `Status = New` 항목을 process_source request로 변환
- `process_notion_queue.py` 구현
- allowlist 기반 `source_registry.yml` 도입
- `discover_sources.py` 구현
- scheduler/cron runbook 작성
- e2e automation dry-run 테스트

v0.6의 목표는 다음이다.

```text
처리할 source를 사용자가 직접 주는 단계에서,
Notion과 allowlist crawler가 source job을 생성하는 단계로 확장한다.
```

---

## 28. Summary

v0.5는 FFXIV bot의 “자동화 기반”이다.

핵심은 다음이다.

```text
OpenClaw Skill
= 사용자 요청을 해석하고 처리 인자를 구성한다.

process_source.py
= source 하나를 ingest → rebuild → status payload까지 처리한다.
```

v0.5가 완료되면 OpenClaw는 다음 수준의 요청을 안정적으로 처리할 수 있다.

```text
이 URL을 KB에 넣어줘.
이 파일을 raid guide로 저장해줘.
이 메모를 검색 가능하게 만들어줘.
```

하지만 v0.5는 아직 다음을 하지 않는다.

```text
최신 FFXIV 정보를 알아서 찾아오기
Notion New 항목 자동 감시
스케줄러 기반 주기 업데이트
allowlist crawler
```

그 범위는 v0.6 Automation Loop에서 다룬다.
