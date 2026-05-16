# CURRENT_HANDOFF

이 문서는 다음 agent/session이 가장 먼저 읽는 현재 상태 대시보드다. 과거 상세 로그는 `docs/handoff/history/`에 보관한다.

## 현재 상태

- Repository: `https://github.com/clip968/ffxiv-claw-bot`
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Branch: `main`
- Last pushed commit: `d1cd69a` (`what: v07-04 intent detector 추가`)
- Current phase: v0.7 Grounded Ask Pipeline 진행 중
- Last completed task: v07-04 intent detector
- Next task: v07-05 query parser integration
- Current maintenance task: GitHub Actions dependency install fix for `bs4`

## 먼저 읽을 문서

1. `docs/WORKFLOW.md`
2. `docs/specs/0007-v07-grounded-ask-pipeline.md`
3. `docs/plans/v07/README.md`
4. `docs/plans/v07/2026-05-17-v07-05-query-parser-integration.md`
5. `docs/runbooks/process-source.md`
6. `docs/runbooks/generate-derived-wiki.md`

필요할 때만 과거 상세 로그를 읽는다.

- `docs/handoff/history/2026-05-17-current-handoff.md`

## v07 진행 상황

완료:

- v07-01: `ParsedQuery`, `normalize_query()`, `extract_terms()`
- v07-02: `detect_job()` job detector
- v07-03: `parse_patch_range()` numeric patch range parser
- v07-04: `detect_intent()` deterministic intent detector

다음 작업:

- v07-05: `parse_query()`에서 normalization, job detection, patch parsing, intent detection을 통합한다.

아직 하지 말 것:

- crawling
- polling/scheduler
- Discord slash command
- LLM API 호출
- vector/embedding search
- raid/item/system derived wiki generation

## 현재 검증 스냅샷

CI dependency fix 확인:

```bash
/tmp/ffxiv-claw-bot-ci-repro/bin/python -m unittest tests.test_v06_extractors.V06TextMarkdownHtmlExtractorTests -v
/tmp/ffxiv-claw-bot-ci-repro/bin/python -m unittest discover -s tests -p "test_*.py"
```

수정 전 결과:

- clean venv에서 `ModuleNotFoundError: No module named 'bs4'` 재현
- 원인: `requirements.txt` 부재 및 GitHub Actions dependency install step 부재

수정 후 결과:

- clean venv에서 `python -m pip install -r requirements.txt` 성공
- clean venv에서 `python -m unittest discover -s tests -p "test_*.py"` 238 tests OK

v07-04 완료 시점 검증:

```bash
python -m unittest tests.test_v07_query_parser -v
python -m py_compile src/query/intent_detector.py src/query/__init__.py
python scripts/finish_task.py
```

결과:

- `tests.test_v07_query_parser`: 17 tests OK
- `py_compile`: OK
- `finish_task.py`: 238 tests OK, docs freshness OK, Notion handoff dry-run OK

## 현재 작업트리 주의사항

다음 변경은 v07-01~04 구현 범위 밖의 기존 변경으로 남아 있다. 임의로 되돌리지 말 것.

```text
M .gitignore
M AGENTS.md
```

이번 handoff 정리 작업으로 예상되는 변경:

```text
docs/handoff/CURRENT_HANDOFF.md
docs/handoff/README.md
docs/handoff/history/2026-05-17-current-handoff.md
```

## 운영 원칙

- `docs/`가 source of truth다. Notion은 mirror/index/control layer일 뿐이다.
- `CURRENT_HANDOFF.md`에는 현재 상태만 남긴다.
- 완료된 상세 작업 로그는 `docs/handoff/history/` 또는 각 task plan에 남긴다.
- 코드 변경이 있으면 관련 spec/runbook/plan과 handoff를 함께 갱신한다.
- 기존 사용자 변경을 임의로 revert하지 않는다.

## 다음 agent에게

v07을 계속한다면 v07-05부터 시작한다. 먼저 v07-05 plan을 읽고, red test를 작성한 뒤 구현한다. 작업 범위가 handoff 구조 자체라면 `docs/handoff/README.md`의 규칙을 우선 따른다.
