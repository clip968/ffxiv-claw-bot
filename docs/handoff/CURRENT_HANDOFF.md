# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`
- Current phase: docs-first workflow tooling 강화 진행

## 현재 상태

완료된 것:

- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run 완료
- docs 기반 workflow 정리
- 작업 종료 자동화 workflow
- DOC_OWNERS rule 기반 contract freshness 정책 도입
- check_docs_freshness.py 새 schema/TDD 정책 테스트 추가

현재 큰 흐름:

```text
URL / Drive / Discord note
  -> raw 저장
  -> sources DB 기록
  -> wiki markdown 생성
  -> SQLite FTS 색인
  -> search_kb.py 검색
  -> answer.py context pack 생성
  -> graph 구축
  -> graph path 포함 답변
```

Drive sync의 현재 완료 범위는 manifest 기반 `--dry-run`이다. manifest 기반 `--apply`, 실제 `raw/drive` 저장, `sources` DB upsert, 실제 Google Drive API/OAuth, Google Docs export/download는 아직 구현되지 않았다.

## Docs workflow 상태

구현 기준은 Notion이 아니라 레포 내부 Markdown 문서다. Notion은 handoff 요약과 링크를 남기는 mirror/index 역할만 한다.

- specs: 현재 시스템 동작 계약
- adrs: 기술적 결정 이유
- plans: 구현 전 작업 분해
- runbooks: 반복 실행 절차
- handoff: 다음 session 인계
- templates: 문서 작성 템플릿
- archive: 오래된 문서 보관

Notion은 요약/인덱스만 담당한다.

큰 코드 변경의 기준 순서:

```text
spec
-> ADR(if needed)
-> plan
-> failing tests
-> implementation
-> docs update
-> handoff update
-> python scripts/finish_task.py
-> optional Notion apply
```

행동이 바뀌는 코드 변경은 먼저 실패하는 테스트를 작성한다. 테스트를 먼저 작성하지 못하면 plan에 이유와 대체 검증 방법을 남긴다.

작업 종료 단일 명령은 handoff 갱신 후 마지막에 실행한다.

```bash
python scripts/finish_task.py
```

이 명령은 unittest, 전체 작업 트리 대상 docs freshness check, Notion handoff dry-run, `git status --short`, `git diff --stat`을 실행한다.

docs freshness check는 `docs/DOC_OWNERS.yml`을 읽는다. 새 schema는 `code_paths`, `ignored_paths`, `global_required_on_code_change`, `rules[].paths`, `contract_docs`, `procedure_docs`를 사용한다.

정책:

- 변경된 코드 파일은 matching rule이 있어야 한다.
- 매칭된 rule의 contract/procedure docs 중 하나 이상이 같은 작업 트리에서 변경되어야 한다.
- 코드 변경이 있으면 `docs/handoff/CURRENT_HANDOFF.md`도 변경되어야 한다.
- handoff는 전역 종료 조건이지만 경로별 contract docs를 대체하지 않는다.
- `docs/archive/**`, Notion 문서, 외부 링크는 owner로 인정하지 않는다.
- `docs/plans/**`는 장기 owner로 쓰지 않는다.

## Reviewed docs

기본 `finish_task.py` 검증은 이 섹션만으로 required docs를 충족시키지 않는다.

`check_docs_freshness.py --allow-reviewed-docs`를 명시적으로 사용할 때만 아래 목록이 보조 증거로 인정될 수 있다.

- `docs/WORKFLOW.md`
- `docs/runbooks/finish-task.md`
- `docs/runbooks/test.md`
- `docs/handoff/CURRENT_HANDOFF.md`

추가된 자동화:

- `scripts/check_docs_freshness.py`
- `scripts/sync_notion_handoff.py`
- `scripts/finish_task.py`
- `docs/DOC_OWNERS.yml`
- `.github/workflows/docs-freshness.yml`
- `.pre-commit-config.yaml`
- `.github/pull_request_template.md`

이번 workflow/tooling 변경의 관련 파일:

- `scripts/check_docs_freshness.py`
- `tests/test_check_docs_freshness.py`
- `docs/DOC_OWNERS.yml`
- `docs/WORKFLOW.md`
- `docs/README.md`
- `docs/runbooks/finish-task.md`
- `docs/runbooks/test.md`
- `docs/templates/SPEC_TEMPLATE.md`
- `docs/templates/PLAN_TEMPLATE.md`
- `docs/templates/HANDOFF_TEMPLATE.md`
- `CLAUDE.md`
- `.github/pull_request_template.md`

## 다음 agent가 먼저 읽을 문서

1. `docs/README.md`
2. `docs/WORKFLOW.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. `docs/DOC_OWNERS.yml`
5. `docs/runbooks/test.md`
6. `docs/runbooks/finish-task.md`
7. 변경 대상과 관련된 `docs/specs/`, `docs/runbooks/`, `docs/adrs/`

## 다음 구현 후보

1. manifest 기반 `--apply` 구현
2. 실제 Google Drive API 인증/조회 설계
3. Google Docs export/download 구현
4. Drive 변경 감지 후 wiki/FTS/graph 재빌드 연결
5. 검색 품질 평가
6. Discord/OpenClaw 연결
7. 패치노트 자동 수집

manifest 기반 `--apply`의 첫 구현 범위는 fixture content를 `raw/drive`에 저장하고, `sources.source_type = drive_document`로 DB upsert하며, 같은 manifest 반복 실행의 idempotent 동작을 unittest로 검증하는 것이다. 기존 dry-run 동작은 유지해야 한다.

실제 Drive API/OAuth/export-download는 그 이후 단계다.

embedding/vector DB는 필요성이 확인될 때까지 보류한다.

## 건드리지 말아야 할 것

명시 요청 없이는 다음을 건드리지 않는다.

- `tools/` 구현 코드
- `tests/` 코드
- `config/`
- `raw/`
- `wiki/`
- `graph/`
- `db/`
- `db/ffxiv.sqlite`
- Discord/OpenClaw 연결
- 실제 Google Drive API/OAuth
- embedding/vector DB
- 기존 사용자 변경

## 현재 주의사항

이번 session 시작 시점의 `git status --short`와 `git diff --stat`은 비어 있었다.

사용자 명시 없이 commit/push하지 않는다.

## 테스트 명령

```bash
python scripts/finish_task.py
```

특정 unittest만 실행해야 할 때:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

다음 agent는 작업 종료 전 `python scripts/finish_task.py`를 실행해야 한다.

이번 변경에서 먼저 확인한 명령:

```bash
python -m unittest tests.test_check_docs_freshness
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

`check_docs_freshness.py --all`은 handoff 갱신 전에는 `docs/handoff/CURRENT_HANDOFF.md` 누락으로 실패했다. 이 handoff 갱신 후 다시 실행해야 한다.
