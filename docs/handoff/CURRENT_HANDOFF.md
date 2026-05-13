# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`
- Current phase: v0.3 완료

## 현재 상태

완료된 것:

- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 Google Drive sync dry-run
- docs 기반 workflow 정리

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

## 다음 agent가 먼저 읽을 문서

1. `docs/README.md`
2. `docs/WORKFLOW.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. `docs/specs/0003-google-drive-sync.md`
5. `docs/plans/2026-05-14-post-v03-next-steps.md`
6. `docs/runbooks/test.md`
7. `docs/runbooks/sync-drive.md`

## 다음 구현 후보

1. 실제 Google Drive API 인증/조회 설계
2. Google Docs export/download 구현
3. Drive 변경 감지 후 wiki/FTS/graph 재빌드 연결
4. 검색 품질 평가
5. Discord/OpenClaw 연결
6. 패치노트 자동 수집

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
python -m unittest discover -s tests -p "test_*.py"
```

특정 Drive sync 테스트:

```bash
python -m unittest tests.test_sync_drive
```
