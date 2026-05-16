# v0.6-02: Extractor Registry

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-2)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

파일 확장자에 따라 extractor function을 선택하는 registry를 구현한다.

`process_source.py`나 pending loop가 확장자별 분기 로직을 직접 들고 있지 않도록, 단일 entrypoint(`extract_source_text(path)`)로 호출하면 적절한 extractor를 찾아 실행하는 layer를 만든다.

## Scope

- `src/source_processing/extractor_registry.py` 추가
- `src/source_processing/extractors/__init__.py` 추가
- `EXTRACTORS` mapping 정의
- `get_extractor_for_path(path)` 구현
- `extract_source_text(path) -> ExtractedSource` 구현
- 미지원 확장자에서 `UnsupportedSourceExtensionError` 발생
- suffix는 case-insensitive로 처리 (`.HTML`, `.XLSX` 등)
- 초기 mapping에는 실제 구현이 없는 확장자에 대해 lazy import 또는 stub 함수를 연결 가능 (실제 함수 구현은 v06-03~v06-05)

지원 확장자:

```text
.txt
.md
.html
.htm
.csv
.xlsx
```

Out of scope:

- 각 확장자별 실제 extractor 로직 (v06-03~v06-05)
- `tools/process_source.py` 통합 (v06-06)
- pending loop (v06-07)
- derived wiki (v06-08 이후)

## Red Test

- File: `tests/test_v06_extractors.py`
- Implementation target: `src/source_processing/extractor_registry.py`, `src/source_processing/extractors/__init__.py`
- Expected red reason: registry module이 아직 존재하지 않거나 `get_extractor_for_path`가 정의되지 않아 import/attribute error.

Contracts fixed by the tests:

- `.txt`, `.md`, `.html`, `.htm`, `.csv`, `.xlsx`는 각각 대응되는 extractor를 반환한다.
- 대문자 확장자(`.HTML`, `.XLSX`)도 같은 extractor로 resolve된다.
- 미지원 확장자(`.png`, `.pdf`)는 `UnsupportedSourceExtensionError`를 발생시킨다.
- error 메시지에 실제 path와 extension이 들어간다.

## Checklist

- [x] `src/source_processing/extractors/__init__.py` 생성
- [x] `src/source_processing/extractor_registry.py` 생성
  - [x] `EXTRACTORS: dict[str, Callable[[str], ExtractedSource]]`
  - [x] `get_extractor_for_path(path: str | Path)`
  - [x] `extract_source_text(path: str | Path) -> ExtractedSource`
  - [x] case-insensitive suffix 처리
  - [x] 미지원 확장자에서 `UnsupportedSourceExtensionError`
- [x] 확장자별 stub 함수 임시 연결 (v06-03~v06-05에서 교체)
- [x] `tests/test_v06_extractors.py`에 다음 테스트 추가
  - [x] `test_registry_selects_text_extractor_for_txt`
  - [x] `test_registry_selects_markdown_extractor_for_md`
  - [x] `test_registry_selects_html_extractor_for_html_and_htm`
  - [x] `test_registry_selects_csv_extractor_for_csv`
  - [x] `test_registry_selects_xlsx_extractor_for_xlsx`
  - [x] `test_registry_is_case_insensitive`
  - [x] `test_registry_raises_for_unsupported_extension`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환
- [x] README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_v06_extractors -v
python -m py_compile src/source_processing/extractor_registry.py src/source_processing/extractors/__init__.py
```

## Key Decisions

- registry는 `Path.suffix.lower()` 기준으로 lookup한다.
- registry는 lazy import를 허용하지만, 테스트 단순화를 위해 v06-02에서는 stub 함수로 등록한 뒤 v06-03~v06-05에서 실제 함수로 교체한다.
- registry는 `process_source.py`가 의존하는 단일 entrypoint(`extract_source_text`)만 노출한다. 내부 mapping은 직접 사용하지 않도록 권장한다.
- 미지원 확장자 error는 pending loop에서 `error_stage=extract`로 기록되어야 하므로, 메시지 포맷을 변경하지 않도록 주의한다.

## Implementation Notes

- 이 task는 v06-01의 `ExtractedSource`, `UnsupportedSourceExtensionError`에 의존한다. 두 task 사이의 import path를 깨지 않도록 한다.
- registry는 `process_source.py`나 `process_pending_sources.py`에서 호출되지만, 이 task에서는 아직 통합하지 않는다.
- 향후 PDF/DOCX/OCR 등 v0.7+ 확장은 동일 registry pattern으로 확장하므로, mapping 확장이 쉬운 구조를 유지한다.

## Verification Results

- Red: `python -m unittest tests.test_v06_extractors.V06ExtractorRegistryTests -v` failed with 8 expected `ModuleNotFoundError: No module named 'src.source_processing.extractor_registry'` errors before implementation.
- Green: `python -m unittest tests.test_v06_extractors -v` passed 13 tests.
- Compile: `python -m py_compile src/source_processing/extractor_registry.py src/source_processing/extractors/__init__.py src/source_processing/__init__.py` passed.
