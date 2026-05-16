# v0.6-01: Extractor Model and Error Layer

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-1)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md` (SPEC 0006)
- Parent v0.5 spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Parent v05.1 spec: `docs/specs/0004a-v05.1-source-processing-hardening.md`

## Status

Completed 2026-05-16

## Goal

모든 source extractor가 공통으로 사용할 `ExtractedSource` 모델과 `SourceExtractionError` 계열 error class를 추가한다.

이 task는 v0.6 extractor layer의 토대를 만드는 단계이며, 실제 extractor 구현(`.txt`, `.md`, `.html`, `.csv`, `.xlsx`)은 후속 task에서 다룬다.

## Scope

- `src/source_processing/` 패키지 추가
- `ExtractedSource` data model 정의 (title, text, metadata)
- `SourceExtractionError` base class 정의
- `UnsupportedSourceExtensionError` 정의 (extension, source_path 보존)
- `SourceDecodingError` 정의
- `SourceParseError` 정의
- 필수 metadata key 계약 문서화 (`source_path`, `extension`, `extracted_at`, `extractor_name`)

Out of scope:

- extractor registry 구현 (v06-02 책임)
- 실제 extractor 구현 (v06-03~v06-05 책임)
- `tools/process_source.py` 연결 (v06-06 책임)
- pending source loop (v06-07 책임)
- derived wiki (v06-08 이후 책임)

## Red Test

- File: `tests/test_v06_extractors.py`
- Implementation target: `src/source_processing/models.py`, `src/source_processing/errors.py`, `src/source_processing/__init__.py`
- Expected red reason: `src.source_processing` 패키지가 아직 존재하지 않아 import 또는 attribute access가 실패한다.

Contracts fixed by the tests:

- `ExtractedSource`는 `title`, `text`, `metadata` 세 필드를 가진다.
- `ExtractedSource`는 `text`와 `metadata` 없이는 생성되지 않는다.
- `UnsupportedSourceExtensionError`는 메시지에 extension과 source path를 포함한다.
- `SourceDecodingError`와 `SourceParseError`는 `SourceExtractionError`를 상속한다.
- 모든 error는 `__init__`에서 받은 정보를 attribute로 보존한다.

## Checklist

- [x] `src/source_processing/__init__.py` 생성
- [x] `src/source_processing/models.py` 생성 (`ExtractedSource`)
- [x] `src/source_processing/errors.py` 생성
  - [x] `SourceExtractionError` base
  - [x] `UnsupportedSourceExtensionError(extension, source_path)`
  - [x] `SourceDecodingError`
  - [x] `SourceParseError`
- [x] 필수 metadata 계약 docstring 추가
  - [x] `source_path`
  - [x] `extension`
  - [x] `extracted_at`
  - [x] `extractor_name`
- [x] `tests/test_v06_extractors.py` 생성 또는 갱신
  - [x] `test_extracted_source_requires_text_and_metadata`
  - [x] `test_extracted_source_preserves_title_text_metadata`
  - [x] `test_unsupported_extension_error_includes_extension_and_path`
  - [x] `test_source_decoding_error_is_extraction_error`
  - [x] `test_source_parse_error_is_extraction_error`
- [x] red 상태 확인 (`python -m unittest tests.test_v06_extractors -v`)
- [x] 최소 구현으로 green 전환
- [x] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_v06_extractors -v
python -m py_compile src/source_processing/models.py src/source_processing/errors.py src/source_processing/__init__.py
```

Full regression (선택):

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Key Decisions

- `src/source_processing/`는 repo 내 새 패키지로 추가한다. 기존 `tools/extractors/` (v05.1 Lodestone) 와 별도 layer이며, 향후 통합 여부는 v0.6 이후 결정한다.
- `ExtractedSource`는 우선 `@dataclass`로 시작한다. 외부 의존성(예: pydantic) 추가는 금지한다.
- error 메시지는 한국어가 아니라 로그/JSON 친화적인 영어 문장으로 유지한다 (`Unsupported source extension: .png (path=...)`).
- `extracted_at`은 ISO8601 UTC string으로 통일한다.

## Implementation Notes

- 이 task는 행동 변경이 없으므로 process_source.py / pending loop / wiki에 영향을 주지 않아야 한다.
- import path는 `from src.source_processing import ExtractedSource, UnsupportedSourceExtensionError` 형태가 되도록 `__init__.py`에 re-export 한다.
- 추후 v06-02 registry는 이 모델과 error를 그대로 사용한다.

## Verification Results

- Red: `python -m unittest tests.test_v06_extractors -v` failed with 5 expected `ModuleNotFoundError: No module named 'src'` errors before implementation.
- Green: `python -m unittest tests.test_v06_extractors -v` passed 5 tests.
- Compile: `python -m py_compile src/source_processing/models.py src/source_processing/errors.py src/source_processing/__init__.py src/__init__.py` passed.
