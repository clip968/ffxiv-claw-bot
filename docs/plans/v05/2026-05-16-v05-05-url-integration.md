# v0.5-05: URL Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: Supported Source Types (`url`), URL Fetch, Fetch Error, URL Policy

## Status

**Completed** 2026-05-16

## Goal

Connect a user-provided single URL to the v0.5 source pipeline:

```text
provided URL -> fetch text content -> Local Storage ingest -> JSON result
```

## Scope

- Implement a URL fetch helper.
- Fetch exactly one user-provided URL.
- Support `text/html`, `text/plain`, `application/json`, and `+json` content.
- Extract HTML title and visible text for HTML pages.
- Preserve plain text and JSON bodies as text.
- Prefer CLI `--title` over fetched title.
- Use URL domain + path as fallback title.
- Connect fetched body to Local Storage through `tools.ingest_local.ingest_source()`.
- Return `status=error`, `source_id=null`, and skipped ingest/rebuild on fetch failure.

Out of scope:

- Crawlers
- Recursive crawling
- Sitemap parsing
- Scheduler or daemon behavior
- Search engine usage
- Auth-required URLs
- Rebuild integration, owned by v05-06
- Notion success payload generation, owned by v05-07

## Red Tests

- File: `tests/test_v05_fetch_url.py`, `tests/test_v05_process_source.py`
- Implementation target: `tools/fetch_url.py`, `tools/process_source.py`
- Initial red reason: `tools.fetch_url` did not exist and `process_source.py` did not connect `source_type=url` apply mode.

Contracts fixed by the tests:

- URL fetch succeeds with mocked HTTP GET and extracts title/body.
- Unsupported content type raises `UrlFetchError`.
- HTTP/status errors raise `UrlFetchError`.
- `process_source.py --apply --source-type url` calls a mocked `fetch_single_url()` exactly once for the provided URL.
- URL fetch success creates a Local Storage source and raw snapshot.
- URL fetch failure does not write Local Storage files or DB rows.
- CLI `--title` overrides the fetched title.

## Checklist

- [x] Add `tools/fetch_url.py`.
- [x] Implement `fetch_single_url()`.
- [x] Add `UrlFetchError`.
- [x] Support `text/html`.
- [x] Support `text/plain`.
- [x] Support `application/json` and `+json`.
- [x] Reject unsupported content types.
- [x] Extract HTML `<title>`.
- [x] Extract visible HTML body text.
- [x] Use URL domain + path fallback title.
- [x] Prefer process_source CLI `--title`.
- [x] Connect URL fetch result to `ingest_local.ingest_source(source_type="url", ...)`.
- [x] Preserve `source_type=url` in process_source output.
- [x] Skip rebuild with `reason=v05-06_not_implemented`.
- [x] Add mocked URL fetch unit tests.
- [x] Add mocked process_source URL integration tests.
- [x] Avoid crawler, scheduler, search engine, sitemap, or recursive behavior.

## Implementation Notes

- `tools/fetch_url.py` uses `requests` when available.
- If `requests` is unavailable, it falls back to stdlib `urllib` so this repo still works without a dependency file.
- `fetch_single_url()` returns a dict with `url`, `content_type`, `title`, and `body`.
- HTML body extraction reuses `tools.html_utils.extract_text_from_html()`.
- `tools/process_source.py` catches fetch errors before Local Storage ingest.
- URL ingest still delegates storage path, source ID, raw snapshot, DB upsert, and content hash behavior to `tools.ingest_local.ingest_source()`.
- v05-05 intentionally leaves wiki/FTS/graph rebuild skipped.

## Verification

Commands:

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
python -m py_compile tools/fetch_url.py tools/process_source.py
python -m unittest discover -s tests -p "test_*.py"
```

Results:

- `python -m unittest tests.test_v05_fetch_url -v`: **4 tests, OK**.
- `python -m unittest tests.test_v05_process_source -v`: **15 tests, OK**.
- `python -m py_compile tools/fetch_url.py tools/process_source.py`: **OK**.
- `python -m unittest discover -s tests -p "test_*.py"`: **117 tests, OK**.

## Key Decisions

- Only a single user-provided URL is fetched.
- URL fetch is isolated in `tools/fetch_url.py` for focused tests.
- `process_source.py` remains the v0.5 execution entrypoint.
- Existing Local Storage ingest remains the source of truth for canonical paths and DB writes.
- HTTP/network/content-type failures are fetch failures and stop the pipeline before ingest.
