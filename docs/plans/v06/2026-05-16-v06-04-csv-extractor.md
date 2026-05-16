# v0.6-04: CSV Extractor

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-4)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Pending

## Goal

CSV 파일을 column header가 보존된 Markdown table (또는 structured text)로 변환하는 extractor를 구현한다.

## Scope

- `src/source_processing/extractors/csv.py` 추가
- Python 표준 `csv` 모듈 사용 (pandas 새 dependency 추가 금지)
- header row 보존
- row values 보존
- Markdown table 출력
- metadata에 `row_count`, `column_count`, `columns` 기록
- `extractor_name=csv`
- 비어 있는 CSV 처리: 빈 metadata + 명확한 빈 결과 또는 `SourceParseError`

Out of scope:

- XLSX extractor (v06-05)
- `process_source.py` 통합 (v06-06)
- chart/style/formula 처리

권장 출력 예시:

```markdown
# Source: sample.csv

| Dungeon | Boss | Item |
|---|---|---|
| The Aetherfont | Lyngbakr | Hypostatic Gear |
```

## Red Test

- File: `tests/test_v06_extractors.py`
- Fixture: `tests/fixtures/source_files/sample.csv`
- Implementation target: `src/source_processing/extractors/csv.py`
- Expected red reason: csv extractor module이 아직 stub이거나 metadata 미구현.

Contracts fixed by the tests:

- CSV header가 추출 텍스트에 포함된다.
- 모든 row value가 추출 텍스트에 포함된다.
- 출력은 Markdown table 형식이다.
- metadata.columns는 실제 CSV header와 일치한다.
- metadata.row_count, metadata.column_count가 정확하다.
- 비어 있는 CSV는 명확한 error 또는 빈 table metadata로 처리된다.

## Checklist

- [ ] `tests/fixtures/source_files/sample.csv` 추가 (헤더 + 데이터 행 여러 개)
- [ ] `src/source_processing/extractors/csv.py` 구현
  - [ ] csv.reader 기반 파싱
  - [ ] header 보존
  - [ ] Markdown table 생성
  - [ ] metadata `row_count`, `column_count`, `columns`
  - [ ] `extractor_name=csv`
  - [ ] 비어 있는 CSV 처리 정책 결정 (빈 table 또는 `SourceParseError`)
- [ ] `extractor_registry.py`의 `.csv` stub을 실제 함수로 교체
- [ ] `tests/test_v06_extractors.py`에 다음 테스트 추가
  - [ ] `test_csv_extractor_preserves_headers`
  - [ ] `test_csv_extractor_preserves_rows`
  - [ ] `test_csv_extractor_outputs_markdown_table`
  - [ ] `test_csv_extractor_records_row_and_column_metadata`
  - [ ] `test_csv_extractor_handles_empty_file`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_extractors -v
python -m py_compile src/source_processing/extractors/csv.py
```

기존 extractor 회귀:

```bash
python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

## Key Decisions

- Python 표준 `csv` 모듈만 사용한다. pandas는 dependency 추가 정책 위반이므로 도입하지 않는다.
- 값 안에 `|` 문자가 들어 있는 경우 Markdown table이 깨지지 않도록 escape 또는 substitute 한다.
- 매우 큰 CSV에 대비해 streaming read를 권장하나, v0.6에서는 단순 list-of-rows로 충분하다.
- 비어 있는 CSV는 본 task에서 `SourceParseError` 대신 빈 table을 반환하는 정책을 권장한다. (pending loop에서 처리 완료로 인정하기 위함)

## Implementation Notes

- 이 task는 v06-01의 model/error와 v06-02의 registry에 의존한다.
- 추출된 Markdown text는 후속 ingest pipeline에 그대로 들어가므로, heading(`# Source: <filename>`)을 포함하여 source summary가 의미를 가지도록 한다.
- BOM이 포함된 CSV는 `utf-8-sig`로 처리해 첫 컬럼 이름 손상을 막는다.

## Verification Results

- Pending.
