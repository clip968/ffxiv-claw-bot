# Agent Workflow

This repository uses a docs-first workflow. The source of truth is the Markdown documentation under `docs/`; Notion is only a mirror/index for summaries and links.

## Required Start Order

Before starting non-trivial work:

1. First read `docs/WORKFLOW.md`.
2. Then read `docs/handoff/CURRENT_HANDOFF.md`.
3. Check the relevant spec, runbook, ADR, or plan for the files you will touch.
4. Check the working tree before editing:

```bash
git status --short
git branch --show-current
git log --oneline -5
git diff --stat
```

Do not revert existing user changes unless the maintainer explicitly asks.

## Implementation Rules

1. For non-trivial behavior changes, confirm or create a spec before implementation.
2. Create an ADR only when the change records a lasting technical decision.
3. Keep implementation plans under `docs/plans/`; plans do not replace specs or runbooks.
4. Write failing tests before implementation.
5. If a red test cannot be written first, record the reason and alternate verification in the plan.
6. Keep changes small and reviewable.
7. Update relevant specs/runbooks/ADRs before handoff.
8. Update `docs/handoff/CURRENT_HANDOFF.md` before running `finish_task`.
9. Run `python scripts/finish_task.py` as the final verification gate.
10. Do not commit or push unless explicitly requested by the maintainer.

## Project Constraints

- Project root: `/mnt/d/programming/ffxiv-claw-bot`
- Avoid broad refactors unless explicitly requested.
- Prefer the repository's existing unittest-based test style.
- Do not introduce pytest unless a spec/plan explicitly adds that dependency and workflow.
- Do not treat Notion pages, external links, `docs/plans/`, or `docs/archive/` as DOC_OWNERS contract owners.

## Development Commands

- DB init: `python tools/init_db.py`
- URL ingest: `python tools/ingest_url.py <URL>`
- Wiki compile: `python tools/compile_wiki.py --source-id <id>`
- Search: `python tools/search_kb.py <query>`
- Answer: `python tools/answer.py <question>`
- Build graph: `python tools/build_graph.py`
- Graph query: `python tools/graph_path.py --source <node_id>`
- Drive sync dry-run: `python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json`
- Test: `python -m unittest discover -s tests -p "test_*.py"`
- Finish task: `python scripts/finish_task.py`

## Git

Only commit or push when the maintainer explicitly asks. If requested, first report the intended files, validation result, and commit message.
