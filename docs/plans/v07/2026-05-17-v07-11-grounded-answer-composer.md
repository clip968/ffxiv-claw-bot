# v0.7-11: Grounded Answer Composer

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-11)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

context pack으로부터 결정론적 answer text를 생성하는 `compose_answer()` 함수를 구현한다. LLM을 사용하지 않는다.

## Scope

- `src/answering/composer.py` 추가
- `Answer` model (body, confidence, sources)
- `compose_answer(context_pack: AskContextPack) -> Answer` 함수
- context가 있으면 excerpt 기반 answer body 생성
- context가 없으면 "no relevant KB document found" answer
- sources section 포함
- confidence 포함

Out of scope:

- LLM fluent answer generation
- CLI (v07-12)
- text formatting mode (v07-13)

## Red Test

- File: `tests/test_v07_answer_composer.py`
- Implementation target: `src/answering/composer.py`
- Expected red reason: `src.answering.composer` module 미존재 또는 `Answer` 미정의.

Contracts fixed by the tests:

- answer body에 source path가 포함된다.
- answer body에 source_id가 포함된다.
- context 없으면 hallucination 없는 no-context answer 반환
- confidence가 `"source_grounded"` 또는 `"N/A"` 중 하나
- answer text에 필수 섹션 포함 (Sources, Confidence)

## Checklist

- [ ] `src/answering/composer.py` 생성
  - [ ] `Answer` frozen dataclass (body, confidence, sources)
  - [ ] `compose_answer(context_pack: AskContextPack) -> Answer` 구현
  - [ ] no-context answer 로직
  - [ ] job wiki excerpt 포함 로직
  - [ ] sources section 생성
  - [ ] confidence 결정
- [ ] `tests/test_v07_answer_composer.py` 갱신
  - [ ] `test_answer_includes_source_path`
  - [ ] `test_answer_includes_source_id`
  - [ ] `test_answer_no_context_no_hallucination`
  - [ ] `test_answer_uses_source_grounded_confidence`
  - [ ] `test_answer_text_format_contains_required_sections`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_answer_composer -v
python -m py_compile src/answering/composer.py
```

## Key Decisions

- answer body는 excerpt를 그대로 포함한다. 재작성하지 않는다.
- no-context answer는 명확히 "관련 KB 문서를 찾지 못했습니다"라고 표기한다. 추측을 넣지 않는다.
- `Answer.body`는 plain text (Markdown 허용).
- `Answer.sources`는 path와 source_id를 모두 포함하는 tuple.

## Implementation Notes

- v07-09의 `AskContextPack`과 v07-10의 `collect_sources`, `confidence_for_context_count`에 의존한다.
- 이 함수가 `tools/ask.py`의 최종 출력물을 생성한다.
- LLM을 호출하지 않으므로 deterministic하다.

## Agent Prompt

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
