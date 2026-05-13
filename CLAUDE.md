# Agent Workflow

This project uses Superpowers-style skills through ForgeCode project skills.

Before starting any non-trivial coding task:

1. Check the available skills.
2. Prefer the relevant skill workflow instead of ad-hoc implementation.
3. For new features, use `brainstorming` before writing code.
4. After design approval, use `writing-plans` to create an implementation plan.
5. Keep plans under `docs/plans/` unless the user says otherwise.
6. Keep project documentation under `docs/`.
7. During implementation, prefer small, reviewable changes.
8. For bug fixes, use `systematic-debugging` before changing code.
9. For code changes, verify with the most relevant test, typecheck, lint, or build command.
10. Do not claim completion without verification.

## Project-specific constraints

- Project root: `/mnt/d/programming/ffxiv-claw-bot`
- Avoid broad refactors unless explicitly requested.
- Prefer small commits or small reviewable diffs.

## Before starting work

1. Check `CLAUDE.md` for workflow instructions.
2. Check the latest session log under `logs/` to pick up where you left off.
3. Review available skills (brainstorming, writing-plans, etc.) and prefer them over ad-hoc work.

## During work

- Briefly explain your intent before making code changes.
- Keep changes small and reviewable.

## After completing work

1. `git add . && git commit -m "prefix: message"`
2. `git push`
3. Write a session log entry to `logs/YYYY-MM-DD.md` using the format below.
4. Check the latest file in `logs/` to track progress.

### Session log entry format

```
### YYYY-MM-DD HH:MM — Title

#### Files changed
- `path/to/file` — added/modified/deleted

#### Reason
- Why the change was needed

#### Changes
- Specific details of what was changed (functions, classes, schema, logic, etc.)

#### Result
- Final state summary (execution output, table structure, example output, etc.)
```

### Git commit message rules

- Written in Korean (한국어).
- Prefix: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Example: `feat: ingest_url.py added — URL input → HTML save → DB record`

## Development Commands

- DB init: `python tools/init_db.py`
- URL ingest: `python tools/ingest_url.py <URL>`
- Wiki compile: `python tools/compile_wiki.py --source-id <id>`
- Search: `python tools/search_kb.py <query>`
- Answer (context pack): `python tools/answer.py <question>`
- Git commit: `git add . && git commit -m "feat: 설명" && git push`
- Session log: `logs/YYYY-MM-DD.md`

## Session Logs

All session records are stored in the `logs/` directory as date-stamped files.

- `logs/2026-05-14.md` — Initial project setup + session log refactor + compile_wiki + search_kb + answer
