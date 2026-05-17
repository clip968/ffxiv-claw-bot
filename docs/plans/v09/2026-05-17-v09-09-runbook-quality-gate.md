# v09-09: Runbook, Quality Gate, and Final Finish Workflow

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 09)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

In Progress

## Goal

v09 operating procedure를 runbook으로 문서화하고 final quality gate를 실행한다.

## Scope

- `docs/runbooks/guide-ff14-crawler.md`
- spec/status updates if needed
- handoff and final task report

Out of scope:

- new product behavior unless a docs/test failure reveals a small missed integration
- live network smoke without maintainer-approved crawl scope

## Red Test

No new product red test required if Tasks 01-08 already cover behavior. Docs freshness is the gate for stale docs.

## Checklist

- [ ] runbook 작성
- [ ] manual/network-approved smoke section 작성
- [ ] rollback/cleanup notes 작성
- [ ] all v09 focused tests 실행
- [ ] docs freshness 실행
- [ ] `scripts/finish_task.py` 실행
- [ ] handoff 갱신

## Verification

```bash
python -m unittest tests.test_guide_ff14_storage -v
python -m unittest tests.test_guide_ff14_category_map -v
python -m unittest tests.test_guide_ff14_fetcher -v
python -m unittest tests.test_guide_ff14_item_extractor -v
python -m unittest tests.test_guide_ff14_crawler -v
python -m unittest tests.test_guide_ff14_item_wiki -v
python -m unittest tests.test_guide_ff14_item_graph -v
python -m unittest tests.test_guide_ff14_item_retrieval -v
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

## Agent Prompt

```text
v09 Task 09를 수행한다. runbook을 작성하고 final v09 quality gate를 실행한다. live network smoke는 승인 없이는 실행하지 않는다.
```
