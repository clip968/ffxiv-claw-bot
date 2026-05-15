# v0.5-05: URL Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 5] Supported Source Types (url), [Sec 10.2] URL Fetch, [Sec 14.2] Fetch Error, [Sec 16] URL Policy

## Status

**Pending**

## Goal

`process_source.py`가 사용자가 제공한 단일 URL을 fetch하고, 결과를 Local Storage에 저장할 수 있도록 한다.

## Scope

- URL fetch helper 구현 (HTTP GET → status/content-type/content)
- content-type 기반 body 추출:
  - text/html → HTML title 추출 + main text 추출 (html2text 또는 regex)
  - text/plain → 그대로 사용
  - application/json → 그대로 사용
  - 기타 content-type → error
- Title extraction: HTML `<title>` 태그 → `--title` CLI override → URL domain+path fallback
- URL → Local ingest 연결
- 저장 위치: `{storage_root}/sources/{category}/{url_slug}.md`
- fetch 실패 시 `status=error`, source_id=null

Out of scope:

- 재귀 URL fetch
- sitemap parsing
- 크롤링
- 인증이 필요한 URL

## Red Test

- File: `tests/test_v05_fetch_url.py`, `tests/test_v05_process_source.py`
- Implementation target: `tools/fetch_url.py`, `tools/process_source.py`
- Current red reason: fetch_url module does not exist, process_source.py URL path not connected.
- Contract fixed by the test:
  - Mock HTTP GET으로 URL fetch 성공 시 source_id 반환.
  - Mock fetch 실패 시 error JSON 반환.
  - 지원하지 않는 content-type 처리.

## Checklist

- [ ] `tools/fetch_url.py` 또는 기존 fetch 함수 확인
- [ ] URL fetch 함수 구현 (HTTP GET → status/content-type/content)
- [ ] text/html → HTML title 추출 + main text 추출 (html2text 또는 regex)
- [ ] text/plain → 그대로 사용
- [ ] application/json → 그대로 사용
- [ ] 기타 content-type → error
- [ ] HTML 문서에서 `<title>` 태그 추출
- [ ] `--title`이 CLI로 제공된 경우 제공된 title 우선
- [ ] title이 없으면 URL domain + path 기반 생성
- [ ] fetch 결과 body를 `ingest_local._do_ingest()`로 전달
- [ ] source_type은 `url`, category는 사용자 제공 category
- [ ] 저장 위치: `{storage_root}/sources/{category}/{url_slug}.md`
- [ ] fetch 실패 시 `status=error`, source_id=null
- [ ] `test_process_url_ok` — 목 fetch로 url 처리 성공 검증
- [ ] `test_process_url_fetch_fails_returns_error` — fetch 실패 시 error
- [ ] `test_fetch_url_unsupported_content_type` — 지원 않는 content-type 처리

## Verification

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com/ffxiv/patch"
```

## Key Decisions

- 단일 URL만 fetch한다. 재귀/crawling은 v0.5 non-goal.
- fetch helper는 모듈 분리하여 `process_source.py` 외부에서도 재사용 가능하게 한다.
- HTTP 오류(4xx, 5xx)는 fetch 실패로 처리하고 error JSON을 반환한다.
