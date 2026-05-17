# v0.8.5-06: Improve Ask Answer Quality

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 6)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

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

- [ ] red test 작성: `tests/test_v08_5_answer_quality.py`
  - [ ] `test_answer_not_raw_source_dump`
  - [ ] `test_answer_has_summary_section`
  - [ ] `test_answer_has_related_entities`
  - [ ] `test_answer_has_sources_section`
  - [ ] `test_answer_has_uncertainty_when_sparse`
  - [ ] `test_format_text_outputs_body_only`
  - [ ] `test_existing_v07_v08_tests_pass`
- [ ] red 상태 확인
- [ ] Step 1: Context classification
  - [ ] context를 wiki_type별로 분류 (job, patch, skill, source_summary, 기타)
  - [ ] 이미 있는 page metadata를 활용
- [ ] Step 2: Evidence extraction
  - [ ] 질문 term 또는 matched entity alias 포함 문장 우선
  - [ ] trigger keyword 포함 문장 우선 (changed, adjusted, duration, potency, cooldown, 변경, 조정, 상향, 하향)
  - [ ] evidence 문장 최대 N개, 각 최대 M자 제한
- [ ] Step 3: Answer sections 조립
  - [ ] 요약 (1~3문장)
  - [ ] 관련 항목 (Job/Patch/Skill)
  - [ ] 확인된 내용 (evidence bullet)
  - [ ] 근거 (source path/source id bullet)
  - [ ] 주의 (context 부족, source 제한 등)
- [ ] Step 4: No source dump guard
  - [ ] context body 전체를 그대로 append하지 않음
  - [ ] source 경로는 근거 섹션에만 표시
- [ ] Step 5: Confidence 유지
  - [ ] context 0개: low
  - [ ] source summary 1개 이상: medium
  - [ ] derived wiki + source summary: medium/high
  - [ ] 자동 high 남발 금지
- [ ] 수정 대상 파일
  - [ ] `src/answering.py` (우선)
  - [ ] 필요 시 `src/retrieval/context_builder.py`
  - [ ] 필요 시 `tools/ask.py`
- [ ] JSON output schema 유지 확인
- [ ] `--format text` 동작 확인
- [ ] 기존 v07/v08 ask tests 통과 확인
- [ ] 최소 코드 수정으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_v08_5_answer_quality -v
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

- 수정 우선순위는 `src/answering.py`다.
- JSON 출력 schema를 변경하지 않는다.
- 한국어 질문에 대해 한국어 구조화 답변을 기본으로 한다.
- retrieval이 아니라 answer composition을 개선한다.

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
