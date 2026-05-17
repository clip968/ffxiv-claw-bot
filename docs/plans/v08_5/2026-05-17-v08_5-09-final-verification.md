# v0.8.5-09: Final Verification

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 9)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

## Goal

v08.5 완료 전 전체 regression과 smoke test를 수행한다.

## Scope

- 전체 pipeline smoke test
- full unittest 실행
- docs freshness 확인
- finish_task 실행
- CURRENT_HANDOFF.md 최종 기록

Out of scope:

- 새 코드 수정
- 새 테스트 추가 (v08_5-07 책임)

## Red Test

이 task는 검증 전용이므로 별도 red test가 필요하지 않다.

## Checklist

- [ ] pipeline smoke test
  - [ ] `python tools/rebuild_domain_graph.py --dry-run --verbose`
  - [ ] `python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph`
  - [ ] `python tools/generate_derived_wiki.py --dry-run --verbose`
- [ ] ask smoke query
  - [ ] `python tools/ask.py "건브 7.5 변경점 알려줘" --format json`
  - [ ] `python tools/ask.py "No Mercy 관련 변경 있어?" --format json`
  - [ ] `python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json`
  - [ ] `python tools/ask.py "건브 관련 source 보여줘" --format json`
  - [ ] 각 결과 확인: status=ok, contexts 비어 있지 않음, source dump 아님
- [ ] 실제 graph count 확인
- [ ] full unittest 실행
  - [ ] `python -m unittest discover -s tests -p "test_*.py"`
- [ ] docs freshness 확인
  - [ ] `python scripts/check_docs_freshness.py --all`
- [ ] finish_task 실행
  - [ ] `python scripts/finish_task.py`
- [ ] CURRENT_HANDOFF.md 최종 기록
  - [ ] Current phase: v08.5 Managed Wiki Knowledge Base Activation completed
  - [ ] Last completed task: final regression / handoff update
  - [ ] Next task: wait for maintainer scope, then consider v09 namespace expansion
  - [ ] 검증 명령과 결과
  - [ ] 아직 하지 말 것
- [ ] handoff/README feature map status 갱신

## Verification

필수 명령:

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

추가 확인:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('db/ffxiv.sqlite')
print('node types')
for row in conn.execute('SELECT type, COUNT(*) FROM graph_nodes GROUP BY type ORDER BY type'):
    print(row)
print('edge types')
for row in conn.execute('SELECT type, COUNT(*) FROM graph_edges GROUP BY type ORDER BY type'):
    print(row)
print('wiki types')
for row in conn.execute('SELECT wiki_type, COUNT(*) FROM wiki_pages GROUP BY wiki_type ORDER BY wiki_type'):
    print(row)
conn.close()
PY
```

## Key Decisions

- full unittest 통과, docs freshness 통과, finish_task 통과가 모두 필요하다.
- ask answer가 source dump가 아니라 구조화 요약인지 최종 확인한다.
- CURRENT_HANDOFF.md에 실행 명령과 결과를 기록한다.

## Implementation Notes

- 이 task는 코드를 수정하지 않는다.
- 모든 이전 task가 완료된 상태에서 실행한다.
- 실패가 있으면 해당 task로 돌아가 수정한다.

## Agent Prompt

```text
v08.5 Task 9를 수행한다.
전체 pipeline smoke test, ask smoke query, full regression, docs freshness, finish_task를 실행한다.
모든 것이 통과하면 CURRENT_HANDOFF.md를 최종 갱신한다.
실패가 있으면 해당 task로 돌아가 수정한다.
```
