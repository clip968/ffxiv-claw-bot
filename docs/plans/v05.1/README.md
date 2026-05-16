# v05.1 Feature Plans

v05.1 Source Processing Hardening의 feature별 plan을 보관한다.

v05.1의 목표는 v0.5 Source Processing Pipeline을 실제 Lodestone 7.5 패치노트 저장 과정에서 드러난 문제 기준으로 안정화하는 것이다. 새 automation layer를 만들지 않고, 기존 공식 entrypoint인 `tools/process_source.py`를 더 신뢰할 수 있게 만든다.

기본 운영 경로는 v0.5와 동일하다.

```text
사용자 source 제공
-> OpenClaw Source Processing Skill
-> tools/process_source.py
-> fetch 또는 local file read
-> Local Storage ingest
-> wiki/FTS/graph rebuild
-> notion_update payload 생성
-> OpenClaw 또는 Notion adapter가 payload 적용
```

`process_source.py`는 Notion API를 직접 호출하지 않는다. `notion_update` payload를 생성할 뿐이며, 실제 Notion DB write는 OpenClaw 또는 별도 control layer의 책임이다.

## Master Plan

원본 구현 계획은 `docs/plans/2026-05-16-v05.1_implementation_plan.md`에 있다.

구현 계약은 `docs/specs/0004a-v05.1-source-processing-hardening.md`를 따른다.

부모 v0.5 계약은 `docs/specs/0004-v05-source-processing-pipeline.md`와 `docs/plans/v05/README.md`를 따른다.

## Active Feature Map

| # | Plan | Purpose | Status |
|---|---|---|---|
| 01 | 2026-05-16-v05.1-01-spec-and-plan.md | v05.1 scope, spec, task breakdown 고정 | **Completed** 2026-05-16 |
| 02 | 2026-05-16-v05.1-02-lodestone-fixture-and-red-tests.md | Lodestone fixture와 extractor red test 작성 | **Completed** 2026-05-16 |
| 03 | 2026-05-16-v05.1-03-lodestone-extractor.md | Lodestone 전용 article extractor 구현 | **Completed** 2026-05-16 |
| 04 | 2026-05-16-v05.1-04-fetch-url-routing.md | `fetch_url.py`에서 Lodestone URL을 전용 extractor로 라우팅 | **Completed** 2026-05-16 |
| 05 | 2026-05-16-v05.1-05-process-source-extractor-metadata.md | `process_source.py` action log에 extractor metadata 포함 | **Completed** 2026-05-16 |
| 06 | 2026-05-16-v05.1-06-entrypoint-boundary-docs.md | 공식 entrypoint와 helper boundary를 문서화 | **Completed** 2026-05-16 |
| 07 | 2026-05-16-v05.1-07-runbook-regression-tests.md | helper misuse/Notion boundary 문서 회귀 테스트 추가 | **Completed** 2026-05-16 |
| 08 | 2026-05-16-v05.1-08-final-verification-and-handoff.md | 전체 검증, docs freshness, handoff 마무리 | **Completed** 2026-05-16 |

## Red Test Map

| Plan | Red test | Implementation target |
|---|---|---|
| 02 | `tests/test_v05_1_lodestone_extractor.py` | `tools/extractors/lodestone.py`, `tests/fixtures/lodestone_patch_7_5.html` |
| 03 | `tests/test_v05_1_lodestone_extractor.py` | `tools/extractors/__init__.py`, `tools/extractors/lodestone.py` |
| 04 | `tests/test_v05_fetch_url.py` or `tests/test_v05_1_fetch_url_routing.py` | `tools/fetch_url.py` |
| 05 | `tests/test_v05_process_source.py` | `tools/process_source.py` |
| 06 | documentation-only; no red test required | `docs/runbooks/process-source.md`, `docs/runbooks/test.md`, `docs/handoff/CURRENT_HANDOFF.md` |
| 07 | `tests/test_v05_process_source.py` or docs-specific unittest file | `docs/runbooks/process-source.md` |
| 08 | all v05.1 and existing v0.5 tests | handoff, docs freshness, final verification |

## v05.1 Scope

v05.1에서 구현하는 것:

- Lodestone URL/domain detection
- Lodestone `.news__detail__wrapper` article extraction
- Lodestone title/body/extractor metadata 반환
- Lodestone extraction error handling
- `fetch_single_url()` extractor metadata
- `process_source.py` `fetch_url` action extractor metadata
- non-Lodestone HTML, text/plain, JSON URL behavior regression protection
- official entrypoint boundary documentation
- `ingest_local.py --body <file path>` misuse warning
- `local_rebuild.py` library-only boundary documentation
- `status_notification.py` payload-builder-only boundary documentation
- `notion_update` is payload-only, not already-applied Notion DB state
- v05.1 validation commands and handoff

## v05.1 Non-Goals

v05.1에서는 다음을 구현하지 않는다.

- Notion polling
- scheduler 또는 daemon
- Discord slash command runtime
- crawler
- sitemap traversal
- 검색 엔진 기반 최신 패치노트 탐색
- 여러 URL 자동 순회
- 로그인 필요한 페이지 처리
- Cloudflare 우회
- paywall 우회
- PDF parsing
- OCR
- embedding pipeline
- vector DB
- LLM 기반 요약 품질 개선
- graph schema 확장
- `process_source.py` 내부 Notion API 직접 호출

## Source Type Policy

v05.1은 v0.5 source type을 확장하지 않는다.

| Source Type | v05 status | v05.1 hardening |
|---|---|---|
| text_note | Supported | regression only |
| markdown_file | Supported | official `process_source.py --local-path` boundary documentation |
| plain_text_file | Supported | regression only |
| url | Supported | Lodestone-specific extraction and extractor metadata |
| binary_attachment | Contract only / limited | no new implementation |

## Entrypoint Policy

Allowed normal source processing commands:

```bash
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "..." --body "..."
python tools/process_source.py --apply --source-type markdown_file --category patch_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/patch.md"
python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/note.txt"
python tools/process_source.py --apply --source-type url --category patch_notes --url "https://na.finalfantasyxiv.com/lodestone/..."
```

Disallowed for normal OpenClaw source processing:

```bash
python tools/ingest_local.py --source-type markdown_file --body "/path/to/file.md"
python tools/local_rebuild.py
python tools/status_notification.py
```

Manual debugging may inspect or test helper modules, but committed workflow docs must keep `tools/process_source.py` as the official user/OpenClaw entrypoint.

## Verification

Each implementation task should run its focused tests first.

Focused v05.1 tests:

```bash
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

Existing v0.5 focused tests:

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Docs freshness:

```bash
python scripts/check_docs_freshness.py --all
```

Whitespace:

```bash
git diff --check
```

Final gate:

```bash
python scripts/finish_task.py
```

## Writing Rules

- 각 plan은 spec의 한 기능 단위에 대응한다.
- Tasks는 체크리스트 형식으로 작성한다.
- 완료 시 Status를 `Completed YYYY-MM-DD`로 변경하고 이 README의 feature map도 함께 갱신한다.
- 코드 변경 task는 handoff 외에도 관련 spec/runbook/ADR 중 하나 이상을 갱신해야 한다.
- 행동 변경은 먼저 red test를 작성한다.
- 테스트 명령은 repo 표준인 `python -m unittest ...`를 사용한다.
- `pytest`를 새 표준으로 도입하지 않는다.
- Google Drive를 기본 경로로 되살리지 않는다.
- Notion을 원본 파일 저장소로 사용하지 않는다.
- `process_source.py`에서 Notion API를 직접 호출하지 않는다.
- crawler/scheduler/daemon은 v05.1에 넣지 않는다.
