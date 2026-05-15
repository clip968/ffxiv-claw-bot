# v05-05: URL Integration

## Goal

`process_source.py`가 사용자가 제공한 단일 URL을 fetch하고, 결과를 Local Storage에 저장할 수 있도록 한다.

## Spec Reference

- [Sec 5] Supported Source Types (url)
- [Sec 10.2] URL Fetch
- [Sec 14.2] Fetch Error
- [Sec 16] URL Policy
- [Sec 20.1] Test Plan (url tests)

## Tasks

### 1. Create or reuse URL fetch helper

- [ ] `tools/fetch_url.py` 또는 기존 fetch 함수 확인
- [ ] URL fetch 함수 구현 (HTTP GET → status/content-type/content)
- [ ] content-type 기반 body 추출:
  - text/html → HTML title 추출 + main text 추출 (html2text 또는 regex)
  - text/plain → 그대로 사용
  - application/json → 그대로 사용
  - 기타 content-type → error

### 2. Title extraction

- [ ] HTML 문서에서 `<title>` 태그 추출
- [ ] `--title`이 CLI로 제공된 경우 제공된 title 우선
- [ ] title이 없으면 URL domain + path 기반 생성

### 3. URL → Local ingest 연결

- [ ] fetch 결과 body를 `ingest_local._do_ingest()`로 전달
- [ ] source_type은 `url`, category는 사용자 제공 category
- [ ] 저장 위치: `{storage_root}/sources/{category}/{url_slug}.md`
- [ ] fetch 실패 시 `status=error`, source_id=null

### 4. Tests

- [ ] `test_process_url_ok` — 목 fetch로 url 처리 성공 검증
- [ ] `test_process_url_fetch_fails_returns_error` — fetch 실패 시 error
- [ ] `test_fetch_url_unsupported_content_type` — 지원 않는 content-type 처리

## Red Test

`tests/test_v05_fetch_url.py`, `tests/test_v05_process_source.py`

## Completion

- 단일 URL fetch 구현
- fetch한 body를 Local Storage에 저장
- fetch 실패 시 error 반환
- URL policy 준수 (단일 URL만, 재귀/crawling 없음)
