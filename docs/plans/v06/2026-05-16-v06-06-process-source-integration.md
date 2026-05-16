# v0.6-06: process_source.py Integration with Extractor Layer

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-6)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`
- Parent v0.5 spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Parent v05.1 spec: `docs/specs/0004a-v05.1-source-processing-hardening.md`

## Status

Pending

## Goal

기존 `tools/process_source.py`가 local file source를 처리할 때 v0.6 extractor registry를 사용하도록 연결한다.

`--body` 기반 ingest 경로와 URL fetch 경로는 그대로 유지하고, `--local-path` 기반 file source만 extractor layer를 경유시킨다.

## Scope

- `tools/process_source.py`에서 `--local-path` 처리 분기 변경
- file source path가 들어오면 `extract_source_text(path)` 호출
- 반환된 `ExtractedSource.text`를 ingest body로 사용
- `ExtractedSource.metadata`를 source metadata 또는 processing metadata에 보존
- extractor 실패 시 `stage=extract`로 error 처리
  - `UnsupportedSourceExtensionError`
  - `SourceDecodingError`
  - `SourceParseError`
- 기존 `--body` 직접 전달 동작 유지
- v05.1 Lodestone URL 라우팅 보호 (URL 경로는 v05.1 그대로 유지)

Out of scope:

- pending source loop (v06-07)
- derived wiki hook (v06-13)
- URL fetch 경로 변경
- Notion payload schema 변경

## Red Test

- File: `tests/test_v06_extractors.py` 또는 `tests/test_v05_process_source.py` 보강
- Implementation target: `tools/process_source.py`, 관련 ingest module
- Expected red reason: `--local-path` 처리 시 extractor가 호출되지 않거나 unsupported extension이 ingest 단계 error로 흘러간다.

Contracts fixed by the tests:

- `.md` local file을 `--local-path`로 처리하면 source summary까지 생성된다.
- `.xlsx` local file을 `--local-path`로 처리하면 extractor에서 normalize된 text가 ingest된다.
- `.png` 같은 미지원 파일은 `status=error`, `error_stage=extract`로 결과 JSON에 기록된다.
- extractor metadata (예: sheet_count) 가 result JSON의 metadata block에 보존된다.

## Checklist

- [ ] `tools/process_source.py` `--local-path` 분기 식별
- [ ] extractor registry import (`from src.source_processing import extract_source_text`)
- [ ] file source 처리 시 `extract_source_text(path)` 호출
- [ ] 반환된 `text`를 ingest body로 사용
- [ ] 반환된 metadata를 result JSON 또는 source record에 저장
- [ ] extractor exception을 `stage=extract` error로 변환
  - [ ] `UnsupportedSourceExtensionError` → `error_message: Unsupported source extension: ...`
  - [ ] `SourceDecodingError` → `error_message: Decoding failed: ...`
  - [ ] `SourceParseError` → `error_message: Parse failed: ...`
- [ ] `--body` 기반 text_note 경로 회귀 보호
- [ ] URL 경로 회귀 보호 (Lodestone 포함)
- [ ] 테스트 추가
  - [ ] `test_process_source_uses_extractor_for_local_file_source`
  - [ ] `test_process_source_records_extract_error_for_unsupported_file`
  - [ ] `test_process_source_preserves_extracted_metadata`
  - [ ] `test_process_source_text_note_body_path_unchanged`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

apply smoke (선택):

```bash
python tools/process_source.py --dry-run \
  --source-type markdown_file --category personal_notes \
  --local-path tests/fixtures/source_files/sample.md
```

## Key Decisions

- `--body` 기반 경로는 손대지 않는다. extractor는 file path가 있을 때만 호출된다.
- URL 경로는 v05.1 fetch_url/Lodestone 라우팅을 그대로 사용한다. v0.6 extractor는 file source 전용이다.
- extractor metadata가 Notion payload에 직접 들어가지 않도록 한다. v0.5 boundary (`notion_update` payload-only) 유지.
- 미지원 확장자는 ingest 이전에 실패해야 한다. raw/local_storage에 파일을 복사하지 않거나, 복사 후 status=error로 표기한다 (구현 정책은 코드 확인 후 결정).

## Implementation Notes

- v06-01~v06-05 완료가 전제조건이다.
- `process_source.py`가 source body를 인자로 직접 받는 경우와 file path를 받는 경우를 명확히 구분한다.
- result JSON의 `actions` 배열에 `name=extract` action을 추가해 extractor 실행 상태를 명시하면 디버깅이 쉽다.
- pending loop (v06-07)와 derived wiki hook (v06-13)이 같은 JSON 구조를 사용하므로 schema를 함부로 깨지 않는다.

## Verification Results

- Pending.
