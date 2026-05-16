# v06 Implementation Plan - Multi-format Source Processing and Derived Wiki Generation

Status: Active
Target spec: SPEC 0006 - v0.6 Multi-format Source Processing and Derived Wiki Generation
Project: ffxiv-claw-bot
Storage root: /mnt/d/ffixiv-bot-storage
Repository root: /mnt/d/programming/ffxiv-claw-bot
Created: 2026-05-16

## 1. 목적

v06의 목적은 현재 source별 요약 자동화 파이프라인을 확장하여 다음 두 가지를 달성하는 것이다.

1. 다양한 원본 파일 형식을 source로 등록하고 자동 처리한다.
2. source별 요약을 다시 주제별 derived wiki 문서로 재구성한다.

현재 자동화는 다음 단계까지 수행한다.

    source ingest
      -> compile_wiki
      -> wiki/source_summaries/<source_id>.md 생성
      -> FTS 인덱싱
      -> graph 생성

v06 완료 후 목표 파이프라인은 다음과 같다.

    local source file
      -> extension detection
      -> extractor registry
      -> normalized text
      -> source ingest
      -> source summary generation
      -> FTS indexing
      -> graph build
      -> derived wiki generation
      -> wiki/jobs/*.md generation
      -> derived wiki FTS indexing

즉, v06는 단순한 batch loop가 아니라 multi-format ingestion과 topic-oriented wiki generation을 포함하는 단계다.

## 2. 비목표

v06에서 하지 않을 작업을 명확히 제한한다.

- 이미지 OCR
- 스캔 PDF OCR
- PDF table extraction
- DOCX 스타일 보존
- Excel 차트 해석
- Excel 수식 의미 분석
- Discord command 추가
- scheduler 또는 watcher daemon 추가
- 신규 web crawler 구현
- LLM 기반 답변 품질 튜닝

PDF, DOCX, 이미지 지원은 이후 v06.1 또는 v07에서 별도 spec으로 다룬다.

## 3. 구현 원칙

1. process_source.py에 확장자별 세부 로직을 몰아넣지 않는다.
2. extractor는 독립적으로 테스트 가능해야 한다.
3. source summary와 derived wiki를 명확히 구분한다.
4. derived wiki 항목은 가능한 한 source_id와 patch version을 보존한다.
5. source summary에 없는 정보를 derived wiki에 확정 정보로 생성하지 않는다.
6. 실패는 조용히 무시하지 말고 stage, message, retry_count로 기록한다.
7. FTS와 graph 갱신은 source processing의 성공 조건에 포함한다.
8. v06 task는 agent가 하나씩 맡아도 충돌하지 않도록 파일 단위 책임을 분리한다.

## 4. 권장 파일 구조

새 파일과 변경 대상은 다음 구조를 기준으로 한다.

    tools/
      process_source.py
      process_pending_sources.py
      generate_derived_wiki.py
      generate_job_wiki.py

    src/
      source_processing/
        __init__.py
        models.py
        errors.py
        extractor_registry.py
        extractors/
          __init__.py
          text.py
          markdown.py
          html.py
          csv.py
          xlsx.py
      derived_wiki/
        __init__.py
        job_catalog.py
        summary_loader.py
        job_wiki_generator.py
        templates.py
        writer.py
      wiki_indexing/
        __init__.py
        wiki_document_scanner.py

    tests/
      fixtures/
        source_files/
          sample.txt
          sample.md
          sample.html
          sample.csv
          sample.xlsx
          unsupported.png
        source_summaries/
          patch_7_0.md
          patch_7_1.md
          patch_7_2.md
      test_v06_extractors.py
      test_v06_pending_sources.py
      test_v06_job_wiki_generator.py
      test_v06_fts_indexing.py

실제 레포의 기존 구조가 다르면, 새 구조를 그대로 강제하지 말고 기존 import style과 패키지 구조에 맞춰 조정한다. 단, extractor layer와 derived_wiki layer는 분리한다.

## 5. 데이터 모델

### 5.1 ExtractedSource

모든 extractor는 동일한 shape를 반환해야 한다.

    class ExtractedSource:
        title: str
        text: str
        metadata: dict[str, Any]

필수 metadata:

- source_path
- extension
- extracted_at
- extractor_name

형식별 추가 metadata:

- CSV: row_count, column_count, columns
- XLSX: sheet_count, sheet_names, total_row_count, empty_sheets
- HTML: html_title, removed_elements

### 5.2 UnsupportedSourceExtensionError

지원하지 않는 확장자는 명확한 에러로 처리한다.

    UnsupportedSourceExtensionError(extension: str, source_path: str)

이 에러는 pending loop에서 다음 상태로 기록되어야 한다.

    status: error
    error_stage: extract
    error_message: Unsupported source extension: .png
    retry_count: retry_count + 1

## 6. Task Breakdown

## Task v06-1. Extractor model and error layer 추가

### 목표

source extractor가 공통으로 사용할 model과 error class를 추가한다.

### 변경 파일

- src/source_processing/models.py
- src/source_processing/errors.py
- src/source_processing/__init__.py
- tests/test_v06_extractors.py

### 구현 내용

1. ExtractedSource 모델 정의
2. SourceExtractionError base class 정의
3. UnsupportedSourceExtensionError 정의
4. SourceDecodingError 정의
5. SourceParseError 정의

### Red test

먼저 다음 테스트를 작성하고 실패를 확인한다.

    test_extracted_source_requires_text_and_metadata
    test_unsupported_extension_error_includes_extension_and_path

### Acceptance Criteria

- ExtractedSource가 title, text, metadata를 가진다.
- UnsupportedSourceExtensionError 메시지에 extension과 source path가 포함된다.
- unittest에서 v06-1 관련 테스트가 통과한다.

### Agent prompt

    Implement v06-1 only. Add the shared source extraction model and error classes for v06. Do not implement any actual extractor yet. Add failing tests first, then make them pass. Keep the implementation small and compatible with the existing project import style.

## Task v06-2. Extractor registry 구현

### 목표

파일 확장자에 따라 extractor function을 선택하는 registry를 구현한다.

### 변경 파일

- src/source_processing/extractor_registry.py
- src/source_processing/extractors/__init__.py
- tests/test_v06_extractors.py

### 구현 내용

1. EXTRACTORS mapping 정의
2. get_extractor_for_path(path) 구현
3. extract_source_text(path) 구현
4. 미지원 확장자에서 UnsupportedSourceExtensionError 발생

초기 registry에는 아직 stub 또는 실제 구현 예정 함수를 연결한다.

    .txt
    .md
    .html
    .htm
    .csv
    .xlsx

### Red test

    test_registry_selects_text_extractor_for_txt
    test_registry_selects_markdown_extractor_for_md
    test_registry_selects_html_extractor_for_html_and_htm
    test_registry_selects_csv_extractor_for_csv
    test_registry_selects_xlsx_extractor_for_xlsx
    test_registry_raises_for_unsupported_extension

### Acceptance Criteria

- suffix는 case-insensitive로 처리된다.
- .HTML, .XLSX 같은 대문자 확장자도 정상 처리된다.
- 미지원 확장자는 extract stage error로 추적 가능하다.

### Agent prompt

    Implement v06-2 only. Add an extractor registry that maps file extensions to extractor functions. Write red tests for supported extensions and unsupported extensions. Do not implement full extraction logic beyond minimal stubs required for registry tests unless the functions already exist.

## Task v06-3. TXT, Markdown, HTML extractor 구현

### 목표

기본 문서형 파일을 normalized text로 변환한다.

### 변경 파일

- src/source_processing/extractors/text.py
- src/source_processing/extractors/markdown.py
- src/source_processing/extractors/html.py
- tests/test_v06_extractors.py
- tests/fixtures/source_files/sample.txt
- tests/fixtures/source_files/sample.md
- tests/fixtures/source_files/sample.html

### 구현 내용

TXT:

- UTF-8로 파일을 읽는다.
- 실패 시 SourceDecodingError를 발생시킨다.
- 원문 텍스트를 그대로 반환한다.

Markdown:

- Markdown heading과 본문 구조를 보존한다.
- frontmatter가 있으면 최소한 본문과 함께 유지하거나 metadata로 분리한다.
- v06에서는 복잡한 markdown AST 처리는 하지 않는다.

HTML:

- BeautifulSoup를 사용한다.
- script, style, nav, footer 제거
- title 추출
- 본문 텍스트를 heading과 paragraph 중심으로 normalize
- 불필요한 공백을 collapse

### Red test

    test_text_extractor_preserves_plain_text
    test_markdown_extractor_preserves_headings
    test_html_extractor_removes_script_and_style
    test_html_extractor_removes_nav_and_footer
    test_html_extractor_preserves_main_content

### Acceptance Criteria

- sample.txt의 내용이 손실 없이 추출된다.
- sample.md의 heading이 추출 결과에 남는다.
- sample.html의 script/style/nav/footer 내용은 추출 결과에 없다.
- sample.html의 main/article/body 본문은 추출 결과에 있다.

### Agent prompt

    Implement v06-3 only. Add txt, markdown, and html extractors. Preserve useful document structure. Strip noisy HTML elements. Write red tests first using small fixtures. Do not touch CSV, XLSX, pending loop, derived wiki, or FTS indexing in this task.

## Task v06-4. CSV extractor 구현

### 목표

CSV 파일을 column header가 보존된 Markdown table 또는 structured text로 변환한다.

### 변경 파일

- src/source_processing/extractors/csv.py
- tests/test_v06_extractors.py
- tests/fixtures/source_files/sample.csv

### 구현 내용

1. Python csv module 또는 pandas 사용
2. header row 보존
3. row values 보존
4. Markdown table 생성
5. metadata에 row_count, column_count, columns 저장

권장 출력 예시:

    # Source: sample.csv

    | Dungeon | Boss | Item |
    |---|---|---|
    | The Aetherfont | Lyngbakr | Hypostatic Gear |

### Red test

    test_csv_extractor_preserves_headers
    test_csv_extractor_preserves_rows
    test_csv_extractor_outputs_markdown_table
    test_csv_extractor_records_row_and_column_metadata

### Acceptance Criteria

- header가 추출 텍스트에 포함된다.
- row 값이 추출 텍스트에 포함된다.
- metadata.columns가 실제 CSV header와 일치한다.
- 비어 있는 CSV는 명확한 SourceParseError 또는 빈 table metadata를 남긴다.

### Agent prompt

    Implement v06-4 only. Add CSV extraction to normalized Markdown table text. Preserve headers and rows. Add metadata for row_count, column_count, and columns. Write red tests first. Do not change XLSX or derived wiki logic.

## Task v06-5. XLSX extractor 구현

### 목표

Excel workbook을 sheet별 Markdown table로 변환한다.

### 변경 파일

- src/source_processing/extractors/xlsx.py
- tests/test_v06_extractors.py
- tests/fixtures/source_files/sample.xlsx

### 구현 내용

1. openpyxl 사용
2. workbook의 모든 sheet 순회
3. empty sheet는 skip하되 metadata.empty_sheets에 기록
4. 각 sheet name을 heading으로 보존
5. 첫 번째 non-empty row를 header로 사용하거나, header가 불명확한 경우 Column 1, Column 2 형식으로 fallback
6. 셀 값은 저장된 값 기준으로 추출
7. 수식 의미 분석은 하지 않는다
8. chart, image, style은 무시한다

권장 출력 예시:

    # Source: sample.xlsx

    ## Sheet: Dungeon Drops

    | Dungeon | Boss | Item | Drop Rate |
    |---|---|---|---|
    | The Aetherfont | Lyngbakr | Hypostatic Gear | Unknown |

    ## Sheet: Currency

    | Content | Token | Weekly Limit |
    |---|---|---|
    | Raid | Savage Book | 1 per floor |

### Red test

    test_xlsx_extractor_reads_single_sheet
    test_xlsx_extractor_preserves_sheet_name
    test_xlsx_extractor_reads_multiple_sheets
    test_xlsx_extractor_records_sheet_metadata
    test_xlsx_extractor_skips_empty_sheets_but_records_them

### Acceptance Criteria

- multi-sheet workbook이 모두 추출된다.
- sheet name이 추출 텍스트에 포함된다.
- empty sheet가 추출 텍스트에는 나오지 않지만 metadata에 기록된다.
- metadata.sheet_count와 sheet_names가 정확하다.

### Agent prompt

    Implement v06-5 only. Add XLSX extraction with openpyxl. Convert each non-empty sheet to Markdown table text and preserve sheet names. Skip empty sheets but record them in metadata. Write red tests first. Do not implement Excel formula evaluation, chart parsing, or style preservation.

## Task v06-6. process_source.py와 extractor layer 연결

### 목표

기존 process_source.py가 local file source를 처리할 때 extractor registry를 사용하도록 연결한다.

### 변경 파일

- tools/process_source.py
- 관련 ingest module
- tests/test_v06_extractors.py 또는 별도 integration test

### 구현 내용

1. source record에서 source file path 확인
2. source body가 직접 전달되는 경우 기존 경로 유지
3. source file path가 있는 경우 extract_source_text(path) 호출
4. 반환된 ExtractedSource.text를 ingest body로 사용
5. ExtractedSource.metadata를 source metadata 또는 processing metadata에 보존
6. extractor 실패 시 stage=extract로 error 처리

### Red test

    test_process_source_uses_extractor_for_local_file_source
    test_process_source_records_extract_error_for_unsupported_file
    test_process_source_preserves_extracted_metadata

### Acceptance Criteria

- .md source file을 process_source.py로 처리하면 source summary까지 생성된다.
- .xlsx source file을 process_source.py로 처리하면 normalized text가 ingest된다.
- .png 같은 미지원 파일은 error 상태로 남는다.

### Agent prompt

    Implement v06-6 only. Integrate the extractor registry into the existing process_source flow for local file sources. Preserve the existing body-based behavior. Errors from extraction must be recorded as extract-stage failures. Add red tests before implementation.

## Task v06-7. Pending source automation loop 구현 또는 보강

### 목표

pending 상태의 source 여러 개를 일괄 처리하는 CLI를 구현한다.

### 변경 파일

- tools/process_pending_sources.py
- source status DB access layer
- tests/test_v06_pending_sources.py

### CLI 계약

    python tools/process_pending_sources.py --limit 10
    python tools/process_pending_sources.py --source-type local_file --limit 10
    python tools/process_pending_sources.py --retry-errors --max-retry 3
    python tools/process_pending_sources.py --dry-run

### 구현 내용

1. pending source 조회
2. --limit 적용
3. --dry-run에서는 대상 source_id만 출력하고 처리하지 않음
4. 처리 시작 시 in_progress로 상태 변경
5. process_source 호출
6. 성공 시 processed/wiki_built/graph_built 계열 상태 반영
7. 실패 시 error 상태와 error_stage, error_message 기록
8. retry_count 증가
9. --retry-errors가 있을 때 retry_count < max_retry인 error source 재처리

### Red test

    test_pending_loop_processes_pending_sources_up_to_limit
    test_pending_loop_dry_run_does_not_mutate_status
    test_pending_loop_marks_successful_source_processed
    test_pending_loop_marks_failed_source_error
    test_pending_loop_increments_retry_count
    test_retry_errors_only_retries_below_max_retry

### Acceptance Criteria

- pending source 여러 개를 한 번에 처리할 수 있다.
- dry-run이 DB 상태를 변경하지 않는다.
- 실패 source가 재시도 가능한 상태로 남는다.
- loop 실행 결과가 stdout에 요약된다.

### Agent prompt

    Implement v06-7 only. Add or harden the pending source processing CLI. It must support --limit, --dry-run, --retry-errors, and --max-retry. Add red tests for status transitions and retry behavior before implementation. Do not implement derived wiki generation in this task.

## Task v06-8. Derived wiki foundation 구현

### 목표

source summaries를 읽어 derived wiki 생성에 사용할 입력 모델로 변환한다.

### 변경 파일

- src/derived_wiki/summary_loader.py
- src/derived_wiki/writer.py
- src/derived_wiki/templates.py
- tests/test_v06_job_wiki_generator.py
- tests/fixtures/source_summaries/patch_7_0.md
- tests/fixtures/source_summaries/patch_7_1.md

### 구현 내용

1. wiki/source_summaries 디렉터리 scan
2. source summary 파일에서 source_id 추출
3. patch version 추출
4. title 또는 heading 추출
5. text body 로딩
6. derived wiki output writer 구현

patch version 추출은 우선 filename, heading, metadata 순서로 시도한다.

예시:

    patch_7_0.md -> 7.0
    patch_7_1.md -> 7.1
    # Patch 7.2 Notes -> 7.2

### Red test

    test_summary_loader_reads_source_summary_files
    test_summary_loader_extracts_source_id
    test_summary_loader_extracts_patch_version_from_filename
    test_summary_writer_writes_to_target_path

### Acceptance Criteria

- source_summaries를 summary object 목록으로 읽을 수 있다.
- 각 summary는 source_id, patch_version, title, text를 가진다.
- writer는 target path의 parent directory를 생성한다.

### Agent prompt

    Implement v06-8 only. Build the foundation for derived wiki generation: load source summaries, extract source_id and patch_version when possible, and write output files. Add red tests first. Do not implement job-specific extraction logic yet.

## Task v06-9. Job catalog와 job alias 정의

### 목표

FFXIV 직업별 derived wiki 생성을 위한 canonical job list와 alias mapping을 정의한다.

### 변경 파일

- src/derived_wiki/job_catalog.py
- tests/test_v06_job_wiki_generator.py

### 구현 내용

1. canonical job slug 목록 정의
2. display name 정의
3. 한국어/영어/약어 alias 정의
4. blue mage는 limited job이므로 include_limited 옵션으로 제어 가능하게 설계

권장 canonical slug:

- paladin
- warrior
- dark_knight
- gunbreaker
- white_mage
- scholar
- astrologian
- sage
- monk
- dragoon
- ninja
- samurai
- reaper
- viper
- bard
- machinist
- dancer
- black_mage
- summoner
- red_mage
- pictomancer
- blue_mage

alias 예시:

    gunbreaker: Gunbreaker, GNB, 건브레이커
    black_mage: Black Mage, BLM, 흑마도사, 흑마
    paladin: Paladin, PLD, 나이트

### Red test

    test_job_catalog_contains_gunbreaker
    test_job_catalog_resolves_english_alias
    test_job_catalog_resolves_abbreviation_alias
    test_job_catalog_resolves_korean_alias
    test_job_catalog_can_exclude_limited_jobs

### Acceptance Criteria

- 모든 전투 직업의 canonical slug가 있다.
- alias로 canonical job을 찾을 수 있다.
- Blue Mage 포함 여부를 옵션으로 제어할 수 있다.

### Agent prompt

    Implement v06-9 only. Add a canonical FFXIV job catalog and alias resolver for derived job wiki generation. Include Korean, English, and abbreviation aliases where reasonable. Add red tests first. Do not implement summary scanning or wiki generation here.

## Task v06-10. Job wiki generator 구현

### 목표

source summaries에서 직업 관련 내용을 수집해 wiki/jobs/<job>.md를 생성한다.

### 변경 파일

- src/derived_wiki/job_wiki_generator.py
- src/derived_wiki/templates.py
- tools/generate_job_wiki.py
- tests/test_v06_job_wiki_generator.py

### CLI 계약

    python tools/generate_job_wiki.py --all
    python tools/generate_job_wiki.py --job gunbreaker
    python tools/generate_job_wiki.py --job gunbreaker --patch-range 7.0..7.5
    python tools/generate_job_wiki.py --dry-run

### 구현 내용

1. job alias를 기준으로 source summary text에서 관련 section 또는 bullet 수집
2. patch_version 기준 시간순 정렬
3. 중복 bullet 제거
4. job별 Markdown 문서 생성
5. source_id와 patch_version 보존
6. 근거 없는 내용은 생성하지 않음

v06의 1차 구현은 LLM 없이 deterministic extraction으로 제한한다.

- job name alias가 포함된 line
- job name alias가 포함된 section
- action name catalog가 없으면 action-level extraction은 보류

향후 action catalog를 추가하면 더 정밀하게 만들 수 있다.

### 출력 형식

    # Gunbreaker 변경 이력

    ## 개요

    이 문서는 source summaries를 기반으로 Gunbreaker 관련 변경 사항을 시간순으로 정리한다.

    ## 7.0

    ### 변경 사항
    - 변경 사항 본문

    ### 출처
    - source_id: patch_7_0

    ## 7.1

    ### 변경 사항
    - 변경 사항 본문

    ### 출처
    - source_id: patch_7_1

    ## 누적 요약

    - v06에서는 근거 기반 bullet만 나열한다.
    - 해석형 요약은 후속 버전에서 LLM summarizer로 확장한다.

### Red test

    test_generate_single_job_wiki_creates_file
    test_generate_job_wiki_includes_job_title
    test_generate_job_wiki_includes_matching_patch_entries
    test_generate_job_wiki_preserves_source_id
    test_generate_job_wiki_sorts_entries_by_patch_version
    test_generate_job_wiki_deduplicates_duplicate_entries
    test_generate_job_wiki_dry_run_does_not_write_file

### Acceptance Criteria

- `wiki/jobs/gunbreaker.md`가 생성된다.
- 생성 문서에 patch version과 source_id가 포함된다.
- 관련 없는 patch summary는 문서에 들어가지 않는다.
- dry-run은 생성 예정 내용만 출력하고 파일을 쓰지 않는다.

### Agent prompt

    Implement v06-10 only. Add a deterministic job wiki generator that reads source summaries, finds job-related entries using the job catalog aliases, sorts by patch version, deduplicates entries, and writes wiki/jobs/<job>.md. Add red tests first. Do not add LLM summarization.

## Task v06-11. generate_derived_wiki.py 통합 CLI 구현

### 목표

derived wiki generation을 통합 CLI에서 실행할 수 있게 한다.

### 변경 파일

- tools/generate_derived_wiki.py
- tests/test_v06_job_wiki_generator.py

### CLI 계약

    python tools/generate_derived_wiki.py --kind jobs
    python tools/generate_derived_wiki.py --kind jobs --job gunbreaker
    python tools/generate_derived_wiki.py --kind jobs --patch-range 7.0..7.5
    python tools/generate_derived_wiki.py --kind jobs --dry-run

### 구현 내용

1. --kind jobs 지원
2. --job이 있으면 단일 직업만 생성
3. --job이 없으면 전체 직업 생성
4. --patch-range 적용
5. --dry-run 지원
6. 향후 raids/items/systems를 위한 unsupported kind error 추가

### Red test

    test_generate_derived_wiki_jobs_invokes_job_generator
    test_generate_derived_wiki_rejects_unknown_kind
    test_generate_derived_wiki_passes_patch_range
    test_generate_derived_wiki_dry_run

### Acceptance Criteria

- jobs kind가 정상 동작한다.
- unknown kind는 명확한 에러를 낸다.
- CLI help가 사용 가능한 옵션을 보여준다.

### Agent prompt

    Implement v06-11 only. Add the generic generate_derived_wiki.py CLI and wire --kind jobs to the job wiki generator. Add red tests first. Unknown kinds should fail clearly. Do not implement raids/items/systems yet.

## Task v06-12. FTS indexing 대상 확장

### 목표

FTS 인덱싱이 source_summaries뿐 아니라 derived wiki 문서도 포함하도록 확장한다.

### 변경 파일

- 기존 FTS indexing module
- src/wiki_indexing/wiki_document_scanner.py
- tests/test_v06_fts_indexing.py

### 구현 내용

1. wiki 문서 scanner 추가 또는 기존 scanner 확장
2. 다음 경로를 인덱싱 대상으로 포함

    wiki/source_summaries/*.md
    wiki/jobs/*.md

3. wiki_type metadata 추가

    source_summary
    job

4. topic metadata 추가

    jobs/gunbreaker.md -> topic=gunbreaker

5. 기존 source_summaries 인덱싱 동작은 깨지지 않아야 함

### Red test

    test_fts_scanner_includes_source_summaries
    test_fts_scanner_includes_job_wiki_pages
    test_fts_scanner_sets_wiki_type_for_job_pages
    test_fts_scanner_sets_topic_from_job_filename
    test_existing_source_summary_indexing_still_works

### Acceptance Criteria

- `wiki/jobs/gunbreaker.md`가 FTS 검색 대상에 포함된다.
- source summary 인덱싱이 regression 없이 유지된다.
- 검색 결과에서 wiki_type과 topic을 구분할 수 있다.

### Agent prompt

    Implement v06-12 only. Extend FTS indexing to include derived wiki pages under wiki/jobs/*.md while preserving existing source_summaries indexing. Add metadata for wiki_type and topic. Add red tests first.

## Task v06-13. process_source 완료 후 derived wiki hook 연결

### 목표

source processing 후 derived wiki generation을 선택적으로 실행할 수 있게 한다.

### 변경 파일

- tools/process_source.py
- tools/process_pending_sources.py
- tools/generate_derived_wiki.py
- tests/test_v06_pending_sources.py

### CLI 옵션

process_source.py에 다음 옵션 중 하나를 추가한다.

    --build-derived-wiki
    --skip-derived-wiki

기본값은 프로젝트 상황에 따라 선택한다. v06에서는 안전하게 기본 skip을 권장한다.

권장 기본 정책:

- process_source.py 단독 실행: 기본 skip
- process_pending_sources.py: 옵션으로 --build-derived-wiki 제공

### 구현 내용

1. source processing 성공 후 optional derived wiki generation 실행
2. derived wiki generation 성공 시 상태에 derived_wiki_built 기록
3. 실패 시 source processing 자체 성공과 derived wiki 실패를 구분
4. derived wiki 실패는 error_stage=derived_wiki_generate로 기록

### Red test

    test_process_pending_sources_can_build_derived_wiki_when_enabled
    test_process_pending_sources_skips_derived_wiki_by_default
    test_derived_wiki_failure_records_derived_wiki_stage

### Acceptance Criteria

- 기존 process_source 동작을 깨지 않는다.
- derived wiki generation은 명시적 옵션으로 실행 가능하다.
- derived wiki 실패 stage가 구분된다.

### Agent prompt

    Implement v06-13 only. Add an optional derived wiki generation hook after successful source processing. Keep it disabled by default unless explicitly requested. Record derived_wiki_generate failures separately. Add red tests first.

## Task v06-14. README와 handoff 문서 업데이트

### 목표

v06 사용법을 문서화하고 다음 작업자가 같은 방식으로 진행할 수 있게 한다.

### 변경 파일

- README.md 또는 docs/README.md
- docs/specs/ 또는 docs/plans/ 내 v06 문서
- CURRENT_HANDOFF 문서가 레포에 있다면 업데이트

### 문서에 포함할 내용

1. v06 목표
2. 지원 확장자
3. extractor 구조
4. pending loop 실행법
5. derived wiki generation 실행법
6. FTS indexing 대상
7. known limitations
8. troubleshooting

### 문서 예시 명령어

    python tools/process_pending_sources.py --limit 10 --dry-run
    python tools/process_pending_sources.py --limit 10
    python tools/generate_job_wiki.py --job gunbreaker
    python tools/generate_derived_wiki.py --kind jobs --all

### Acceptance Criteria

- 새 개발자가 README만 보고 v06 pipeline을 실행할 수 있다.
- v06에서 지원하지 않는 범위가 명확히 적혀 있다.
- Notion spec과 repo 문서의 범위가 충돌하지 않는다.

### Agent prompt

    Implement v06-14 only. Update documentation for v06 usage and limitations. Do not change runtime code. Document extractor support, pending source loop, derived wiki generation, FTS indexing, and known exclusions.

## 7. 권장 구현 순서

v06는 다음 순서로 진행한다.

    v06-1 -> v06-2 -> v06-3 -> v06-4 -> v06-5
      -> v06-6 -> v06-7
      -> v06-8 -> v06-9 -> v06-10 -> v06-11
      -> v06-12 -> v06-13 -> v06-14

작업 묶음은 다음처럼 나누는 것이 좋다.

### Batch A. Extractor foundation

- v06-1
- v06-2
- v06-3

목표:

- 공통 모델
- registry
- txt/md/html extractor

### Batch B. Table file support

- v06-4
- v06-5

목표:

- CSV 지원
- XLSX 지원

### Batch C. Source processing automation

- v06-6
- v06-7

목표:

- process_source 통합
- pending source loop

### Batch D. Derived wiki foundation

- v06-8
- v06-9
- v06-10
- v06-11

목표:

- source summaries 로딩
- job catalog
- job wiki 생성
- 통합 CLI

### Batch E. Search integration and docs

- v06-12
- v06-13
- v06-14

목표:

- FTS 확장
- optional derived wiki hook
- 문서화

## 8. 병렬 작업 가능성

병렬로 맡겨도 되는 작업:

- v06-3과 v06-4는 충돌이 적다.
- v06-4와 v06-5는 충돌이 적다.
- v06-8과 v06-9는 충돌이 적다.
- v06-14는 마지막에 하는 것이 좋다.

병렬로 맡기면 안 되는 작업:

- v06-1 이전에 v06-2를 구현하지 않는다.
- v06-2 이전에 process_source integration을 하지 않는다.
- v06-8/v06-9 이전에 v06-10을 하지 않는다.
- v06-12는 v06-10 이후에 한다.
- v06-13은 v06-7과 v06-11 이후에 한다.

## 9. Red Test 정책

v06는 데이터 파이프라인 변경이므로 red test를 적극적으로 요구한다.

반드시 red test가 필요한 task:

- v06-1
- v06-2
- v06-3
- v06-4
- v06-5
- v06-6
- v06-7
- v06-8
- v06-9
- v06-10
- v06-11
- v06-12
- v06-13

문서만 수정하는 v06-14는 red test가 필요 없다.

각 agent 작업 지시에는 다음 문장을 포함한다.

    Start by writing the failing regression tests for this task. Run the tests and confirm they fail for the expected reason before implementing the fix. Then implement the minimal code to make those tests pass. Do not broaden the scope beyond this task.

## 10. 최종 통합 테스트 시나리오

v06 전체 완료 후 다음 시나리오가 통과해야 한다.

### Scenario 1. Markdown source 처리

1. local markdown file을 source로 등록한다.
2. process_pending_sources.py를 실행한다.
3. source summary가 생성된다.
4. FTS에 인덱싱된다.
5. graph가 생성된다.

Expected:

- source 상태가 processed/wiki_built/graph_built 계열로 갱신된다.
- 에러가 없다.

### Scenario 2. XLSX source 처리

1. sample.xlsx를 source로 등록한다.
2. process_pending_sources.py를 실행한다.
3. xlsx extractor가 sheet별 Markdown table을 생성한다.
4. source summary가 생성된다.

Expected:

- sheet name과 table content가 source summary에 반영된다.
- metadata에 sheet_count, sheet_names가 기록된다.

### Scenario 3. Unsupported source 처리

1. unsupported.png를 source로 등록한다.
2. process_pending_sources.py를 실행한다.

Expected:

- source status가 error가 된다.
- error_stage는 extract다.
- error_message에 unsupported extension이 포함된다.
- retry_count가 증가한다.

### Scenario 4. Gunbreaker derived wiki 생성

1. patch_7_0.md, patch_7_1.md, patch_7_2.md source summaries를 준비한다.
2. generate_job_wiki.py --job gunbreaker를 실행한다.

Expected:

- wiki/jobs/gunbreaker.md가 생성된다.
- Gunbreaker 관련 내용만 포함된다.
- patch version과 source_id가 포함된다.
- patch version 순서가 유지된다.

### Scenario 5. Derived wiki FTS 검색

1. wiki/jobs/gunbreaker.md를 생성한다.
2. FTS indexing을 실행한다.
3. gunbreaker 또는 건브레이커로 검색한다.

Expected:

- wiki_type=job 결과가 검색된다.
- topic=gunbreaker metadata가 확인된다.

## 11. 완료 기준

v06는 다음 조건을 모두 만족하면 완료로 본다.

- .txt, .md, .html, .csv, .xlsx extractor가 동작한다.
- extractor registry가 확장자별 extractor를 선택한다.
- 미지원 확장자는 error로 기록된다.
- pending source loop가 여러 source를 일괄 처리한다.
- source summary, FTS, graph 생성이 기존처럼 유지된다.
- source summaries를 기반으로 wiki/jobs/*.md를 생성할 수 있다.
- wiki/jobs/gunbreaker.md가 실제 생성된다.
- derived wiki가 source_id와 patch version을 보존한다.
- FTS가 wiki/jobs/*.md를 인덱싱한다.
- 주요 task별 regression test가 있다.
- README 또는 docs에 v06 사용법이 문서화되어 있다.

## 12. Known Risks

### Risk 1. Excel table 구조가 불규칙할 수 있음

완화:

- v06에서는 단순 sheet-to-table 변환만 지원한다.
- 복잡한 merged cell, multi-header, chart, formula는 후속 버전으로 미룬다.

### Risk 2. Job wiki extraction이 누락될 수 있음

완화:

- v06에서는 deterministic alias matching으로 시작한다.
- action catalog 기반 정밀 추출은 후속 버전에서 추가한다.

### Risk 3. Derived wiki가 잘못된 요약을 생성할 수 있음

완화:

- v06에서는 생성형 요약을 최소화한다.
- source summary에 있는 문장 또는 bullet 중심으로 구성한다.
- source_id와 patch version을 항상 남긴다.

### Risk 4. process_source와 pending loop의 책임이 섞일 수 있음

완화:

- process_source.py는 source 1개 처리 entrypoint로 유지한다.
- process_pending_sources.py는 source 여러 개를 반복 처리하는 orchestration layer로 유지한다.

### Risk 5. FTS schema 변경이 기존 검색을 깨뜨릴 수 있음

완화:

- 기존 source_summaries indexing regression test를 먼저 작성한다.
- metadata 확장은 backward-compatible하게 한다.

## 13. Open Questions

구현 중 확인할 항목:

1. 현재 DB에서 source status를 어느 table/column에 저장하는가?
2. source type 또는 file path metadata가 이미 있는가?
3. process_source.py가 body 기반 ingest와 file 기반 ingest를 어떻게 구분하는가?
4. FTS 인덱싱 대상이 파일 시스템 기반인가, DB 기반인가?
5. graph 생성이 source summary 기준인가, wiki_pages 기준인가?
6. Notion status update가 v06 상태값을 수용할 수 있는가?
7. patch version은 source metadata에 이미 있는가, 아니면 filename에서 추출해야 하는가?

이 질문들은 구현 전 코드 확인으로 해결한다. 답이 불명확해도 v06 구조 자체는 유지한다.

## 14. Agent용 통합 지시문

아래 지시문은 v06 전체를 맡길 때 사용한다. 단, 한 번에 전체를 맡기기보다 Batch A부터 순차적으로 맡기는 것을 권장한다.

    You are implementing v06 for ffxiv-claw-bot.

    Goal:
    Implement Multi-format Source Processing and Derived Wiki Generation.

    Scope:
    - Add extractor model and errors.
    - Add extractor registry.
    - Support .txt, .md, .html, .csv, .xlsx.
    - Integrate extractors into process_source for local file sources.
    - Add or harden process_pending_sources.py.
    - Add derived wiki generation foundation.
    - Add job catalog and job wiki generator.
    - Generate wiki/jobs/<job>.md from source summaries.
    - Extend FTS indexing to include wiki/jobs/*.md.
    - Add regression tests.
    - Update docs.

    Constraints:
    - Do not implement OCR.
    - Do not implement PDF support.
    - Do not implement DOCX support.
    - Do not implement Discord commands.
    - Do not implement web crawler changes.
    - Do not add LLM summarization for derived wiki in v06.
    - Preserve existing source_summaries, FTS, and graph behavior.

    Test policy:
    Start each task by writing failing regression tests. Run tests and confirm they fail for the expected reason. Then implement the minimal code to pass those tests.

    Reporting:
    At the end, report:
    1. Files changed
    2. Tests added
    3. Commands run
    4. Passing/failing tests
    5. Any behavior intentionally deferred

## 15. 첫 작업 지시문

처음 agent에게는 전체 v06를 한 번에 맡기지 말고 Batch A만 맡긴다.

    Implement Batch A for v06 only.

    Batch A includes:
    - v06-1 Extractor model and error layer
    - v06-2 Extractor registry
    - v06-3 TXT, Markdown, HTML extractors

    Requirements:
    - Add red tests first.
    - Implement only txt, md, html support.
    - Do not implement csv or xlsx yet.
    - Do not modify pending source loop yet.
    - Do not implement derived wiki generation yet.
    - Keep process_source.py unchanged unless strictly necessary for tests.

    Expected result:
    - ExtractedSource model exists.
    - UnsupportedSourceExtensionError exists.
    - Registry resolves .txt, .md, .html, .htm.
    - TXT, Markdown, HTML extractors work.
    - HTML extractor removes script/style/nav/footer.
    - Tests for Batch A pass.

## 16. 요약

v06 implementation의 핵심은 다음 순서다.

    extractor 기반 정규화
      -> pending source 자동 처리
      -> source_summaries 유지
      -> derived wiki 생성
      -> jobs wiki 검색 편입

이 계획서의 우선순위는 기능을 많이 넣는 것이 아니라, source processing과 derived wiki generation의 책임을 분리하고, 각 단계를 테스트 가능한 단위로 만드는 것이다.
