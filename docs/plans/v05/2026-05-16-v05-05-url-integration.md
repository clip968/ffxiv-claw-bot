# v0.5-05 Plan: URL Integration

## Goal

process_source.py가 사용자가 직접 제공한 단일 URL을 fetch하고, 그 내용을 Local Storage ingest pipeline으로 연결하도록 구현한다.

이번 task가 끝나면 사용자는 URL 하나를 제공하는 것만으로 source 저장까지 수행할 수 있어야 한다.

## Background

기존 tools/ingest_url.py는 존재하지만, 현재 v0.4 운영 경로는 Local Storage 중심이다.

v0.5에서는 URL도 결국 Local Storage source로 들어와야 한다.

즉, URL 처리 결과는 다음 흐름을 타야 한다.

URL
-> fetch
-> title/body 추출
-> ingest_local.py의 url source로 저장
-> raw/local_storage snapshot 생성
-> sources DB 등록

이번 task에서는 URL fetch와 Local Storage ingest 연결까지만 확실히 한다.

rebuild 전체 연결은 v0.5-06에서 처리한다.

## Scope

이번 task에서 구현할 것:

1. URL fetch helper 구현
2. process_source.py --source-type url apply 처리
3. HTTP status code 처리
4. content-type 검증
5. HTML title 추출
6. text body 추출
7. fetch 실패 handling
8. URL source ingest 연결
9. URL 관련 tests 작성

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- 검색 엔진 사용
- recursive crawling
- sitemap crawling
- 사이트 전체 crawling
- scheduler
- Notion queue
- Cloudflare 우회
- paywall 우회
- 로그인 필요한 페이지 처리
- PDF 자동 파싱
- OCR

사용자가 직접 제공한 URL 하나만 fetch한다.

## Files to Add

tools/fetch_url.py
tests/test_v05_fetch_url.py

## Files to Update

tools/process_source.py
tests/test_v05_process_source.py
docs/runbooks/process-source.md
docs/handoff/CURRENT_HANDOFF.md

필요한 경우:

tools/ingest_url.py

단, ingest_url.py를 v0.5 기본 경로로 되살리는 것이 아니라, 필요한 로직을 재사용하거나 migrate한다.

## URL Policy

허용:

- http URL
- https URL
- text/html
- text/plain
- application/json은 선택적으로 text로 저장 가능
- 사용자가 직접 제공한 단일 URL

거부:

- ftp
- file
- javascript
- data
- mailto
- unsupported content type
- empty body
- login required page
- paywall 우회
- Cloudflare 우회
- recursive link discovery

## Fetch Helper Contract

tools/fetch_url.py는 다음 함수 중심으로 구현한다.

fetch_url_to_source(url: str, timeout: int = 20) -> dict

반환 성공 예시:

{
  "status": "ok",
  "url": "https://example.com",
  "final_url": "https://example.com",
  "title": "Example Domain",
  "content_type": "text/html",
  "body": "Example Domain\nThis domain is for use in illustrative examples...",
  "fetched_at": "2026-05-16T00:00:00+09:00"
}

반환 실패 예시:

{
  "status": "error",
  "url": "https://example.com/missing",
  "error": "HTTP 404",
  "next_action": "Provide a reachable URL."
}

## HTML Extraction

v0.5에서는 복잡한 readability parser가 필수는 아니다.

최소 구현:

- script 제거
- style 제거
- nav/footer 제거는 가능하면 수행
- title 태그 추출
- body text 추출
- 연속 공백 정리
- 너무 짧은 body는 error 처리

BeautifulSoup을 이미 의존하고 있으면 사용한다.

의존성이 없다면 Python standard library 기반 HTMLParser 또는 간단한 fallback을 사용한다.

## process_source.py URL Flow

source_type=url일 때 process_source.py는 다음 순서로 실행한다.

1. validate_request
2. fetch_url
3. fetch 결과 title/body 구성
4. ingest_local.py에 source_type=url로 전달
5. ingest 결과 source_id 수집
6. v0.5-06 전까지 rebuild는 pending 처리

명령 예시:

python tools/process_source.py --apply --source-type url --category patch_notes --url "https://example.com/ffxiv/patch-note"

title이 CLI에 주어지면 사용자가 준 title을 우선한다.

title이 없으면 fetch 결과 title을 사용한다.

fetch 결과 title도 없으면 URL host/path 기반으로 title을 생성한다.

## Error Handling

### Invalid URL

status=error
graph_status=skipped
Last Error=Invalid URL

### HTTP Error

status=error
graph_status=skipped
Last Error=HTTP status error

### Timeout

status=error
graph_status=skipped
Last Error=URL fetch timeout

### Unsupported Content Type

status=error
graph_status=skipped
Last Error=Unsupported content type

### Empty Body

status=error
graph_status=skipped
Last Error=Fetched content is empty

## Tests

tests/test_v05_fetch_url.py:

test_fetch_url_html_ok
test_fetch_url_plain_text_ok
test_fetch_url_http_error
test_fetch_url_timeout
test_fetch_url_unsupported_content_type
test_fetch_url_extracts_title
test_fetch_url_rejects_empty_body

tests/test_v05_process_source.py:

test_process_url_apply_creates_source
test_process_url_missing_url_returns_error
test_process_url_fetch_error_skips_ingest
test_process_url_uses_cli_title_when_provided
test_process_url_uses_fetched_title_when_title_missing
test_process_url_notion_payload_excludes_full_body

테스트 전략:

- 실제 외부 URL에 의존하지 않는다.
- fetch_url.py의 네트워크 호출은 mock한다.
- process_source.py URL 테스트는 fetch helper를 monkeypatch/mock한다.

## Runbook Update

docs/runbooks/process-source.md에 다음을 추가한다.

URL dry-run:

python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"

URL apply:

python tools/process_source.py --apply --source-type url --category patch_notes --url "https://example.com"

URL title override:

python tools/process_source.py --apply --source-type url --category patch_notes --title "Manual title" --url "https://example.com"

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- tools/fetch_url.py가 존재한다.
- source_type=url이 process_source.py에서 처리된다.
- URL fetch 성공 시 Local Storage ingest로 연결된다.
- title이 자동 추출된다.
- CLI title이 있으면 CLI title을 우선한다.
- fetch 실패 시 ingest를 수행하지 않는다.
- unsupported content type은 error로 처리한다.
- URL test가 실제 인터넷에 의존하지 않는다.
- v0.5에서 recursive crawling이 구현되지 않는다.

## Verification

다음 테스트를 실행한다.

python -m unittest discover -s tests -p "test_*.py"

수동 smoke test:

python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"

네트워크가 허용되는 환경에서만 apply smoke test를 수행한다.

python tools/process_source.py --apply --source-type url --category patch_notes --url "https://example.com"

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. URL 처리 방식
3. 새 CLI 사용 예시
4. 통과한 테스트
5. 남은 제한 사항