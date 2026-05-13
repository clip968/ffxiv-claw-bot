# Finish Task Runbook

작업 종료 전에는 단일 명령으로 검증을 실행한다.

```bash
python scripts/finish_task.py
```

## 실행 단계

`finish_task.py`는 다음을 순서대로 실행한다.

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python scripts/check_docs_freshness.py --all`
3. `python scripts/sync_notion_handoff.py --dry-run`
4. `git status --short`
5. `git diff --stat`

하나라도 실패하면 전체 exit code는 1이다.

## 실패 시 대응

- unittest 실패: 실패한 테스트를 먼저 고친다.
- docs freshness 실패: 전체 작업 트리에서 코드 변경과 관련된 required docs가 함께 변경됐는지 확인한다.
- Notion dry-run 실패: `docs/handoff/CURRENT_HANDOFF.md`가 존재하는지 확인한다.
- git 상태 확인: 의도하지 않은 파일이 섞였는지 확인한다.

## Docs freshness check

`finish_task.py`는 `check_docs_freshness.py --all`을 실행한다.

`--all`은 다음 파일을 모두 검사한다.

- staged 파일
- unstaged 파일
- untracked 파일

`check_docs_freshness.py`는 `docs/DOC_OWNERS.yml`의 required docs mapping을 읽는다. 매핑된 코드 파일이 변경되면 해당 `required_docs` 중 최소 하나가 변경되어야 통과한다.

이 검사는 agent가 문서를 실제로 읽었는지 증명하지 않는다. 대신 코드 변경에 대응되는 spec/runbook/handoff 산출물이 작업 트리에 반영됐는지를 검증한다.

pre-commit은 staged 파일만 대상으로 `check_docs_freshness.py --staged`를 계속 사용할 수 있다.

`check_docs_freshness.py --allow-reviewed-docs`는 `docs/handoff/CURRENT_HANDOFF.md`의 `Reviewed docs` 섹션을 보조 증거로 인정하는 옵션이다. 기본 `finish_task.py` 실행은 더 엄격하게 required docs 변경만 인정한다.

## Skip 옵션

예외 상황에서만 사용한다.

```bash
python scripts/finish_task.py --skip-tests
python scripts/finish_task.py --skip-docs-check
python scripts/finish_task.py --skip-notion-dry-run
```

skip 옵션을 쓰면 출력에 `SKIP`이 명확히 표시된다.

## Notion

기본 실행은 Notion apply를 하지 않는다.

`finish_task.py`는 `sync_notion_handoff.py --dry-run`만 실행한다. `docs/handoff/CURRENT_HANDOFF.md`가 source of truth이고, Notion은 mirror/index다.
