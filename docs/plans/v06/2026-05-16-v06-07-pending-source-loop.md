# v0.6-07: Pending Source Automation Loop

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-7)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`
- Parent v0.5 spec: `docs/specs/0004-v05-source-processing-pipeline.md`

## Status

Pending

## Goal

pending 상태의 source 여러 개를 일괄 처리하는 `tools/process_pending_sources.py` CLI를 구현한다.

`process_source.py`는 source 1건 처리 entrypoint 그대로 유지하고, 이 task는 그 위의 orchestration layer를 추가한다.

## Scope

- `tools/process_pending_sources.py` 신규 또는 보강
- source status DB access layer 정비 (필요 시)
- CLI 옵션 처리
- 처리 상태 전이 관리
- retry policy

CLI 계약:

```bash
python tools/process_pending_sources.py --limit 10
python tools/process_pending_sources.py --source-type local_file --limit 10
python tools/process_pending_sources.py --retry-errors --max-retry 3
python tools/process_pending_sources.py --dry-run
```

처리 흐름:

1. pending source 조회
2. `--limit` 적용
3. `--dry-run`은 대상 source_id만 출력하고 DB 변경 없음
4. 처리 시작 시 `in_progress`
5. `process_source` 호출
6. 성공: `processed` / `wiki_built` / `graph_built` 계열 상태 반영
7. 실패: `error`, `error_stage`, `error_message` 기록
8. `retry_count += 1`
9. `--retry-errors`가 있으면 `retry_count < max_retry`인 error source 재처리

Out of scope:

- derived wiki hook (v06-13에서 처리)
- scheduler/cron daemon
- Notion polling
- multi-process 병렬 처리

## Red Test

- File: `tests/test_v06_pending_sources.py`
- Implementation target: `tools/process_pending_sources.py`, source status DB access layer
- Expected red reason: pending loop CLI가 아직 존재하지 않거나 상태 전이/재시도 정책이 비어 있다.

Contracts fixed by the tests:

- pending source가 `--limit`까지 처리된다.
- `--dry-run`은 DB 상태를 변경하지 않는다.
- 성공한 source는 `processed`로 기록된다.
- 실패한 source는 `error`로 기록되고 `error_stage`, `error_message`가 존재한다.
- 실패 시 `retry_count`가 증가한다.
- `--retry-errors`는 `retry_count < max_retry`인 error source만 재처리한다.

## Checklist

- [ ] `tools/process_pending_sources.py` 생성
- [ ] argparse 옵션
  - [ ] `--limit` (default 10)
  - [ ] `--source-type` (optional filter)
  - [ ] `--dry-run`
  - [ ] `--retry-errors`
  - [ ] `--max-retry` (default 3)
  - [ ] `--db-path` (default `db/ffxiv.sqlite`)
  - [ ] `--storage-root` (default `/mnt/d/ffixiv-bot-storage`)
- [ ] DB access: pending source 조회 / 상태 전이 / retry_count 업데이트
- [ ] process_source 호출 wiring (직접 main 호출 또는 함수 import)
- [ ] dry-run 시 status 변경 금지
- [ ] result JSON 또는 stdout summary
- [ ] `tests/test_v06_pending_sources.py`에 다음 테스트
  - [ ] `test_pending_loop_processes_pending_sources_up_to_limit`
  - [ ] `test_pending_loop_dry_run_does_not_mutate_status`
  - [ ] `test_pending_loop_marks_successful_source_processed`
  - [ ] `test_pending_loop_marks_failed_source_error`
  - [ ] `test_pending_loop_increments_retry_count`
  - [ ] `test_retry_errors_only_retries_below_max_retry`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_pending_sources -v
python tools/process_pending_sources.py --dry-run --limit 3
```

기존 회귀:

```bash
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v06_extractors -v
```

## Key Decisions

- v0.6 pending loop는 daemon/scheduler가 아니다. 사용자가 명시적으로 CLI를 실행할 때만 동작한다.
- pending loop는 `process_source.py`의 stable JSON output을 소비한다. 새 schema를 만들지 않는다.
- retry policy는 `retry_count` + `max_retry` 단순 비교만 구현한다. exponential backoff 등은 후속 버전.
- Notion direct API 호출은 금지한다 (`process_source.py`가 `notion_update` payload만 생성하는 boundary 유지).

## Implementation Notes

- DB schema에 이미 status/retry_count column이 있는지 확인 후, 없으면 spec/plan 갱신 후 추가한다 (Open Question 1 참조).
- `tools/process_source.py`가 main 함수를 노출하지 않으면 subprocess + JSON parse fallback도 허용한다.
- 한 source 처리 실패가 전체 loop를 중단시키지 않도록 try/except로 격리한다.
- `--source-type` filter는 DB column이 존재할 때만 의미가 있다. 없으면 본 task에서 보류하고 README에 명시한다.

## Verification Results

- Pending.
