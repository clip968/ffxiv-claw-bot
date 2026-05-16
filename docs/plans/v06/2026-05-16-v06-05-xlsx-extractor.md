# v0.6-05: XLSX Extractor

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-5)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Pending

## Goal

Excel workbook(`.xlsx`)을 sheet별 Markdown table로 변환하는 extractor를 구현한다.

## Scope

- `src/source_processing/extractors/xlsx.py` 추가
- `openpyxl` 사용 (필요 시 dependency 명시)
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
- Fixture: `tests/fixtures/source_files/sample.xlsx` (multi-sheet, 빈 sheet 포함)
- Implementation target: `src/source_processing/extractors/xlsx.py`
- Expected red reason: xlsx extractor module이 아직 stub이거나 multi-sheet 처리/메타데이터 미구현.

Contracts fixed by the tests:

- single sheet workbook이 정상 추출된다.
- sheet name이 추출 텍스트의 heading에 포함된다.
- multi-sheet workbook의 모든 non-empty sheet가 추출된다.
- empty sheet는 텍스트에 나오지 않지만 metadata `empty_sheets`에 기록된다.
- metadata.sheet_count, metadata.sheet_names가 정확하다.

## Checklist

- [ ] `tests/fixtures/source_files/sample.xlsx` 추가 (multi-sheet, 빈 sheet 포함)
- [ ] `openpyxl` dependency 확인 (requirements.txt에 없으면 spec/plan 갱신 필요)
- [ ] `src/source_processing/extractors/xlsx.py` 구현
  - [ ] workbook open (read-only, data_only=True)
  - [ ] sheet iteration
  - [ ] empty sheet skip + metadata 기록
  - [ ] header 추출 (첫 non-empty row 또는 fallback)
  - [ ] Markdown table 생성
  - [ ] metadata `sheet_count`, `sheet_names`, `total_row_count`, `empty_sheets`
  - [ ] `extractor_name=xlsx`
- [ ] `extractor_registry.py`의 `.xlsx` stub을 실제 함수로 교체
- [ ] `tests/test_v06_extractors.py`에 다음 테스트 추가
  - [ ] `test_xlsx_extractor_reads_single_sheet`
  - [ ] `test_xlsx_extractor_preserves_sheet_name`
  - [ ] `test_xlsx_extractor_reads_multiple_sheets`
  - [ ] `test_xlsx_extractor_records_sheet_metadata`
  - [ ] `test_xlsx_extractor_skips_empty_sheets_but_records_them`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

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

- `openpyxl`은 read-only, `data_only=True` 모드로 사용해 formula evaluation을 피하고 저장된 값만 읽는다.
- merged cell은 top-left 셀의 값만 사용하고 별도 처리하지 않는다 (v0.6 단순 범위).
- 매우 큰 workbook은 stream read로 처리하지만, v0.6에서는 단순 iteration으로 충분하다.
- fixture는 binary file이므로 직접 작성하거나 작은 generator script로 생성한다. fixture 생성 스크립트가 필요하면 `tests/fixtures/source_files/_build_sample_xlsx.py` 같은 helper를 함께 둔다.

## Implementation Notes

- v06-01의 model/error, v06-02의 registry에 의존한다.
- chart/image/style/formula 의미 분석 미지원은 README/handoff에 반복 명시해야 한다.
- empty workbook (sheet가 0개)이 들어오면 `SourceParseError` 또는 빈 결과로 처리할지 정책을 결정한다. 권장: 빈 결과 + metadata.

## Verification Results

- Pending.
