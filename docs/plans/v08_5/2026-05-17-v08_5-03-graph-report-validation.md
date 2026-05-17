# v0.8.5-03: Graph Report Validation

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 3)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

## Goal

생성된 graph가 의미 있는지 `GRAPH_REPORT.md`로 검증한다.

## Scope

- `GRAPH_REPORT.md` 생성
- node type count 확인
- edge type count 확인
- top mentioned entities 확인
- quality warnings 확인 및 문서화

Out of scope:

- graph rebuild (v08_5-02 책임)
- derived wiki 생성 (v08_5-04 책임)
- graph report generator 코드 대폭 수정

## Red Test

기존 `tests/test_graph_report.py`가 충분하면 새 테스트는 생략 가능. v08.5 기준을 고정하려면:

- File: `tests/test_v08_5_graph_report_quality.py` (optional)
- Implementation target: graph report quality assertions

Contracts (optional):

- report에 `Job`, `Patch`, `Skill`, `Fact` count가 표시된다.
- report에 `Quality Warnings` 섹션이 있다.
- report 생성 결과가 deterministic하다.

## Checklist

- [ ] graph report 생성
  - [ ] `python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph`
- [ ] `graph/GRAPH_REPORT.md` 확인
  - [ ] Summary 존재
  - [ ] total nodes
  - [ ] total edges
  - [ ] node type counts
  - [ ] edge type counts
  - [ ] top mentioned jobs 또는 top mentioned entities
  - [ ] quality warnings
- [ ] Job/Patch/Skill/Fact count가 모두 0이 아닌지 확인
- [ ] warning 원인 및 처리 여부 문서화
- [ ] 필요 시 `docs/reports/2026-05-17-v08_5-graph-report-review.md` 작성
- [ ] graph가 비어 있으면 다음 task로 넘어가지 않음
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

기존 테스트:

```bash
python -m unittest tests.test_graph_report -v
```

## Key Decisions

- `GRAPH_REPORT.md`의 Job/Patch/Skill/Fact count가 모두 0이 아닌 경우에만 v08_5-04로 진행한다.
- warning이 있으면 무시하지 않고 원인과 처리 방침을 기록한다.

## Implementation Notes

- `tools/generate_graph_report.py`는 v08-07에서 이미 구현되어 있다.
- 이 task에서는 report를 생성하고 내용을 검증하는 것이 주 작업이다.
- graph가 비어 있으면 v08_5-02로 돌아가 원인을 점검한다.

## Agent Prompt

```text
v08.5 Task 3을 수행한다.
tools/generate_graph_report.py로 GRAPH_REPORT.md를 생성한다.
report에서 node type count, edge type count, top entities, quality warnings를 확인한다.
Job/Patch/Skill/Fact가 모두 0이 아닌지 검증한다.
warning이 있으면 원인을 문서화한다.
```
