# v0.8.5-01: Source Summary Audit

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 1)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

## Goal

`wiki/source_summaries/`가 실제 domain graph rebuild 입력으로 사용 가능한 상태인지 확인하고 결과를 문서화한다.

## Scope

- `wiki/source_summaries/*.md` 파일 개수 확인
- 각 파일의 source id, title, category, body 존재 여부 확인
- 비-FFXIV 데이터 잔존 여부 확인
- 빈 또는 짧은 source summary 확인
- 중복 source 확인
- audit 결과 문서화

Out of scope:

- source summary 내용 수정
- 새 source summary 추가
- graph rebuild (v08_5-02 책임)

## Red Test

이 task는 audit/문서화 전용이므로 별도 red test가 필요하지 않다. 필요 시 helper script `tools/audit_source_summaries.py`를 추가할 수 있다.

## Checklist

- [ ] `wiki/source_summaries/*.md` 파일 수 확인
- [ ] 각 source summary 점검
  - [ ] 파일명
  - [ ] source id 존재 여부
  - [ ] title 존재 여부
  - [ ] body length
  - [ ] FFXIV 관련성
  - [ ] 비-FFXIV 오염 데이터 여부
  - [ ] 빈 summary 여부
  - [ ] 중복 source 가능성
  - [ ] Job/Patch/Skill alias 포함 가능성
- [ ] SQLite 현재 상태 확인
  - [ ] `sources` table count
  - [ ] `wiki_pages` table count
  - [ ] `graph_nodes` table count
  - [ ] `graph_edges` table count
- [ ] audit 문서 작성: `docs/reports/2026-05-17-v08_5-source-audit.md`
  - [ ] Summary 섹션
  - [ ] Method 섹션
  - [ ] Findings 테이블
  - [ ] Exclusions or Fixes Needed 섹션
  - [ ] Decision 섹션
- [ ] graph rebuild 진행 가능 여부 결정
- [ ] handoff/README feature map status 갱신

## Verification

```bash
find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | wc -l
find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | head -20
```

SQLite 상태 확인:

```bash
python - <<'PY'
import sqlite3
from pathlib import Path
db = Path('db/ffxiv.sqlite')
if not db.exists():
    print('db_missing')
    raise SystemExit(0)
conn = sqlite3.connect(db)
for table in ['sources', 'wiki_pages', 'graph_nodes', 'graph_edges']:
    try:
        n = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(table, n)
    except sqlite3.Error as exc:
        print(table, 'error', exc)
conn.close()
PY
```

## Key Decisions

- audit 결과에 따라 graph rebuild 진행 여부를 결정한다.
- 비-FFXIV 오염 데이터가 남아 있으면 제외 후보로 기록한다.
- helper script 추가가 과하면 문서와 임시 one-liner로 충분하다.

## Implementation Notes

- `docs/reports/2026-05-17-v08_5-source-audit.md`에 audit 결과를 기록한다.
- audit 문서 템플릿은 implementation plan의 Task 1 참조.
- source summary가 사용 불가능하면 v08_5-02로 넘어가지 않는다.

## Agent Prompt

```text
v08.5 Task 1을 수행한다.
wiki/source_summaries/ 파일을 audit하고 결과를 docs/reports/2026-05-17-v08_5-source-audit.md에 기록한다.
각 파일의 source id, title, body, FFXIV 관련성을 확인한다.
graph rebuild 가능 여부를 결정한다.
```
