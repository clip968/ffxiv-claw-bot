# SPEC 0007 - v0.7 Grounded Ask Pipeline - ffxiv-claw-bot

Status: Active
Target version: v0.7
Project: ffxiv-claw-bot
Scope: Crawling / polling / Discord notification excluded

---

## 1. Purpose

v0.7의 목적은 v0.6까지 구축한 지식 베이스 산출물을 실제 질문 응답에 사용할 수 있는 ask pipeline으로 연결하는 것이다.

v0.6까지 완료된 것은 자료 처리 파이프라인이다.

```text
source ingest
→ wiki/source_summaries/*.md 생성
→ wiki/jobs/*.md derived wiki 생성
→ wiki_fts 인덱싱
→ graph 생성
```

v0.7은 사용자의 질문을 받아 다음 흐름을 수행한다.

```text
사용자 질문
→ query parser
→ job / patch / intent 감지
→ retrieval planner
→ wiki/jobs 우선 검색
→ source_summaries fallback 검색
→ context pack 생성
→ grounded answer composer
→ text/json 답변 출력
```

v0.7은 공식 패치노트 watcher, crawling, polling, Discord notification, Discord slash command를 포함하지 않는다.

---

## 2. Current State

v0.6까지 완료된 기능:

- `.txt`, `.md`, `.html`, `.csv`, `.xlsx` source 처리
- `tools/process_source.py` 단일 source 처리
- `tools/process_pending_sources.py` pending queue 처리
- `wiki/source_summaries/*.md` 생성
- `wiki/jobs/*.md` derived wiki 생성
- derived wiki 생성 후 FTS 자동 반영
- graph 생성
- source 처리 결과 JSON 및 Notion payload 생성

현재 부족한 점:

- 사용자 질문에서 job, patch, intent를 구조적으로 파싱하지 못함
- `wiki/jobs/<job>.md`를 우선 검색하는 정책이 없음
- source summary fallback 검색 정책이 없음
- 답변이 source_id/path 기반으로 충분히 구조화되어 있지 않음
- `search_kb.py`와 `answer.py`가 아직 ask pipeline 전체를 대표하지 못함

---

## 3. Scope

### Included

- Query parser
- Job detector
- Patch range parser
- Intent detector
- Retrieval planner
- Filtered FTS search
- Job wiki 우선 검색
- Source summaries fallback 검색
- Context pack builder
- Grounded answer composer
- `tools/ask.py` CLI
- JSON/text output contract
- Debug output
- Regression tests
- Runbook documentation

### Excluded

- Official patchnote watcher
- Crawling
- Polling
- Webhook receiver
- Discord notification
- Discord slash command
- Scheduler / cron integration
- LLM API 기반 자연어 생성
- Vector DB / embedding search
- `wiki/raids`, `wiki/items`, `wiki/systems` derived wiki generation

---

## 4. Target User Flow

Example command:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format text
```

Expected internal result:

```json
{
  "parsed_query": {
    "intent": "job_change_history",
    "job": "gunbreaker",
    "patch_range": "7.0..7.99",
    "topic": "job"
  },
  "retrieval_plan": {
    "primary": {
      "wiki_type": "job",
      "topic": "gunbreaker"
    },
    "fallback": {
      "wiki_type": "source_summary"
    }
  }
}
```

Expected answer shape:

```text
현재 KB 기준 Gunbreaker 관련 변경 사항은 다음과 같습니다.

7.0
- Continuation potency adjusted.
  근거: source_id: patch_7_0

7.1
- No Mercy window clarified.
  근거: source_id: patch_7_1

근거 문서:
- wiki/jobs/gunbreaker.md

확실도:
- source_grounded
```

---

## 5. Architecture

Recommended structure:

```text
tools/
  ask.py
  answer.py
  search_kb.py

src/
  query/
    __init__.py
    models.py
    normalize.py
    job_detector.py
    patch_parser.py
    intent_detector.py
    parser.py

  retrieval/
    __init__.py
    models.py
    fts_search.py
    planner.py
    context_builder.py
    ranking.py

  answering/
    __init__.py
    composer.py
    citations.py
    confidence.py
```

`tools/ask.py` should become the official v0.7 entrypoint.

---

## 6. Query Parser

### 6.1 ParsedQuery Model

File:

```text
src/query/models.py
```

Suggested model:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ParsedQuery:
    raw_query: str
    normalized_query: str
    intent: str | None
    job: str | None
    patch_range: str | None
    topic: str | None
    terms: tuple[str, ...]
```

Example:

```text
Input:
7.x 건브레이커 변경 이력 알려줘

ParsedQuery:
raw_query = "7.x 건브레이커 변경 이력 알려줘"
normalized_query = "7.x 건브레이커 변경 이력 알려줘"
intent = "job_change_history"
job = "gunbreaker"
patch_range = "7.0..7.99"
topic = "job"
terms = ("건브레이커", "변경", "이력")
```

---

## 7. Job Detector

Reuse the v0.6 job catalog:

```text
src/derived_wiki/job_catalog.py
```

The detector should resolve English names, abbreviations, and Korean aliases.

Examples:

```text
건브레이커 -> gunbreaker
건브 -> gunbreaker
GNB -> gunbreaker
Gunbreaker -> gunbreaker

흑마 -> black_mage
흑마도사 -> black_mage
BLM -> black_mage
Black Mage -> black_mage

픽토 -> pictomancer
픽토맨서 -> pictomancer
PCT -> pictomancer
```

Suggested file:

```text
src/query/job_detector.py
```

Required behavior:

- Exact alias matching
- Case-insensitive English matching
- Korean alias matching
- Return `None` when no job is found
- Avoid false positives inside unrelated words

---

## 8. Patch Range Parser

Suggested file:

```text
src/query/patch_parser.py
```

v0.7 should support numeric patch expressions only.

Required examples:

```text
7.2 -> 7.2..7.2
7.x -> 7.0..7.99
7.0~7.5 -> 7.0..7.5
7.0-7.5 -> 7.0..7.5
7.0부터 7.5까지 -> 7.0..7.5
```

Out of scope for v0.7:

```text
효월
칠흑
창천
홍련
황금
Dawntrail
Endwalker
```

Expansion name mapping should be deferred.

---

## 9. Intent Detector

Suggested file:

```text
src/query/intent_detector.py
```

Initial implementation should be rule-based.

Required intents:

```text
job_change_history
generic_search
```

Optional v0.7 intent:

```text
patch_summary
```

Rules:

```text
job + "변경 이력" -> job_change_history
job + "변경점" -> job_change_history
job + "뭐 바뀜" -> job_change_history
job + "패치" + "변경" -> job_change_history
otherwise -> generic_search
```

Examples:

```text
"7.x 건브레이커 변경 이력 알려줘"
-> job_change_history

"흑마 7.2에서 뭐 바뀜?"
-> job_change_history

"M4S 공략 찾아줘"
-> generic_search
```

---

## 10. Retrieval Planner

Suggested file:

```text
src/retrieval/planner.py
```

### 10.1 RetrievalPlan Model

Suggested model:

```python
@dataclass(frozen=True)
class RetrievalPlan:
    primary: tuple[RetrievalTarget, ...]
    fallback: tuple[RetrievalTarget, ...]
    limit: int
```

Suggested target model:

```python
@dataclass(frozen=True)
class RetrievalTarget:
    wiki_type: str | None
    topic: str | None
    query: str
    priority: int
```

### 10.2 Job Change History Plan

If:

```text
intent = job_change_history
job = gunbreaker
```

Plan:

```text
Primary:
- wiki_type=job
- topic=gunbreaker
- query="gunbreaker Gunbreaker 건브레이커 GNB"

Fallback:
- wiki_type=source_summary
- query="gunbreaker Gunbreaker 건브레이커 GNB"
```

Search order:

```text
1. wiki/jobs/<job>.md
2. wiki/source_summaries/*.md
3. generic FTS
```

---

## 11. Filtered FTS Search

Suggested file:

```text
src/retrieval/fts_search.py
```

Add a search function that can filter by wiki type and topic.

Suggested signature:

```python
def search_wiki(
    query: str,
    *,
    wiki_type: str | None = None,
    topic: str | None = None,
    limit: int = 5,
    db_path: Path | None = None,
) -> list[SearchResult]:
    ...
```

Expected behavior:

- `wiki_type="job"` should return job wiki pages first
- `topic="gunbreaker"` should narrow to `job_gunbreaker` or `wiki_pages.job = gunbreaker`
- Existing `tools/search_kb.py` should remain compatible
- FTS query should still sanitize unsafe FTS5 syntax

---

## 12. Context Pack Builder

Suggested file:

```text
src/retrieval/context_builder.py
```

### 12.1 AskContextPack Model

```python
@dataclass(frozen=True)
class AskContextPack:
    question: str
    parsed_query: ParsedQuery
    retrieval_plan: RetrievalPlan
    contexts: tuple[ContextDocument, ...]
    confidence: str
```

### 12.2 ContextDocument Model

```python
@dataclass(frozen=True)
class ContextDocument:
    page_id: str
    wiki_type: str
    title: str
    path: str
    score: float | None
    snippet: str
    content_excerpt: str
    source_ids: tuple[str, ...]
```

Required behavior:

- Read document content from `wiki_pages.path`
- Limit excerpt length
- Preserve source_id lines from job wiki
- Include wiki path in context
- Return empty contexts when no relevant document is found

---

## 13. Grounded Answer Composer

Suggested file:

```text
src/answering/composer.py
```

v0.7 should use deterministic composition, not LLM generation.

Rules:

- Do not invent facts not present in context
- Include source_id or wiki path
- If no context exists, say no relevant KB document was found
- Prefer job wiki content when available
- Include confidence

Output sections:

```text
핵심 답변
근거 문서
확실도
주의
```

No-context output:

```text
현재 KB에서 해당 질문과 관련된 문서를 찾지 못했습니다.
context에 없는 내용은 추정하지 않았습니다.

확실도:
N/A
```

---

## 14. `tools/ask.py` CLI

Official v0.7 entrypoint:

```text
tools/ask.py
```

Required commands:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘"

python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format text

python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json

python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --debug

python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --limit 5
```

Required options:

```text
--format json|text
--debug
--limit
--db-path
--root-path
```

### 14.1 JSON Output Contract

Required JSON shape:

```json
{
  "status": "ok",
  "question": "7.x 건브레이커 변경 이력 알려줘",
  "parsed_query": {
    "intent": "job_change_history",
    "job": "gunbreaker",
    "patch_range": "7.0..7.99",
    "topic": "job"
  },
  "retrieval_plan": {
    "primary": [],
    "fallback": []
  },
  "contexts": [],
  "answer": {
    "format": "text",
    "body": "...",
    "confidence": "source_grounded",
    "sources": []
  },
  "actions": []
}
```

Failure shape:

```json
{
  "status": "error",
  "question": "...",
  "error_stage": "parse|retrieval|compose",
  "error_message": "...",
  "actions": []
}
```

---

## 15. Acceptance Criteria

v0.7 is complete when:

1. `tools/ask.py "7.x 건브레이커 변경 이력"` detects `job=gunbreaker`.
2. `tools/ask.py "7.x 건브레이커 변경 이력"` detects `patch_range=7.0..7.99`.
3. Job change history queries prefer `wiki/jobs/<job>.md`.
4. If the job wiki is missing, source summary fallback search runs.
5. The answer includes wiki path or source_id.
6. No-context questions return a no-context answer instead of hallucinating.
7. `--format json` has a stable schema.
8. `--format text` produces readable grounded output.
9. `--debug` exposes parsed query and retrieval plan.
10. Existing `search_kb.py` and `answer.py` behavior is not broken.
11. Existing v06 tests continue to pass.

---

## 16. Test Plan

### 16.1 Query Parser Tests

```text
test_parse_job_korean_alias
test_parse_job_abbreviation
test_parse_job_english_name
test_parse_no_job_returns_none
test_parse_patch_single
test_parse_patch_x_range
test_parse_patch_tilde_range
test_parse_patch_korean_range
test_detect_job_change_history_intent
test_generic_search_when_no_specific_intent
```

### 16.2 Retrieval Tests

```text
test_retrieval_prefers_job_wiki
test_retrieval_fallback_to_source_summary_when_job_wiki_missing
test_retrieval_filters_by_wiki_type
test_retrieval_filters_by_topic
test_retrieval_sanitizes_fts_query
```

### 16.3 Context Pack Tests

```text
test_context_pack_includes_job_wiki_path
test_context_pack_includes_source_ids
test_context_pack_limits_excerpt_length
test_context_pack_empty_when_no_results
```

### 16.4 Answer Composer Tests

```text
test_answer_includes_source_path
test_answer_includes_source_id
test_answer_no_context_no_hallucination
test_answer_uses_source_grounded_confidence
test_answer_text_format
```

### 16.5 CLI Tests

```text
test_ask_cli_json_contract
test_ask_cli_text_output
test_ask_cli_debug_output
test_ask_cli_no_context
test_ask_cli_job_change_history_e2e
```

---

## 17. Task Breakdown

### v07-01. Query model and normalization

Files:

```text
src/query/models.py
src/query/normalize.py
src/query/__init__.py
```

Tasks:

- Add `ParsedQuery`
- Add normalization helpers
- Add tests

Acceptance:

- Query model can preserve raw and normalized query
- Terms are extracted deterministically

---

### v07-02. Job detector

Files:

```text
src/query/job_detector.py
```

Tasks:

- Reuse v06 job catalog
- Match Korean/English/abbreviation aliases
- Return job slug

Acceptance:

- `건브`, `건브레이커`, `GNB`, `Gunbreaker` all resolve to `gunbreaker`

---

### v07-03. Patch range parser

Files:

```text
src/query/patch_parser.py
```

Tasks:

- Parse single patch
- Parse x-range
- Parse explicit range

Acceptance:

- `7.x` returns `7.0..7.99`
- `7.0~7.5` returns `7.0..7.5`

---

### v07-04. Intent detector

Files:

```text
src/query/intent_detector.py
```

Tasks:

- Add `job_change_history`
- Add `generic_search`
- Add optional `patch_summary`

Acceptance:

- `건브레이커 변경 이력` returns `job_change_history`

---

### v07-05. Query parser integration

Files:

```text
src/query/parser.py
```

Tasks:

- Combine job detector, patch parser, intent detector
- Return `ParsedQuery`

Acceptance:

- `7.x 건브레이커 변경 이력` returns job, patch range, intent

---

### v07-06. Retrieval models and planner

Files:

```text
src/retrieval/models.py
src/retrieval/planner.py
```

Tasks:

- Add `RetrievalTarget`
- Add `RetrievalPlan`
- Add job wiki first policy

Acceptance:

- Job change history query creates primary job wiki target

---

### v07-07. Filtered FTS search

Files:

```text
src/retrieval/fts_search.py
```

Tasks:

- Add wiki_type filter
- Add topic/job filter
- Keep existing FTS sanitization behavior

Acceptance:

- `wiki_type=job`, `topic=gunbreaker` returns `job_gunbreaker`

---

### v07-08. Context builder

Files:

```text
src/retrieval/context_builder.py
```

Tasks:

- Build context pack
- Read wiki file excerpt
- Extract source_id references

Acceptance:

- Context includes path, source_ids, excerpt

---

### v07-09. Answer composer

Files:

```text
src/answering/composer.py
src/answering/citations.py
src/answering/confidence.py
```

Tasks:

- Compose deterministic answer
- Include source path/source_id
- No-context response

Acceptance:

- Answer does not invent facts outside context

---

### v07-10. `tools/ask.py`

Files:

```text
tools/ask.py
```

Tasks:

- CLI parser
- JSON/text format
- Debug mode
- Error contract

Acceptance:

- `python tools/ask.py "7.x 건브레이커 변경 이력" --format json` returns stable schema

---

### v07-11. Tests

Files:

```text
tests/test_v07_query_parser.py
tests/test_v07_retrieval.py
tests/test_v07_context_builder.py
tests/test_v07_answer_composer.py
tests/test_v07_ask_cli.py
```

Tasks:

- Add red tests first
- Implement features
- Preserve existing v06 tests

Acceptance:

- v07 tests pass
- Full test suite passes

---

### v07-12. Documentation

Files:

```text
docs/specs/0007-v07-grounded-ask-pipeline.md
docs/plans/v07/README.md
docs/runbooks/ask.md
docs/handoff/CURRENT_HANDOFF.md
```

Tasks:

- Document ask pipeline
- Document CLI examples
- Document known limitations

Acceptance:

- Next session can continue from docs alone

---

## 18. Implementation Notes

- Do not add crawling in v0.7.
- Do not add Discord command in v0.7.
- Do not add LLM-based answer generation in v0.7.
- Prefer deterministic behavior.
- Keep `answer.py` and `search_kb.py` backward compatible.
- `ask.py` can reuse existing functions, but should become the stable user-facing ask entrypoint.
- Retrieval should prefer derived wiki when possible.
- Fallback should preserve source grounding.

---

## 19. Expected Result After v0.7

After v0.7, the system should support:

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘"
```

Expected behavior:

```text
1. Query parser detects job=gunbreaker.
2. Patch parser detects patch_range=7.0..7.99.
3. Retrieval planner searches wiki/jobs/gunbreaker.md first.
4. If job wiki exists, it is used as primary context.
5. If job wiki is missing, source_summaries fallback search runs.
6. Answer includes source_id/path.
7. If no context exists, answer says no relevant KB document was found.
```

This is the first version where the project behaves like a usable FFXIV question-answering bot backend, even before Discord integration.

---

## 20. Future Work

Recommended next phases:

```text
v08:
Discord Adapter
- /ask
- /ingest
- /status

v09:
Official Patchnote Watcher
- polling
- queue registration
- optional Discord notification

v10:
More Derived Wiki
- raids
- items
- systems

v11:
LLM Answer Composer
- LLM-based fluent answer generation
- context-only policy enforcement
```

---

## 21. Summary

v0.7 should focus only on the ask pipeline.

```text
v07 = Grounded Ask Pipeline
```

It should convert the existing v0.6 knowledge base into a usable query-answering backend.

```text
user question
→ parsed query
→ retrieval plan
→ job wiki first
→ source summary fallback
→ grounded answer
```
