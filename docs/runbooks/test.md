# Test Runbook

## 기본 테스트

현재 레포에서 실제 가능한 기본 테스트 명령은 `unittest`다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

검증 결과는 작업 종료 시 `docs/handoff/CURRENT_HANDOFF.md`에 기록한다.

## 특정 테스트

Local Storage sync dry-run 테스트:

```bash
python -m unittest tests.test_sync_storage
```

Drive sync dry-run 테스트:

```bash
python -m unittest tests.test_sync_drive
```

## v0.4 Red Tests

The active v0.4 plan files name their red tests. These tests are expected to fail until the matching implementation slice is written.

```bash
python -m unittest tests.test_v04_openclaw_notion_control
python -m unittest tests.test_v04_ingest_local_cli
python -m unittest tests.test_v04_local_rebuild
python -m unittest tests.test_v04_status_notification
```

Current red targets:

- `tests/test_v04_openclaw_notion_control.py` -> `tools/openclaw_notion_control.py`
- `tests/test_v04_ingest_local_cli.py` -> `tools/ingest_local.py`
- `tests/test_v04_local_rebuild.py` -> `tools/local_rebuild.py`
- `tests/test_v04_status_notification.py` -> `tools/status_notification.py`

When these red tests are present and not yet implemented, full unittest discover is expected to fail on those planned v0.4 slices.

## pytest

현재 레포에는 pytest 설정이나 requirements가 없다. 따라서 pytest를 기본 테스트 명령으로 쓰지 않는다.

pytest가 필요해지면 dependency와 실행 방식을 별도 plan/spec에서 먼저 정한다.
