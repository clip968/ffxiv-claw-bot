# Docs 기반 작업 워크플로우

이 프로젝트의 작업 기준은 레포 내부 `docs/` 문서다. Notion은 source of truth가 아니며, 요약과 링크를 남기는 인덱스 역할만 한다.

## 기본 흐름

1. 문제 또는 기능 요구를 확인한다.
2. 관련 spec을 `docs/specs/`에서 확인한다.
3. spec이 없으면 `docs/specs/`에 작성한다.
4. 기술적 결정이 필요하면 `docs/adrs/`에 ADR을 작성한다.
5. 구현 전 `docs/plans/`에 작은 구현 계획을 작성한다.
6. 구현한다.
7. 작업 종료 전 `python scripts/finish_task.py`를 실행한다.
8. 결과를 `docs/handoff/CURRENT_HANDOFF.md`에 반영한다.
9. Notion에는 요약과 링크만 반영한다.

## 문서 역할

- spec은 구현이 따라야 하는 계약이다.
- ADR은 이미 결정한 이유를 보존하는 문서다.
- plan은 구현 전 작업 계획이다.
- runbook은 반복 가능한 명령 모음이다.
- handoff는 다음 agent가 읽는 첫 문서다.
- archive는 현재 기준 실행 대상이 아닌 문서를 보관한다.

## 작업 규칙

- Notion은 source of truth가 아니다.
- 코드 변경과 spec 변경이 함께 필요하면 같은 작업 단위에서 관리한다.
- 큰 변경은 `spec -> ADR -> plan -> implementation -> tests -> handoff` 순서로 진행한다.
- 구현 코드와 무관한 문서 정리는 `documentation-only change`로 취급한다.
- 문서를 실제로 읽었는지 직접 증명할 수는 없다. 대신 `docs/DOC_OWNERS.yml`의 경로별 required docs mapping으로 코드 변경에 대응되는 문서 산출물이 갱신됐는지 검증한다.
- 매핑된 코드 파일이 바뀌면 required docs 중 최소 하나가 같은 작업 트리 변경에 포함되어야 한다. 기본 검증은 `Reviewed docs`만으로 통과시키지 않는다.
- runbook에는 추측한 명령을 쓰지 않는다. 확실하지 않으면 `TODO`로 남긴다.
- 오래된 handoff나 폐기된 계획은 삭제하지 말고 `docs/archive/`로 옮긴다.
- 작업 종료 전 `python scripts/finish_task.py`를 실행한다.
- `finish_task.py`는 unittest, 전체 작업 트리 대상 docs freshness check, Notion dry-run, `git status --short`, `git diff --stat`을 한 번에 실행한다.
- pre-commit은 staged 파일만 대상으로 `check_docs_freshness.py --staged`를 계속 사용할 수 있다.
- Notion apply는 기본 종료 검증에 포함하지 않는다. Notion은 mirror/index이고, `docs/handoff/CURRENT_HANDOFF.md`가 원본이다.

## Required docs mapping

`docs/DOC_OWNERS.yml`은 코드 경로별 required docs를 정의한다.

예시:

```yaml
tools/sync_drive.py:
  required_docs:
    - docs/specs/0003-google-drive-sync.md
    - docs/runbooks/sync-drive.md
    - docs/handoff/CURRENT_HANDOFF.md
```

`check_docs_freshness.py --all`은 staged, unstaged, untracked 파일을 모두 검사한다. 변경된 코드 파일이 `DOC_OWNERS.yml`에 있으면 해당 `required_docs` 중 하나가 변경되어야 통과한다.

예외적으로 `check_docs_freshness.py --allow-reviewed-docs`를 쓰면 `docs/handoff/CURRENT_HANDOFF.md`의 `Reviewed docs` 섹션에 적힌 문서도 required docs 확인으로 인정할 수 있다. 기본 workflow와 `finish_task.py`는 이 옵션을 쓰지 않는다.

## 작업 시작 체크

1. `git status --short`
2. `git branch --show-current`
3. `git log --oneline -5`
4. `git diff --stat`
5. `docs/handoff/CURRENT_HANDOFF.md` 확인

uncommitted 변경이 있으면 되돌리지 않는다. 현재 작업과 무관한 변경은 건드리지 않는다.

## 작업 종료 체크

```bash
python scripts/finish_task.py
```

예외 상황이 아니면 skip 옵션을 쓰지 않는다.
