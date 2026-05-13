# Test Runbook

## 기본 테스트

현재 레포에서 실제 가능한 기본 테스트 명령은 `unittest`다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

현재 확인된 결과:

```text
Ran 3 tests
OK
```

## 특정 테스트

Drive sync dry-run 테스트:

```bash
python -m unittest tests.test_sync_drive
```

## pytest

현재 레포에는 pytest 설정이나 requirements가 없다. 따라서 pytest를 기본 테스트 명령으로 쓰지 않는다.

pytest가 필요해지면 dependency와 실행 방식을 별도 plan/spec에서 먼저 정한다.
