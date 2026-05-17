# v0.7-09: Context Pack Builder

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-09)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

검색 결과(`SearchResult`)를 answer-ready context document로 변환하고, 파일 본문을 읽어 excerpt를 포함하는 `AskContextPack`을 생성한다.

## Scope

- `src/retrieval/context_builder.py`에 `build_context_pack()` 함수 추가
- `ContextDocument` model (page_id, wiki_type, title, path, score, snippet, content_excerpt, source_ids)
- `AskContextPack` model (question, parsed_query, retrieval_plan, contexts, confidence)
- 파일 본문 읽기 (root_path / result.path)
- source_id 추출 (content에서 `source_id: xxx` 패턴 파싱)
- excerpt 길이 제한 (max_chars)
- 파일 미존재 시 빈 excerpt (crash 금지)

Out of scope:

- citation formatting (v07-10)
- answer composition (v07-11)
- LLM 요약

## Red Test

- File: `tests/test_v07_context_builder.py`
- Implementation target: `src/retrieval/context_builder.py`, `src/retrieval/models.py`
- Expected red reason: `ContextDocument`, `AskContextPack` 미정의 또는 `build_context_pack` 미존재.

Contracts fixed by the tests:

- context에 job wiki path가 포함된다.
- content에서 source_id가 추출된다.
- excerpt가 max_chars 이하로 제한된다.
- 검색 결과가 없으면 빈 context pack이 반환된다.
- 파일이 없어도 crash하지 않는다.

## Checklist

- [x] `src/retrieval/models.py` 갱신
  - [x] `ContextDocument` frozen dataclass 추가
  - [x] `AskContextPack` frozen dataclass 추가
- [x] `src/retrieval/context_builder.py` 갱신
  - [x] `build_context_pack()` 함수 구현
  - [x] 파일 본문 읽기 로직
  - [x] source_id 추출 regex
  - [x] excerpt 길이 제한
  - [x] 파일 미존재 시 safe fallback
- [x] `tests/test_v07_context_builder.py` 생성
  - [x] `test_context_pack_includes_job_wiki_path`
  - [x] `test_context_pack_includes_source_ids_from_content`
  - [x] `test_context_pack_limits_excerpt_length`
  - [x] `test_context_pack_empty_when_no_results`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_context_builder -v
python -m py_compile src/retrieval/context_builder.py
```

## Key Decisions

- source_id 추출 패턴: `source_id: <value>`, `- source_id: <value>`, `> Source: \`<value>\``
- 파일 미존재 시 `content_excerpt = ""`, `source_ids = ()`.
- max_chars 기본값은 2000.
- confidence는 context 존재 여부에 따라 결정 (0개면 "N/A", 1개 이상이면 "source_grounded").

## Implementation Notes

- v07-06의 `RetrievalPlan`, v07-07의 `SearchResult`, v07-08의 실행 결과에 의존한다.
- test에서는 임시 디렉토리에 mock wiki 파일을 생성하여 테스트한다.
- 이 함수는 `tools/ask.py` 파이프라인의 핵심 단계이다.

## Agent Prompt

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
