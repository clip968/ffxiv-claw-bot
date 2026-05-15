# v0.5-04: Local Source Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 5] Supported Source Types (text_note, markdown_file, plain_text_file), [Sec 7] Storage Model, [Sec 10.3] Local Ingest
- Runbook: `docs/runbooks/local-storage.md`

## Status

**Pending**

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

- [ ] `--body`로 받은 텍스트를 임시 파일로 생성 (in-memory 또는 tempfile)
- [ ] 생성한 파일을 `ingest_local._do_ingest()` 또는 유사 함수로 전달
- [ ] source_id, canonical_path, raw_path, content_hash 반환
- [ ] 저장 위치: `{storage_root}/sources/{category}/{title_slug}.md`
- [ ] `--local-path`가 가리키는 `.md` 파일을 `ingest_local._do_ingest()`로 전달
- [ ] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [ ] raw snapshot 생성
- [ ] `--local-path`가 가리키는 `.txt` 파일을 `ingest_local._do_ingest()`로 전달
- [ ] 외부 파일을 `/mnt/d/ffixiv-bot-storage/sources/{category}/`로 복사
- [ ] raw snapshot 생성
- [ ] 필요시 `.md`로 변환 (body wrapping)
- [ ] `process_source.py`의 pipeline sequence에 ingest step 추가
- [ ] ingest 성공 여부에 따라 rebuild skip 결정
- [ ] ingest 실패 시 `status=error`, `graph_status=skipped`
- [ ] `test_process_text_note_ok` — apply text_note → source_id 반환
- [ ] `test_process_markdown_file_ok` — apply markdown_file → source_id 반환
- [ ] `test_process_plain_text_file_ok` — apply plain_text_file → source_id 반환
- [ ] `test_process_ingest_error_skips_rebuild` — ingest 실패 시 rebuild skip

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Test" --body "hello" --storage-root /tmp/test-storage
python tools/process_source.py --apply --source-type markdown_file --category raid_guides --local-path /tmp/test.md --storage-root /tmp/test-storage
```

## Key Decisions

- 기존 `ingest_local.py`의 ingest 로직을 재사용한다. process_source.py는 orchestration만 담당한다.
- `text_note`는 body를 파일로 저장해야 하므로 tempfile을 생성한 후 ingest_local로 전달한다.
