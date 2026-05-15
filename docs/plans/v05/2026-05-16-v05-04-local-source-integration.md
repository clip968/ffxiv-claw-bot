# v05-04: Local Source Integration

## Goal

`process_source.py`가 `text_note`, `markdown_file`, `plain_text_file` 세 가지 로컬 source type을 실제로 ingest할 수 있도록 기존 `ingest_local.py`를 연결한다.

## Spec Reference

- [Sec 5] Supported Source Types (text_note, markdown_file, plain_text_file)
- [Sec 7] Storage Model
- [Sec 10.3] Local Ingest
- [Sec 20.1] Test Plan

## Tasks

### 1. text_note ingest integration

- [ ] `--body`로 받은 텍스트를 임시 파일로 생성 (in-memory 또는 tempfile)
- [ ] 생성한 파일을 `ingest_local._do_ingest()` 또는 유사 함수로 전달
- [ ] source_id, canonical_path, raw_path, content_hash 반환
- [ ] 저장 위치: `{storage_root}/sources/{category}/{title_slug}.md`

### 2. markdown_file ingest integration

- [ ] `--local-path`가 가리키는 `.md` 파일을 `ingest_local._do_ingest()`로 전달
- [ ] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [ ] raw snapshot 생성

### 3. plain_text_file ingest integration

- [ ] `--local-path`가 가리키는 `.txt` 파일을 `ingest_local._do_ingest()`로 전달
- [ ] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [ ] raw snapshot 생성
- [ ] 필요시 `.md`로 변환 (body wrapping)

### 4. pipeline step wiring

- [ ] `process_source.py`의 pipeline sequence에 ingest step 추가
- [ ] ingest 성공 여부에 따라 rebuild skip 결정
- [ ] ingest 실패 시 `status=error`, `graph_status=skipped`

### 5. Tests

- [ ] `test_process_text_note_ok` — apply text_note → source_id 반환
- [ ] `test_process_markdown_file_ok` — apply markdown_file → source_id 반환
- [ ] `test_process_plain_text_file_ok` — apply plain_text_file → source_id 반환
- [ ] `test_process_ingest_error_skips_rebuild` — ingest 실패 시 rebuild skip

## Red Test

`tests/test_v05_process_source.py` (기존 파일에 테스트 추가)

## Completion

- text_note, markdown_file, plain_text_file 모두 ingest 가능
- ingest 결과가 JSON action log에 기록됨
- ingest 실패 시 rebuild skip
