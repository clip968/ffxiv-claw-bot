# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`
- Current phase: v0.3 Google Drive sync dry-run 완료

## 현재 상태

완료된 것:

- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run 완료
- docs 기반 workflow 정리
- 작업 종료 자동화 workflow

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

구현 기준은 Notion이 아니라 레포 내부 Markdown 문서다.

- specs: 현재 시스템 동작 계약
- adrs: 기술적 결정 이유
- plans: 구현 전 작업 분해
- runbooks: 반복 실행 절차
- handoff: 다음 session 인계
- templates: 문서 작성 템플릿
- archive: 오래된 문서 보관

Notion은 요약/인덱스만 담당한다.

작업 종료 단일 명령:

```bash
python scripts/finish_task.py
```

이 명령은 unittest, 전체 작업 트리 대상 docs freshness check, Notion handoff dry-run, `git status --short`, `git diff --stat`을 실행한다.

docs freshness check는 `docs/DOC_OWNERS.yml`을 읽는다. 매핑된 코드 파일이 바뀌면 해당 required docs 중 최소 하나가 변경되어야 한다. 이 검사는 문서 읽기 자체가 아니라 문서 반영 산출물을 검증한다.

## Reviewed docs

기본 `finish_task.py` 검증은 이 섹션만으로 required docs를 충족시키지 않는다.

`check_docs_freshness.py --allow-reviewed-docs`를 명시적으로 사용할 때만 아래 목록이 보조 증거로 인정될 수 있다.

- `docs/WORKFLOW.md`
- `docs/runbooks/finish-task.md`
- `docs/handoff/CURRENT_HANDOFF.md`

추가된 자동화:

- `scripts/check_docs_freshness.py`
- `scripts/sync_notion_handoff.py`
- `scripts/finish_task.py`
- `docs/DOC_OWNERS.yml`
- `.github/workflows/docs-freshness.yml`
- `.pre-commit-config.yaml`
- `.github/pull_request_template.md`

## 다음 agent가 먼저 읽을 문서

1. `docs/README.md`
2. `docs/WORKFLOW.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. `docs/specs/0003-google-drive-sync.md`
5. `docs/plans/2026-05-14-post-v03-next-steps.md`
6. `docs/runbooks/test.md`
7. `docs/runbooks/sync-drive.md`
8. `docs/runbooks/finish-task.md`
9. `docs/runbooks/notion-sync.md`

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

이 handoff 작성 시점에 로컬에는 docs 작업과 무관한 기존 변경이 있었다.

- `CLAUDE.md` 수정
- `db/ffxiv.sqlite` 수정
- `docs/plans/2026-05-14-graph-layer.md` 삭제
- `.gitignore` 미추적

다음 agent는 이 변경을 임의로 되돌리지 않는다.

## 테스트 명령

```bash
python scripts/finish_task.py
```

특정 unittest만 실행해야 할 때:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

다음 agent는 작업 종료 전 `python scripts/finish_task.py`를 실행해야 한다.
