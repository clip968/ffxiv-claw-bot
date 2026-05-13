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

## Development Commands

- DB init: `python tools/init_db.py`
- URL ingest: `python tools/ingest_url.py <URL>`
- Git commit (Korean): `git add . && git commit -m "feat: 설명" && git push`
- Session log: `logs/YYYY-MM-DD.md`
