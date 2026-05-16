# v07 Implementation Plan - Grounded Ask Pipeline - ffxiv-claw-bot

Status: Draft
Based on: `SPEC 0007 - v0.7 Grounded Ask Pipeline`
Scope: Crawling / polling / Discord notification excluded
Target entrypoint: `tools/ask.py`

---

## 0. Goal

v07의 목표는 v06까지 구축된 지식 베이스를 실제 질문 응답에 사용할 수 있는 ask pipeline으로 연결하는 것이다.

v06까지 완료된 파이프라인:

```text
source ingest
→ wiki/source_summaries/*.md 생성
→ wiki/jobs/*.md 생성
→ wiki_fts 인덱싱
→ graph 생성
```

v07에서 구현할 파이프라인:

```text
user question
→ query parser
→ job / patch / intent detection
→ retrieval planner
→ filtered FTS search
→ job wiki first
→ source summary fallback
→ context pack
→ grounded answer
→ tools/ask.py output
```

v07은 다음을 포함하지 않는다.

```text
official patchnote watcher
crawling
polling
Discord notification
Discord slash command
LLM API answer generation
vector DB
embedding search
```

---

## 1. Implementation Strategy

v07은 한 번에 구현하지 말고 다음 batch로 나눈다.

```text
Batch A: Query parsing foundation
Batch B: Retrieval planning and filtered FTS
Batch C: Context pack and grounded answer
Batch D: tools/ask.py CLI
Batch E: E2E tests and docs
```

각 batch는 red test를 먼저 작성한 뒤 구현한다.

---

## 2. Target File Layout

Expected new files:

```text
src/query/__init__.py
src/query/models.py
src/query/normalize.py
src/query/job_detector.py
src/query/patch_parser.py
src/query/intent_detector.py
src/query/parser.py

src/retrieval/__init__.py
src/retrieval/models.py
src/retrieval/fts_search.py
src/retrieval/planner.py
src/retrieval/context_builder.py
src/retrieval/ranking.py

src/answering/__init__.py
src/answering/composer.py
src/answering/citations.py
src/answering/confidence.py

tools/ask.py

tests/test_v07_query_parser.py
tests/test_v07_retrieval.py
tests/test_v07_context_builder.py
tests/test_v07_answer_composer.py
tests/test_v07_ask_cli.py

docs/specs/0007-v07-grounded-ask-pipeline.md
docs/plans/v07/README.md
docs/runbooks/ask.md
```

Files to preserve compatibility with:

```text
tools/search_kb.py
tools/answer.py
tools/compile_wiki.py
src/derived_wiki/job_catalog.py
```

---

# Batch A - Query Parsing Foundation

---

## v07-01. Query model and normalization

### Goal

Add a stable `ParsedQuery` model and basic normalization helpers.

### Files

Create:

```text
src/query/__init__.py
src/query/models.py
src/query/normalize.py
tests/test_v07_query_parser.py
```

### Red tests

Add tests first:

```python
def test_parsed_query_preserves_raw_and_normalized_query():
    ...

def test_normalize_query_casefolds_english_but_preserves_korean():
    ...

def test_tokenize_query_extracts_terms():
    ...
```

Expected initial failure:

```text
ModuleNotFoundError: No module named 'src.query'
```

### Implementation

`src/query/models.py`:

```python
from __future__ import annotations

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

`src/query/normalize.py`:

```python
from __future__ import annotations

import re


def normalize_query(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def extract_terms(value: str) -> tuple[str, ...]:
    normalized = normalize_query(value)
    terms = re.findall(r"[a-z0-9_.]+|[가-힣]+", normalized)
    return tuple(term for term in terms if term)
```

### Acceptance Criteria

- `ParsedQuery` is importable from `src.query`.
- Normalization is deterministic.
- Korean text is preserved.
- English text is casefolded.
- Empty/whitespace input does not crash.

### Agent Prompt

```text
Implement v07-01 only.

Add the query package foundation for v07 Grounded Ask Pipeline.

Files:
- src/query/__init__.py
- src/query/models.py
- src/query/normalize.py
- tests/test_v07_query_parser.py

Rules:
- Write red tests first.
- Add ParsedQuery as a frozen dataclass.
- Add normalize_query() and extract_terms().
- Do not implement job detection yet.
- Do not modify search_kb.py or answer.py.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/models.py src/query/normalize.py src/query/__init__.py
```

---

## v07-02. Job detector

### Goal

Detect FFXIV job names from user questions using the v06 job catalog.

### Files

Create/update:

```text
src/query/job_detector.py
src/query/__init__.py
tests/test_v07_query_parser.py
```

Reuse:

```text
src/derived_wiki/job_catalog.py
```

### Red tests

Add tests:

```python
def test_detect_job_korean_full_alias():
    assert detect_job("건브레이커 변경 이력") == "gunbreaker"

def test_detect_job_korean_short_alias():
    assert detect_job("건브 뭐 바뀜?") == "gunbreaker"

def test_detect_job_abbreviation_alias():
    assert detect_job("GNB patch history") == "gunbreaker"

def test_detect_job_english_name():
    assert detect_job("Black Mage changes") == "black_mage"

def test_detect_no_job_returns_none():
    assert detect_job("패치노트 요약") is None
```

### Implementation

`src/query/job_detector.py`:

```python
from __future__ import annotations

import re

from src.derived_wiki.job_catalog import JOB_CATALOG


def detect_job(query: str) -> str | None:
    normalized = _normalize(query)

    candidates: list[tuple[int, str]] = []
    for job in JOB_CATALOG:
        aliases = {job.slug, job.display_name, *job.aliases}
        for alias in aliases:
            alias_norm = _normalize(alias)
            if not alias_norm:
                continue
            if _matches_alias(normalized, alias_norm):
                candidates.append((len(alias_norm), job.slug))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _normalize(value: str) -> str:
    return " ".join(value.strip().casefold().replace("_", " ").split())


def _matches_alias(text: str, alias: str) -> bool:
    if _is_ascii(alias):
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return alias in text


def _is_ascii(value: str) -> bool:
    return all(ord(char) < 128 for char in value)
```

### Acceptance Criteria

- Korean aliases resolve correctly.
- Abbreviation aliases resolve correctly.
- English names resolve correctly.
- No job returns `None`.
- Shorter alias does not override longer alias incorrectly.

### Agent Prompt

```text
Implement v07-02 only.

Add job detection for the v07 ask pipeline.

Files:
- src/query/job_detector.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- Reuse src.derived_wiki.job_catalog.
- Do not duplicate the job catalog.
- Match Korean aliases, English names, and abbreviations.
- Use safe boundary matching for ASCII aliases.
- Return job slug or None.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/job_detector.py
```

---

## v07-03. Patch range parser

### Goal

Parse numeric patch expressions from user questions.

### Files

Create/update:

```text
src/query/patch_parser.py
src/query/__init__.py
tests/test_v07_query_parser.py
```

### Red tests

Add tests:

```python
def test_parse_single_patch():
    assert parse_patch_range("7.2 패치") == "7.2..7.2"

def test_parse_x_patch_range():
    assert parse_patch_range("7.x 변경점") == "7.0..7.99"

def test_parse_tilde_patch_range():
    assert parse_patch_range("7.0~7.5 변경 이력") == "7.0..7.5"

def test_parse_dash_patch_range():
    assert parse_patch_range("7.0-7.5 변경 이력") == "7.0..7.5"

def test_parse_korean_range():
    assert parse_patch_range("7.0부터 7.5까지") == "7.0..7.5"

def test_parse_no_patch_returns_none():
    assert parse_patch_range("건브레이커 변경 이력") is None
```

### Implementation

`src/query/patch_parser.py`:

```python
from __future__ import annotations

import re


PATCH = r"(\d+)\.(\d+)"
PATCH_X = r"(\d+)\.x"


def parse_patch_range(query: str) -> str | None:
    text = query.casefold()

    korean_range = re.search(rf"{PATCH}\s*부터\s*{PATCH}\s*까지", text)
    if korean_range:
        return _range_from_match_groups(korean_range.groups())

    explicit_range = re.search(rf"{PATCH}\s*[~\-–]\s*{PATCH}", text)
    if explicit_range:
        return _range_from_match_groups(explicit_range.groups())

    x_range = re.search(PATCH_X, text)
    if x_range:
        major = int(x_range.group(1))
        return f"{major}.0..{major}.99"

    single = re.search(PATCH, text)
    if single:
        major = int(single.group(1))
        minor = int(single.group(2))
        return f"{major}.{minor}..{major}.{minor}"

    return None


def _range_from_match_groups(groups: tuple[str, ...]) -> str:
    start_major, start_minor, end_major, end_minor = (int(part) for part in groups)
    return f"{start_major}.{start_minor}..{end_major}.{end_minor}"
```

### Acceptance Criteria

- Numeric patch ranges parse correctly.
- `7.x` maps to `7.0..7.99`.
- No patch returns `None`.
- Expansion names are not handled in v07.

### Agent Prompt

```text
Implement v07-03 only.

Add numeric patch range parsing for v07.

Files:
- src/query/patch_parser.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- Support 7.2, 7.x, 7.0~7.5, 7.0-7.5, 7.0부터 7.5까지.
- Do not implement expansion name mapping.
- Return normalized string like 7.0..7.5 or None.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/patch_parser.py
```

---

## v07-04. Intent detector

### Goal

Classify user questions into simple deterministic intents.

### Files

Create/update:

```text
src/query/intent_detector.py
src/query/__init__.py
tests/test_v07_query_parser.py
```

### Red tests

Add tests:

```python
def test_detect_job_change_history_intent_with_change_history():
    assert detect_intent("건브레이커 변경 이력", job="gunbreaker") == "job_change_history"

def test_detect_job_change_history_intent_with_what_changed():
    assert detect_intent("흑마 뭐 바뀜?", job="black_mage") == "job_change_history"

def test_detect_generic_search_without_job():
    assert detect_intent("M4S 공략 찾아줘", job=None) == "generic_search"
```

### Implementation

`src/query/intent_detector.py`:

```python
from __future__ import annotations


JOB_CHANGE_KEYWORDS = (
    "변경 이력",
    "변경점",
    "뭐 바뀜",
    "바뀐",
    "패치 변경",
    "change history",
    "changes",
)


def detect_intent(query: str, *, job: str | None = None) -> str:
    normalized = " ".join(query.strip().casefold().split())
    if job and any(keyword in normalized for keyword in JOB_CHANGE_KEYWORDS):
        return "job_change_history"
    return "generic_search"
```

### Acceptance Criteria

- Job + change-related phrase returns `job_change_history`.
- Without job, generic search is used.
- No LLM dependency.

### Agent Prompt

```text
Implement v07-04 only.

Add deterministic intent detection for the v07 ask pipeline.

Files:
- src/query/intent_detector.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- Required intents: job_change_history and generic_search.
- Use simple rule-based detection.
- Do not call any LLM.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/intent_detector.py
```

---

## v07-05. Query parser integration

### Goal

Combine normalization, job detection, patch range parsing, and intent detection into one parser.

### Files

Create/update:

```text
src/query/parser.py
src/query/__init__.py
tests/test_v07_query_parser.py
```

### Red tests

Add tests:

```python
def test_parse_query_job_change_history():
    parsed = parse_query("7.x 건브레이커 변경 이력 알려줘")
    assert parsed.intent == "job_change_history"
    assert parsed.job == "gunbreaker"
    assert parsed.patch_range == "7.0..7.99"
    assert parsed.topic == "job"

def test_parse_query_generic_search():
    parsed = parse_query("M4S 공략 찾아줘")
    assert parsed.intent == "generic_search"
    assert parsed.job is None
```

### Implementation

`src/query/parser.py`:

```python
from __future__ import annotations

from src.query.intent_detector import detect_intent
from src.query.job_detector import detect_job
from src.query.models import ParsedQuery
from src.query.normalize import extract_terms, normalize_query
from src.query.patch_parser import parse_patch_range


def parse_query(query: str) -> ParsedQuery:
    normalized = normalize_query(query)
    job = detect_job(query)
    patch_range = parse_patch_range(query)
    intent = detect_intent(query, job=job)
    topic = "job" if job else None

    return ParsedQuery(
        raw_query=query,
        normalized_query=normalized,
        intent=intent,
        job=job,
        patch_range=patch_range,
        topic=topic,
        terms=extract_terms(query),
    )
```

### Acceptance Criteria

- Single function returns complete `ParsedQuery`.
- Works for job change history.
- Works for generic search.
- Existing parser components remain separately testable.

### Agent Prompt

```text
Implement v07-05 only.

Integrate the query parser.

Files:
- src/query/parser.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- parse_query() must return ParsedQuery.
- Reuse normalize_query, extract_terms, detect_job, parse_patch_range, detect_intent.
- Do not implement retrieval yet.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/parser.py
```

---

# Batch B - Retrieval Planning and Filtered FTS

---

## v07-06. Retrieval models and planner

### Goal

Build a retrieval plan from `ParsedQuery`.

### Files

Create:

```text
src/retrieval/__init__.py
src/retrieval/models.py
src/retrieval/planner.py
tests/test_v07_retrieval.py
```

### Red tests

Add tests:

```python
def test_job_change_history_plan_prefers_job_wiki():
    parsed = ParsedQuery(... job="gunbreaker", intent="job_change_history")
    plan = build_retrieval_plan(parsed)
    assert plan.primary[0].wiki_type == "job"
    assert plan.primary[0].topic == "gunbreaker"

def test_generic_search_plan_has_no_topic_filter():
    ...
```

### Implementation

`src/retrieval/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalTarget:
    wiki_type: str | None
    topic: str | None
    query: str
    priority: int


@dataclass(frozen=True)
class RetrievalPlan:
    primary: tuple[RetrievalTarget, ...]
    fallback: tuple[RetrievalTarget, ...]
    limit: int
```

`src/retrieval/planner.py`:

```python
from __future__ import annotations

from src.derived_wiki.job_catalog import resolve_job
from src.query.models import ParsedQuery
from src.retrieval.models import RetrievalPlan, RetrievalTarget


def build_retrieval_plan(parsed: ParsedQuery, *, limit: int = 5) -> RetrievalPlan:
    if parsed.intent == "job_change_history" and parsed.job:
        query = _job_query(parsed.job)
        return RetrievalPlan(
            primary=(
                RetrievalTarget(
                    wiki_type="job",
                    topic=parsed.job,
                    query=query,
                    priority=1,
                ),
            ),
            fallback=(
                RetrievalTarget(
                    wiki_type="source_summary",
                    topic=None,
                    query=query,
                    priority=2,
                ),
                RetrievalTarget(
                    wiki_type=None,
                    topic=None,
                    query=parsed.raw_query,
                    priority=3,
                ),
            ),
            limit=limit,
        )

    return RetrievalPlan(
        primary=(
            RetrievalTarget(
                wiki_type=None,
                topic=None,
                query=parsed.raw_query,
                priority=1,
            ),
        ),
        fallback=(),
        limit=limit,
    )


def _job_query(job_slug: str) -> str:
    job = resolve_job(job_slug)
    if not job:
        return job_slug
    aliases = [job.slug, job.display_name, *job.aliases]
    return " ".join(dict.fromkeys(aliases))
```

### Acceptance Criteria

- Job change history queries create job wiki primary target.
- Source summary fallback is present.
- Generic queries search without job filter.
- Planner is deterministic.

### Agent Prompt

```text
Implement v07-06 only.

Add retrieval models and planner.

Files:
- src/retrieval/__init__.py
- src/retrieval/models.py
- src/retrieval/planner.py
- tests/test_v07_retrieval.py

Rules:
- Job change history queries must prefer wiki_type=job and topic=<job>.
- Source summary fallback must be included.
- Generic search must remain unfiltered.
- Do not implement database search yet.
- Run:
  python -m unittest tests.test_v07_retrieval -v
  python -m py_compile src/retrieval/models.py src/retrieval/planner.py
```

---

## v07-07. Filtered FTS search

### Goal

Search `wiki_fts` with optional `wiki_pages.type` and topic/job filtering.

### Files

Create/update:

```text
src/retrieval/fts_search.py
src/retrieval/models.py
tests/test_v07_retrieval.py
```

May reuse:

```text
tools/search_kb.py
```

### Red tests

Add tests that create temporary `wiki_pages` and `wiki_fts` rows.

```python
def test_search_wiki_filters_by_wiki_type_job():
    ...

def test_search_wiki_filters_by_topic():
    ...

def test_search_wiki_returns_source_summary_fallback():
    ...

def test_search_wiki_sanitizes_fts_query():
    ...
```

### Implementation

Add `SearchResult` model:

```python
@dataclass(frozen=True)
class SearchResult:
    page_id: str
    title: str
    wiki_type: str
    path: str
    score: float | None
    snippet: str
    topic: str | None
```

`src/retrieval/fts_search.py` should:

- connect to SQLite
- sanitize FTS query using existing `tools.search_kb.format_query` or equivalent
- join `wiki_fts` with `wiki_pages`
- apply optional filters
- return `SearchResult`

Expected SQL idea:

```sql
SELECT wiki_fts.page_id,
       wiki_fts.title,
       wiki_pages.type,
       wiki_pages.path,
       wiki_pages.job,
       wiki_fts.rank AS score,
       snippet(wiki_fts, -1, '', '', '...', 48) AS snippet
FROM wiki_fts
JOIN wiki_pages ON wiki_fts.page_id = wiki_pages.id
WHERE wiki_fts MATCH ?
  AND (? IS NULL OR wiki_pages.type = ?)
  AND (? IS NULL OR wiki_pages.job = ? OR wiki_fts.page_id = ?)
ORDER BY rank
LIMIT ?
```

### Acceptance Criteria

- Can return `job_gunbreaker` when filtering `wiki_type=job`, `topic=gunbreaker`.
- Can search source summaries when filtering `wiki_type=source_summary`.
- Unsafe FTS characters do not crash.
- Existing `tools/search_kb.py` is not broken.

### Agent Prompt

```text
Implement v07-07 only.

Add filtered FTS search for the ask pipeline.

Files:
- src/retrieval/fts_search.py
- src/retrieval/models.py
- tests/test_v07_retrieval.py

Rules:
- Search wiki_fts joined with wiki_pages.
- Support wiki_type filter.
- Support topic/job filter.
- Reuse or preserve existing FTS query sanitization.
- Do not modify the output contract of tools/search_kb.py.
- Use temporary SQLite DBs in tests.
- Run:
  python -m unittest tests.test_v07_retrieval -v
  python -m py_compile src/retrieval/fts_search.py
```

---

## v07-08. Execute retrieval plan

### Goal

Execute primary search targets first, then fallback only if no results are found.

### Files

Create/update:

```text
src/retrieval/context_builder.py
src/retrieval/planner.py
tests/test_v07_retrieval.py
```

### Red tests

```python
def test_execute_retrieval_plan_uses_primary_first():
    ...

def test_execute_retrieval_plan_uses_fallback_when_primary_empty():
    ...

def test_execute_retrieval_plan_deduplicates_page_ids:
    ...
```

### Implementation

Function:

```python
def execute_retrieval_plan(
    plan: RetrievalPlan,
    *,
    db_path: Path,
) -> tuple[SearchResult, ...]:
    ...
```

Rules:

- Search primary targets in priority order.
- If primary returns results, do not run fallback.
- If all primary targets return empty, run fallback.
- Deduplicate by `page_id`.
- Limit total result count.

### Acceptance Criteria

- Primary job wiki result wins.
- Source summary fallback runs only when primary has no results.
- Duplicate `page_id` appears only once.

### Agent Prompt

```text
Implement v07-08 only.

Add retrieval plan execution.

Files:
- src/retrieval/context_builder.py or src/retrieval/planner.py
- tests/test_v07_retrieval.py

Rules:
- Execute primary targets first.
- Run fallback only if primary produces no results.
- Deduplicate by page_id.
- Respect plan.limit.
- Do not build answer text yet.
- Run:
  python -m unittest tests.test_v07_retrieval -v
```

---

# Batch C - Context Pack and Answer Composer

---

## v07-09. Context pack builder

### Goal

Convert retrieval results into answer-ready context documents.

### Files

Create/update:

```text
src/retrieval/context_builder.py
src/retrieval/models.py
tests/test_v07_context_builder.py
```

### Red tests

```python
def test_context_pack_includes_job_wiki_path():
    ...

def test_context_pack_includes_source_ids_from_content():
    ...

def test_context_pack_limits_excerpt_length():
    ...

def test_context_pack_empty_when_no_results():
    ...
```

### Implementation

Add models:

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


@dataclass(frozen=True)
class AskContextPack:
    question: str
    parsed_query: ParsedQuery
    retrieval_plan: RetrievalPlan
    contexts: tuple[ContextDocument, ...]
    confidence: str
```

Functions:

```python
def build_context_pack(
    question: str,
    parsed_query: ParsedQuery,
    retrieval_plan: RetrievalPlan,
    search_results: tuple[SearchResult, ...],
    *,
    root_path: Path,
    max_chars: int = 2000,
) -> AskContextPack:
    ...
```

Source ID extraction:

```text
source_id: patch_7_0
- source_id: patch_7_1
> Source: `local_xxx`
```

### Acceptance Criteria

- Context documents include path, title, page_id.
- File content excerpt is read from disk.
- source_ids are extracted when present.
- Missing file results in empty excerpt, not crash.
- Empty search results produce empty context pack.

### Agent Prompt

```text
Implement v07-09 only.

Add AskContextPack and ContextDocument building.

Files:
- src/retrieval/context_builder.py
- src/retrieval/models.py
- tests/test_v07_context_builder.py

Rules:
- Convert SearchResult into ContextDocument.
- Read content from root_path / result.path.
- Extract source_id references.
- Limit excerpt length.
- Missing files must not crash.
- Do not compose final answer yet.
- Run:
  python -m unittest tests.test_v07_context_builder -v
  python -m py_compile src/retrieval/context_builder.py
```

---

## v07-10. Citation and confidence helpers

### Goal

Provide small helpers for source formatting and confidence labels.

### Files

Create:

```text
src/answering/__init__.py
src/answering/citations.py
src/answering/confidence.py
tests/test_v07_answer_composer.py
```

### Red tests

```python
def test_collect_sources_includes_paths():
    ...

def test_collect_sources_includes_source_ids():
    ...

def test_confidence_no_context_returns_na():
    ...

def test_confidence_with_context_returns_source_grounded():
    ...
```

### Implementation

`src/answering/citations.py`:

```python
def collect_sources(contexts: tuple[ContextDocument, ...]) -> tuple[str, ...]:
    ...
```

`src/answering/confidence.py`:

```python
def confidence_for_context_count(count: int) -> str:
    return "source_grounded" if count > 0 else "N/A"
```

### Acceptance Criteria

- Source path is included.
- source_ids are included.
- Duplicates are removed.
- Confidence is deterministic.

### Agent Prompt

```text
Implement v07-10 only.

Add citation and confidence helpers.

Files:
- src/answering/__init__.py
- src/answering/citations.py
- src/answering/confidence.py
- tests/test_v07_answer_composer.py

Rules:
- Do not implement the full composer yet.
- Deduplicate sources while preserving order.
- Run:
  python -m unittest tests.test_v07_answer_composer -v
  python -m py_compile src/answering/citations.py src/answering/confidence.py
```

---

## v07-11. Grounded answer composer

### Goal

Compose deterministic answer text from context pack.

### Files

Create/update:

```text
src/answering/composer.py
tests/test_v07_answer_composer.py
```

### Red tests

```python
def test_answer_includes_source_path():
    ...

def test_answer_includes_source_id():
    ...

def test_answer_no_context_no_hallucination():
    ...

def test_answer_uses_source_grounded_confidence():
    ...

def test_answer_text_format_contains_required_sections():
    ...
```

### Implementation

Suggested model:

```python
@dataclass(frozen=True)
class Answer:
    body: str
    confidence: str
    sources: tuple[str, ...]
```

Function:

```python
def compose_answer(context_pack: AskContextPack) -> Answer:
    ...
```

Rules:

- If no contexts, return no-context answer.
- For job wiki, include excerpt lines.
- Include sources section.
- Include confidence.
- Do not add facts not present in excerpts.

### Acceptance Criteria

- Text answer is deterministic.
- Sources are included.
- No context produces no hallucination.
- Job wiki answer includes content excerpt.

### Agent Prompt

```text
Implement v07-11 only.

Add deterministic grounded answer composer.

Files:
- src/answering/composer.py
- tests/test_v07_answer_composer.py

Rules:
- No LLM calls.
- Use only context_pack content.
- Include source paths and source_ids.
- No-context answer must say no relevant KB document was found.
- Run:
  python -m unittest tests.test_v07_answer_composer -v
  python -m py_compile src/answering/composer.py
```

---

# Batch D - tools/ask.py CLI

---

## v07-12. `tools/ask.py` skeleton and JSON contract

### Goal

Add the official ask CLI with stable JSON output.

### Files

Create:

```text
tools/ask.py
tests/test_v07_ask_cli.py
```

### Red tests

```python
def test_ask_cli_json_contract_no_context():
    ...

def test_ask_cli_rejects_empty_question():
    ...

def test_ask_cli_debug_includes_parsed_query_and_retrieval_plan():
    ...
```

### Implementation

CLI options:

```text
question
--format json|text
--debug
--limit
--db-path
--root-path
```

Skeleton flow:

```python
parsed = parse_query(question)
plan = build_retrieval_plan(parsed, limit=args.limit)
results = execute_retrieval_plan(plan, db_path=args.db_path)
context_pack = build_context_pack(...)
answer = compose_answer(context_pack)
print json or text
```

### JSON Contract

```json
{
  "status": "ok",
  "question": "...",
  "parsed_query": {},
  "retrieval_plan": {},
  "contexts": [],
  "answer": {
    "format": "text",
    "body": "...",
    "confidence": "...",
    "sources": []
  },
  "actions": []
}
```

### Acceptance Criteria

- CLI exists.
- JSON output is parseable.
- Empty question returns status=error.
- Debug mode includes parsed query and retrieval plan.

### Agent Prompt

```text
Implement v07-12 only.

Add tools/ask.py with JSON output contract.

Files:
- tools/ask.py
- tests/test_v07_ask_cli.py

Rules:
- Wire together parse_query, build_retrieval_plan, retrieval execution, context builder, and composer.
- Support --format json|text, --debug, --limit, --db-path, --root-path.
- Empty question must return status=error.
- Do not implement Discord.
- Do not implement crawling.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
  python -m py_compile tools/ask.py
```

---

## v07-13. Text output mode

### Goal

Make `tools/ask.py --format text` produce readable output.

### Files

Update:

```text
tools/ask.py
tests/test_v07_ask_cli.py
```

### Red tests

```python
def test_ask_cli_text_output_contains_answer_body():
    ...

def test_ask_cli_text_output_no_json_braces():
    ...
```

### Implementation

If `--format text`, print only the composed answer body.

### Acceptance Criteria

- Text output is readable.
- Text output does not print raw JSON.
- JSON mode remains stable.

### Agent Prompt

```text
Implement v07-13 only.

Add text output mode to tools/ask.py.

Files:
- tools/ask.py
- tests/test_v07_ask_cli.py

Rules:
- --format text prints the answer body only.
- --format json remains unchanged.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```

---

## v07-14. Job wiki first E2E

### Goal

Prove that a job change question uses `wiki/jobs/<job>.md` before source summaries.

### Files

Update:

```text
tests/test_v07_ask_cli.py
```

### Red test

Build temporary DB and files:

```text
wiki/jobs/gunbreaker.md
wiki/source_summaries/patch_7_0.md
```

Index them using existing `index_wiki_documents()`.

Test:

```python
def test_ask_cli_job_change_history_uses_job_wiki_first():
    ...
```

Expected:

- `contexts[0].page_id == "job_gunbreaker"`
- answer includes `wiki/jobs/gunbreaker.md`
- answer includes job wiki content

### Acceptance Criteria

- Derived job wiki is primary context.
- Source summary is not primary when job wiki exists.

### Agent Prompt

```text
Implement v07-14 only.

Add E2E test proving tools/ask.py uses job wiki first.

Files:
- tests/test_v07_ask_cli.py
- update implementation if needed

Rules:
- Use temporary root and SQLite DB.
- Create wiki/jobs/gunbreaker.md and wiki/source_summaries/*.md fixtures.
- Use tools.compile_wiki.index_wiki_documents() for indexing.
- Assert job_gunbreaker is first context.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```

---

## v07-15. Source summary fallback E2E

### Goal

Prove that when job wiki is missing, source summaries are used.

### Files

Update:

```text
tests/test_v07_ask_cli.py
```

### Red test

Temporary setup:

```text
wiki/source_summaries/patch_7_0.md
no wiki/jobs/gunbreaker.md
```

Expected:

- First context type is `source_summary`
- answer includes source summary path
- answer includes `source_id`

### Acceptance Criteria

- Fallback works.
- No job wiki does not cause empty answer if source summary exists.

### Agent Prompt

```text
Implement v07-15 only.

Add E2E fallback test for tools/ask.py.

Files:
- tests/test_v07_ask_cli.py
- update implementation if needed

Rules:
- If job wiki is missing, source_summary fallback must run.
- Answer must include source summary path or source_id.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```

---

# Batch E - Documentation and Final Verification

---

## v07-16. Runbook documentation

### Goal

Document how to use v07 ask pipeline.

### Files

Create/update:

```text
docs/runbooks/ask.md
docs/plans/v07/README.md
docs/handoff/CURRENT_HANDOFF.md
```

### Content Requirements

`docs/runbooks/ask.md` must include:

```text
- Purpose
- CLI examples
- JSON output example
- Text output example
- Debug mode
- Job wiki first policy
- Source summary fallback policy
- No-context behavior
- Known limitations
```

### Acceptance Criteria

- Next agent can understand ask pipeline from docs.
- No crawling is documented as v07 behavior.
- Discord integration is explicitly future work.

### Agent Prompt

```text
Implement v07-16 only.

Document the v07 Grounded Ask Pipeline.

Files:
- docs/runbooks/ask.md
- docs/plans/v07/README.md
- docs/handoff/CURRENT_HANDOFF.md

Rules:
- Do not mention crawling as part of v07.
- State that Discord integration is future work.
- Include examples for --format json, --format text, and --debug.
- Run:
  python scripts/check_docs_freshness.py --all
```

---

## v07-17. Full regression verification

### Goal

Run the full test suite and confirm v07 did not break v06.

### Required commands

```bash
python -m unittest tests.test_v07_query_parser -v
python -m unittest tests.test_v07_retrieval -v
python -m unittest tests.test_v07_context_builder -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v

python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v

python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

### Acceptance Criteria

- All v07 tests pass.
- Existing v06 tests pass.
- Full test suite passes.
- Docs freshness check passes.
- `python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json` returns valid JSON.

### Agent Prompt

```text
Implement v07-17 verification only.

Run all v07 tests, all v06 tests, full unittest discovery, and docs freshness check.

Do not modify code unless a test failure reveals a real bug.
If fixing is required:
- explain the failing test
- patch only the minimal affected files
- rerun the relevant tests
- then rerun the full verification commands

Report:
- commands run
- pass/fail result
- files changed
- remaining known limitations
```

---

## 3. Recommended Batch Execution Order

Use the following execution order when assigning to an agent.

```text
Batch A:
v07-01
v07-02
v07-03
v07-04
v07-05

Batch B:
v07-06
v07-07
v07-08

Batch C:
v07-09
v07-10
v07-11

Batch D:
v07-12
v07-13
v07-14
v07-15

Batch E:
v07-16
v07-17
```

Do not assign all tasks at once unless the agent is explicitly instructed to keep commits small and stop after each batch.

---

## 4. Suggested High-Level Agent Prompt

Use this when giving the entire v07 plan to a coding agent.

```text
You are implementing v07 Grounded Ask Pipeline for ffxiv-claw-bot.

Read first:
1. docs/specs/0007-v07-grounded-ask-pipeline.md
2. docs/runbooks/process-source.md
3. docs/runbooks/generate-derived-wiki.md
4. docs/handoff/CURRENT_HANDOFF.md
5. src/derived_wiki/job_catalog.py
6. tools/search_kb.py
7. tools/answer.py
8. tools/compile_wiki.py

Scope:
- Implement query parsing, retrieval planning, context pack building, deterministic grounded answer composition, and tools/ask.py.
- Do not implement crawling.
- Do not implement polling.
- Do not implement Discord.
- Do not call an LLM.
- Preserve search_kb.py and answer.py compatibility.

Work style:
- Implement one v07 task at a time.
- For each task, write red tests first.
- Run the relevant tests after implementation.
- Keep changes minimal and documented.
- Update docs only in the documentation task unless needed for correctness.

Final acceptance:
- tools/ask.py can answer "7.x 건브레이커 변경 이력 알려줘" using wiki/jobs/gunbreaker.md first.
- If job wiki is missing, source_summaries fallback works.
- Answers include source path or source_id.
- No-context answers do not hallucinate.
- Full test suite passes.
```

---

## 5. Known Limitations After v07

v07 will still not support:

```text
- Discord slash commands
- automatic official patchnote crawling
- webhook receiver
- scheduled polling
- LLM-generated fluent answers
- vector search
- raid/item/system derived wiki generation
- expansion-name patch mapping
```

These should be handled in later phases.

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
- context-only fluent answer generation
```

---

## 6. Final v07 Definition

```text
v07 = Grounded Ask Pipeline
```

It turns the v06 knowledge base into a usable question-answering backend.

```text
question
→ parse
→ plan
→ retrieve
→ context
→ answer
```

The core value is that user questions can now use derived wiki documents such as `wiki/jobs/gunbreaker.md` directly, instead of forcing every answer to re-search many source summaries.
