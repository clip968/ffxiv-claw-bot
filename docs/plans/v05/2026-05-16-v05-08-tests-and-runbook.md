# v0.5-08: Tests and Runbook

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 20] Test Plan, [Sec 21] Acceptance Criteria, [Sec 25] Verification Commands
- Runbook: `docs/runbooks/process-source.md`

## Status

**Pending**

## Goal

v0.5 전체의 테스트를 완료하고, runbook 문서를 작성하며, handoff 문서를 갱신한다.

## Scope

- 누락된 unit test 보강
- `docs/runbooks/process-source.md` 작성
- `docs/handoff/CURRENT_HANDOFF.md`에 v0.5 완료 상태 기록
- `docs/WORKFLOW.md` 업데이트 (필요시)
- `CLAUDE.md` 업데이트 (필요시)
- `docs/FILE_INVENTORY.md` 업데이트
- 최종 verification 실행

Red tests coverage:
- `test_process_text_note_ok`
- `test_process_markdown_file_ok`
- `test_process_plain_text_file_ok`
- `test_process_url_ok`
- `test_process_dry_run_does_not_write`
- `test_process_missing_body_returns_error`
- `test_process_missing_url_returns_error`
- `test_process_missing_local_path_returns_error`
- `test_process_ingest_error_skips_rebuild`
- `test_process_rebuild_error_returns_partial`
- `test_process_graph_failure_sets_graph_status_failed`
- `test_process_notion_payload_excludes_body`
- `test_process_text_note_e2e_creates_source_wiki_fts_graph`

Out of scope:
- v0.6 Automation Loop 기능
- Notion queue polling
- scheduler 구현

## Red Test

- File: all v0.5 test files
- Implementation target: all v0.5 implementation files

## Checklist

- [ ] v05-03~07에서 누락된 unit test가 있으면 추가
- [ ] 모든 test 파일이 테스트 runner에서 발견되는지 확인
- [ ] `test_process_text_note_e2e_creates_source_wiki_fts_graph` — e2e smoke (mock/fixture 기반)
- [ ] `docs/runbooks/process-source.md` 작성:
  - [ ] process_source.py CLI 사용법
  - [ ] source type별 예시
  - [ ] dry-run 사용법
  - [ ] 출력 JSON 설명
  - [ ] OpenClaw skill 호출 순서
  - [ ] 문제 해결 가이드
- [ ] `docs/handoff/CURRENT_HANDOFF.md`에 v0.5 완료 상태 기록
- [ ] 새 CLI 사용법 예시
- [ ] 남은 제한 사항 (한국어 검색, binary attachment 등)
- [ ] `docs/WORKFLOW.md` 업데이트 (필요시)
- [ ] `CLAUDE.md` 업데이트 (필요시)
- [ ] `docs/FILE_INVENTORY.md` 업데이트

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py --skip-notion-dry-run
# 수동 smoke test
python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "v05 smoke" --body "Test"
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "v05 smoke" --body "Test"
python tools/search_kb.py "v05 smoke"
python tools/answer.py "v05 smoke" --format text
```
