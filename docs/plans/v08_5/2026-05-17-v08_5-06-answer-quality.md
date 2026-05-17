# v0.8.5-06: Improve Ask Answer Quality

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 6)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Completed 2026-05-17

## Goal

`ask.py` 결과가 raw source dump처럼 보이지 않고, 주제별 grounded summary로 보이도록 개선한다.

## Scope

- answer composer 개선: source dump → 구조화 요약
- context classification (wiki_type별 분류)
- evidence extraction (질문 관련 핵심 문장 추출)
- answer section 조립 (요약/관련 항목/확인된 내용/근거/주의)
- no source dump guard
- confidence 유지
- JSON output schema 유지

Out of scope:

- retrieval pipeline 전체 재작성
- LLM API 호출
- vector DB 도입
- 새 namespace 추가

## Red Test

- File: `tests/test_v08_5_answer_quality.py`
- Implementation target: ask answer 구조화 품질

Contracts fixed by the tests:

1. 답변이 source body 전체를 그대로 덤프하지 않는다.
2. 답변에 `요약` 섹션이 있다.
3. 답변에 `관련 항목` 또는 entity list가 있다.
4. 답변에 `근거` 섹션이 있다.
5. source가 부족하면 `주의` 또는 불확실성 문구가 있다.
6. `--format text`는 answer body만 출력한다.
7. 기존 `tests.test_v07_ask_cli`와 `tests.test_v08_e2e`가 깨지지 않는다.

## Checklist

- [x] red test 작성: `tests/test_v08_5_answer_quality.py`
  - [x] `test_answer_not_raw_source_dump`
  - [x] `test_answer_has_summary_section`
  - [x] `test_answer_has_related_entities`
  - [x] `test_answer_has_confirmed_content_and_sources_sections`
  - [x] `test_answer_has_uncertainty_when_sparse`
  - [x] `test_format_text_outputs_body_only`
- [x] red 상태 확인
- [x] Step 1: Context classification
  - [x] context를 wiki_type별로 분류 (job, patch, skill, source_summary, 기타)
  - [x] 이미 있는 page metadata를 활용
- [x] Step 2: Evidence extraction
  - [x] 질문 term 또는 matched entity alias 포함 문장 우선
  - [x] trigger keyword 포함 문장 우선 (changed, adjusted, duration, potency, cooldown, 변경, 조정, 상향, 하향)
  - [x] evidence 문장 최대 N개, 각 최대 M자 제한
- [x] Step 3: Answer sections 조립
  - [x] 요약 (1~3문장)
  - [x] 관련 항목 (Job/Patch/Skill)
  - [x] 확인된 내용 (evidence bullet)
  - [x] 근거 (source path/source id bullet)
  - [x] 주의 (context 부족, source 제한 등)
- [x] Step 4: No source dump guard
  - [x] context body 전체를 그대로 append하지 않음
  - [x] source 경로는 근거 섹션에만 표시
- [x] Step 5: Confidence 유지
  - [x] context 0개: `N/A`
  - [x] context 1개 이상: `source_grounded`
  - [x] 자동 high 남발 금지
- [x] 수정 대상 파일
  - [x] `src/answering/composer.py`
- [x] JSON output schema 유지 확인
- [x] `--format text` 동작 확인
- [x] 기존 v07/v08 ask tests 통과 확인
- [x] 최소 코드 수정으로 green 전환
- [x] handoff/README feature map status 갱신

## Results

- 최초 red 상태: `tests/test_v08_5_answer_quality.py` 6개 중 5개 실패. 현재 composer가 raw context body를 그대로 붙이고 `요약`, `관련 항목`, `확인된 내용` 섹션을 만들지 않는 것이 원인.
- 구현 결과: `compose_answer()`가 `요약`, `관련 항목`, `확인된 내용`, `근거 문서`, `확실도`, `주의` 섹션을 조립한다.
- evidence extraction: question term과 trigger keyword를 우선하며, generated boilerplate와 source marker는 제외한다.
- no source dump guard: `# Gunbreaker` 같은 원문 heading이나 unrelated TOC line을 answer body에 직접 덤프하지 않는다.
- sparse context: evidence가 없거나 source summary/source id가 없으면 `근거가 제한적입니다` 주의 문구를 추가한다.
- `--format text`는 계속 answer body만 출력한다.

## Verification

```bash
python -m unittest tests.test_v08_5_answer_quality -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v
python -m unittest tests.test_v08_e2e -v
```

Smoke:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

## Key Decisions

- 실제 수정 파일은 패키지 구조상 `src/answering/composer.py`다.
- JSON 출력 schema를 변경하지 않는다.
- 한국어 질문에 대해 한국어 구조화 답변을 기본으로 한다.
- retrieval이 아니라 answer composition을 개선한다.
- confidence model은 이번 task에서 확장하지 않고 기존 `source_grounded`/`N/A` 계약을 유지한다.

## Implementation Notes

- `compose_answer()` 또는 해당 함수에서 context body를 section 단위로 조립한다.
- 기존 `Answer.confidence` 구조가 있다면 유지한다.
- 기존 v07/v08 ask tests가 깨지지 않도록 answer 구조 변경은 additive하게 한다.

## Agent Prompt

```text
v08.5 Task 6을 수행한다.
먼저 tests/test_v08_5_answer_quality.py에 red test를 작성한다.
src/answering.py를 수정하여 ask 답변을 구조화한다: 요약, 관련 항목, 확인된 내용, 근거, 주의.
source body를 그대로 덤프하지 않고 evidence를 추출한다.
JSON schema와 기존 테스트 호환성을 유지한다.
```
