# v0.6-05: XLSX Extractor

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-5)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

Excel workbook(`.xlsx`)을 sheet별 Markdown table로 변환하는 extractor를 구현한다.

## Scope

- `src/source_processing/extractors/xlsx.py` 추가
- 표준 라이브러리 `zipfile` + `xml.etree.ElementTree` 사용
- workbook의 모든 sheet 순회
- empty sheet skip하되 metadata에 기록
- sheet name을 heading으로 보존
- 첫 번째 non-empty row를 header로 사용 (또는 `Column 1`, `Column 2` fallback)
- 셀 값은 저장된 값 기준 추출 (formula 결과 evaluation 금지)
- chart, image, style 무시
- metadata에 `sheet_count`, `sheet_names`, `total_row_count`, `empty_sheets`

Out of scope:

- formula evaluation
- chart/image parsing
- style/format 보존
- merged cell 정밀 처리 (단순 fallback만)
- CSV extractor 변경 (v06-04에서 종료)

권장 출력 예시:

```markdown
# Source: sample.xlsx

## Sheet: Dungeon Drops

| Dungeon | Boss | Item | Drop Rate |
|---|---|---|---|
| The Aetherfont | Lyngbakr | Hypostatic Gear | Unknown |

## Sheet: Currency

| Content | Token | Weekly Limit |
|---|---|---|
| Raid | Savage Book | 1 per floor |
```

## Red Test

- File: `tests/test_v06_extractors.py`
- Fixture: 테스트 내부에서 임시 `sample.xlsx` 생성 (multi-sheet, 빈 sheet 포함)
- Implementation target: `src/source_processing/extractors/xlsx.py`
- Expected red reason: xlsx extractor module이 아직 stub이거나 multi-sheet 처리/메타데이터 미구현.

Contracts fixed by the tests:

- single sheet workbook이 정상 추출된다.
- sheet name이 추출 텍스트의 heading에 포함된다.
- multi-sheet workbook의 모든 non-empty sheet가 추출된다.
- empty sheet는 텍스트에 나오지 않지만 metadata `empty_sheets`에 기록된다.
- metadata.sheet_count, metadata.sheet_names가 정확하다.

## Checklist

- [x] 테스트 내부에서 임시 `sample.xlsx` 생성 (multi-sheet, 빈 sheet 포함)
- [x] `openpyxl` dependency 확인 (not installed); 새 dependency 없이 표준 라이브러리 reader로 구현
- [x] `src/source_processing/extractors/xlsx.py` 구현
  - [x] workbook zip/XML load
  - [x] sheet iteration
  - [x] empty sheet skip + metadata 기록
  - [x] header 추출 (첫 non-empty row)
  - [x] Markdown table 생성
  - [x] metadata `sheet_count`, `sheet_names`, `total_row_count`, `empty_sheets`
  - [x] `extractor_name=xlsx`
- [x] `extractor_registry.py`의 `.xlsx` stub을 실제 함수로 교체
- [x] `tests/test_v06_extractors.py`에 다음 테스트 추가
  - [x] `test_xlsx_extractor_reads_single_sheet`
  - [x] `test_xlsx_extractor_preserves_sheet_name`
  - [x] `test_xlsx_extractor_reads_multiple_sheets`
  - [x] `test_xlsx_extractor_records_sheet_metadata`
  - [x] `test_xlsx_extractor_skips_empty_sheets_but_records_them`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_extractors -v
python -m py_compile src/source_processing/extractors/xlsx.py
```

기존 extractor 회귀:

```bash
python -m unittest tests.test_v06_extractors -v
```

## Key Decisions

- `openpyxl`은 현재 환경에 설치되어 있지 않으므로 도입하지 않는다. v06-05는 표준 라이브러리 `zipfile`과 `xml.etree.ElementTree`로 minimal `.xlsx` sheet XML을 읽는다.
- merged cell은 top-left 셀의 값만 사용하고 별도 처리하지 않는다 (v0.6 단순 범위).
- 매우 큰 workbook은 후속 최적화 대상이다. v0.6에서는 workbook zip/XML을 단순 순회한다.
- binary fixture는 repo에 추가하지 않고 `tests/test_v06_extractors.py`의 helper가 임시 `.xlsx` 파일을 생성한다.

## Implementation Notes

- v06-01의 model/error, v06-02의 registry에 의존한다.
- chart/image/style/formula 의미 분석 미지원은 README/handoff에 반복 명시해야 한다.
- empty workbook (sheet가 0개)이 들어오면 `SourceParseError` 또는 빈 결과로 처리할지 정책을 결정한다. 권장: 빈 결과 + metadata.

## Verification Results

- Red: `python -m unittest tests.test_v06_extractors.V06XlsxExtractorTests -v` failed with 5 expected missing `src.source_processing.extractors.xlsx` import errors and 1 registry stub content failure.
- Green: `python -m unittest tests.test_v06_extractors -v` passed 32 tests.
- Compile: `python -m py_compile src/source_processing/extractors/xlsx.py src/source_processing/extractors/__init__.py` passed.
