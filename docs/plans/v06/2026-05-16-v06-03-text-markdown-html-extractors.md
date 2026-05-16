# v0.6-03: TXT, Markdown, HTML Extractors

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-3)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Pending

## Goal

기본 문서형 파일(`.txt`, `.md`, `.html`/`.htm`)을 normalized text로 변환하는 extractor 3종을 구현한다.

## Scope

TXT:

- UTF-8 우선 디코딩
- 디코딩 실패 시 `SourceDecodingError`
- 원문 텍스트를 그대로 반환

Markdown:

- heading 구조 보존
- frontmatter가 있으면 metadata로 분리하거나 본문과 함께 유지
- 복잡한 markdown AST 처리는 하지 않음 (raw 또는 가벼운 normalize)

HTML:

- BeautifulSoup 또는 기존 의존성으로 파싱
- `script`, `style`, `nav`, `footer` 제거
- title 추출 (`<title>` 또는 첫 heading)
- 본문 텍스트를 heading/paragraph 중심으로 normalize
- 불필요한 공백 collapse
- metadata에 `html_title`, `removed_elements` 기록

Out of scope:

- CSV, XLSX extractor (v06-04, v06-05)
- `tools/process_source.py` 통합 (v06-06)
- Lodestone 전용 extractor (v05.1, 기존 `tools/extractors/lodestone.py` 유지)
- pending loop / derived wiki

## Red Test

- File: `tests/test_v06_extractors.py`
- Fixtures:
  - `tests/fixtures/source_files/sample.txt`
  - `tests/fixtures/source_files/sample.md`
  - `tests/fixtures/source_files/sample.html`
- Implementation target:
  - `src/source_processing/extractors/text.py`
  - `src/source_processing/extractors/markdown.py`
  - `src/source_processing/extractors/html.py`
- Expected red reason: 각 extractor module이 아직 stub이거나 비어 있어 contract 테스트 실패.

Contracts fixed by the tests:

- TXT extractor는 sample.txt의 본문을 손실 없이 반환한다.
- Markdown extractor는 sample.md의 heading 텍스트를 반환 결과에 유지한다.
- HTML extractor는 sample.html에서 `<script>`, `<style>`, `<nav>`, `<footer>` 내부 텍스트를 제외한다.
- HTML extractor는 sample.html의 `<main>` 또는 `<article>`/`<body>` 본문은 포함한다.
- HTML extractor metadata에 `html_title`과 `removed_elements`가 존재한다.

## Checklist

- [ ] `tests/fixtures/source_files/sample.txt` 추가
- [ ] `tests/fixtures/source_files/sample.md` 추가 (heading + frontmatter)
- [ ] `tests/fixtures/source_files/sample.html` 추가 (script/style/nav/footer + main)
- [ ] `src/source_processing/extractors/text.py` 구현
  - [ ] UTF-8 read
  - [ ] 디코딩 실패 시 `SourceDecodingError`
  - [ ] `ExtractedSource` 반환, metadata에 `extractor_name=text`
- [ ] `src/source_processing/extractors/markdown.py` 구현
  - [ ] heading 보존
  - [ ] frontmatter 처리 (있으면 metadata로 분리)
  - [ ] `extractor_name=markdown`
- [ ] `src/source_processing/extractors/html.py` 구현
  - [ ] script/style/nav/footer 제거
  - [ ] title 추출
  - [ ] heading/paragraph 중심 normalize
  - [ ] 공백 collapse
  - [ ] metadata `html_title`, `removed_elements`
  - [ ] `extractor_name=html`
- [ ] `extractor_registry.py`의 stub을 실제 함수로 교체 (`.txt`, `.md`, `.html`, `.htm`)
- [ ] `tests/test_v06_extractors.py`에 다음 테스트 추가
  - [ ] `test_text_extractor_preserves_plain_text`
  - [ ] `test_text_extractor_raises_on_invalid_encoding` (optional)
  - [ ] `test_markdown_extractor_preserves_headings`
  - [ ] `test_html_extractor_removes_script_and_style`
  - [ ] `test_html_extractor_removes_nav_and_footer`
  - [ ] `test_html_extractor_preserves_main_content`
  - [ ] `test_html_extractor_records_removed_elements_metadata`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_extractors -v
python -m py_compile \
  src/source_processing/extractors/text.py \
  src/source_processing/extractors/markdown.py \
  src/source_processing/extractors/html.py
```

기존 Lodestone 회귀:

```bash
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

## Key Decisions

- v0.6 일반 HTML extractor는 Lodestone 전용 extractor를 대체하지 않는다. Lodestone URL은 기존 `tools/extractors/lodestone.py`로 라우팅되는 v05.1 경로를 유지한다.
- Markdown 처리는 deterministic하게 유지하고 AST/플러그인 dependency 추가는 금지한다.
- HTML extractor는 dependency-light로 시작하되, BeautifulSoup이 이미 repo에 있으면 재사용한다. 새 dependency 추가는 spec/plan 갱신 후에만 한다.
- 향후 PDF/DOCX 지원과 충돌하지 않도록 metadata key 이름은 spec와 일치시킨다 (`removed_elements`, `html_title` 등).

## Implementation Notes

- 세 extractor 모두 `ExtractedSource`를 반환해야 하며 필수 metadata(`source_path`, `extension`, `extracted_at`, `extractor_name`)을 채운다.
- 파일이 비어 있는 경우 빈 `text=""`로 두되 metadata에 그 사실을 표시한다. error로 처리할지는 v06-06 통합 시점에 결정하므로, 이 task에서는 단순히 빈 결과를 반환한다.
- registry stub 교체 시 case-insensitive lookup이 깨지지 않도록 v06-02 테스트를 회귀로 함께 돌린다.

## Verification Results

- Pending.
