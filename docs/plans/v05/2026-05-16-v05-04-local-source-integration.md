# v0.5-04: Local Source Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 5] Supported Source Types (text_note, markdown_file, plain_text_file), [Sec 7] Storage Model, [Sec 10.3] Local Ingest
- Runbook: `docs/runbooks/local-storage.md`

## Status

**Completed** 2026-05-16

## Goal

`process_source.py`가 `text_note`, `markdown_file`, `plain_text_file` 세 가지 로컬 source type을 실제로 ingest할 수 있도록 기존 `ingest_local.py`를 연결한다.

## Scope

- `text_note`: `--body`로 받은 텍스트를 파일로 생성 → `ingest_local`로 전달
- `markdown_file`: `--local-path`의 `.md` 파일을 Local Storage로 복사
- `plain_text_file`: `--local-path`의 `.txt` 파일을 Local Storage로 복사 (필요시 `.md` 변환)
- pipeline sequence에 ingest step 추가
- ingest 성공/실패에 따른 rebuild skip 결정
- 저장 위치: `{storage_root}/sources/{category}/{title_slug}.md`

Out of scope:

- URL fetch 구현 (v05-05)
- rebuild 연결 (v05-06)
- Notion payload 생성 (v05-07)

## Red Test

- File: `tests/test_v05_process_source.py` (기존 파일에 테스트 추가)
- Implementation target: `tools/process_source.py`, `tools/ingest_local.py`
- Current red reason: local source ingest가 process_source.py에 연결되지 않음.
- Contract fixed by the test:
  - `text_note` apply가 source_id를 반환한다.
  - `markdown_file` apply가 source_id를 반환한다.
  - `plain_text_file` apply가 source_id를 반환한다.
  - ingest 실패 시 rebuild step이 skip된다.

## Checklist

- [x] `--body`로 받은 텍스트를 Local Storage ingest body로 전달
- [x] 생성한 body를 `ingest_local.ingest_source()`로 전달
- [x] source_id, canonical_path, raw_path, content_hash 반환
- [x] 저장 위치: `{storage_root}/sources/{category}/{title_slug}.md`
- [x] `--local-path`가 가리키는 `.md` 파일을 `ingest_local.ingest_source()`로 전달
- [x] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [x] raw snapshot 생성
- [x] `--local-path`가 가리키는 `.txt` 파일을 `ingest_local.ingest_source()`로 전달
- [x] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [x] raw snapshot 생성
- [x] `.txt` 입력도 canonical Local Storage 경로는 `.md`로 저장
- [x] `process_source.py`의 pipeline sequence에 ingest step 추가
- [x] ingest 성공 여부에 따라 rebuild skip 결정
- [x] ingest 실패 시 `status=error`, `graph_status=skipped`
- [x] `test_process_text_note_ok` — apply text_note → source_id 반환
- [x] `test_process_markdown_file_ok` — apply markdown_file → source_id 반환
- [x] `test_process_plain_text_file_ok` — apply plain_text_file → source_id 반환
- [x] `test_process_ingest_error_skips_rebuild` — ingest 실패 시 rebuild skip

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v04_ingest_local_cli tests.test_v04_local_rebuild -v
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/process_source.py tools/ingest_local.py
```

## Key Decisions

- 기존 `ingest_local.py`의 ingest 로직을 `ingest_source()` 함수로 노출해 재사용한다. `process_source.py`는 orchestration만 담당한다.
- `text_note`는 body를 그대로 ingest body로 전달한다. 별도 URL fetch, rebuild 실행, Notion 성공 payload 생성은 v05-05~v05-07 범위로 남긴다.
- `markdown_file`과 `plain_text_file`은 `--local-path` 파일을 UTF-8 텍스트로 읽어 Local Storage ingest에 전달한다.
- `plain_text_file`도 v05-04 저장 규칙에 맞춰 canonical path와 raw snapshot 확장자를 `.md`로 사용한다.
- v05-04에서 rebuild는 실행하지 않는다. ingest 성공 시 `rebuild` action은 `skipped`/`v05-06_not_implemented`, ingest 실패 시 `skipped`/`upstream_ingest_error`다.

## Implementation Notes

- `tools/process_source.py`
  - `text_note`, `markdown_file`, `plain_text_file` apply path를 Local Storage ingest로 연결했다.
  - 성공 JSON에 `source_id`, `canonical_path`, `local_source_path`, `raw_path`, `content_hash`, `graph_status=skipped`를 포함한다.
  - URL, binary attachment, rebuild, Notion success payload는 구현하지 않았다.
- `tools/ingest_local.py`
  - CLI 내부 로직을 재사용 가능한 `ingest_source()`로 분리했다.
  - `root_path`를 주입 가능하게 해 테스트가 repo 실제 `raw/`를 오염시키지 않게 했다.
- `tests/test_v05_process_source.py`
  - `test_process_text_note_ok`
  - `test_process_markdown_file_ok`
  - `test_process_plain_text_file_ok`
  - `test_process_ingest_error_skips_rebuild`

## Verification Results

- 2026-05-16: red 확인 완료. 네 local integration test는 skeleton에서 실패했다.
- 2026-05-16: `python -m unittest tests.test_v05_process_source -v` — 12 tests OK.
- 2026-05-16: `python -m unittest tests.test_v04_ingest_local_cli tests.test_v04_local_rebuild -v` — 4 tests OK.
- 2026-05-16: `python -m unittest discover -s tests -p "test_*.py"` — 110 tests OK.
- 2026-05-16: `python -m py_compile tools/process_source.py tools/ingest_local.py` — OK.
