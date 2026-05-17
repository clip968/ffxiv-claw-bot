# SPEC 0006 - v0.6 Multi-format Source Processing and Derived Wiki Generation

Status: Implemented 2026-05-16; v06.1 FTS hardening added 2026-05-16

Target version: v0.6

Project: ffxiv-claw-bot

Created: 2026-05-16

## 1. 목적

v0.6의 목적은 현재의 단일 source 처리 자동화를 확장하여, 다양한 원본 파일 형식을 안정적으로 처리하고, source 단위 요약을 넘어 주제별 derived wiki 문서를 자동 생성하는 것이다.

현재 자동화는 다음 단계까지만 담당한다.

- source ingest: 원본 저장
- compile_wiki: 각 source마다 `wiki/source_summaries/<source_id>.md` 생성
- FTS 인덱싱
- graph 생성

그러나 다음 단계는 아직 자동화되어 있지 않다.

- `wiki/jobs/*.md` 생성
- `wiki/items/*.md` 생성
- `wiki/raids/*.md` 생성
- `wiki/systems/*.md` 생성
- 여러 source를 읽어 직업별, 레이드별, 시스템별 누적 변경 이력으로 재구성

v0.6은 이 차이를 해소한다.

## 2. 핵심 정의

v0.6은 다음 두 레이어로 구성한다.

### Layer 1. Multi-format Source Processing

로컬 storage에 저장된 다양한 원본 파일을 확장자별 extractor로 정규화하고, 기존 source processing 파이프라인으로 넘긴다.

지원 대상 1차 범위:

- `.txt`
- `.md`
- `.html` / `.htm`
- `.csv`
- `.xlsx`

### Layer 2. Derived Wiki Generation

`wiki/source_summaries/*.md` 또는 DB의 source summary 내용을 기반으로 주제별 위키 문서를 생성한다.

1차 목표는 직업별 변경 이력이다.

- `wiki/jobs/paladin.md`
- `wiki/jobs/warrior.md`
- `wiki/jobs/dark_knight.md`
- `wiki/jobs/gunbreaker.md`
- 기타 전투 직업 문서

이후 확장 대상:

- `wiki/raids/*.md`
- `wiki/items/*.md`
- `wiki/systems/*.md`

## 3. 문제 배경

현재 구조에서는 패치노트를 ingest하면 source별 요약은 생성된다.

예시:

- `wiki/source_summaries/patch_7_0.md`
- `wiki/source_summaries/patch_7_1.md`
- `wiki/source_summaries/patch_7_2.md`

이 상태에서도 검색은 가능하다. 그러나 사용자가 “7.x 건브레이커 변경 이력”을 물으면 매번 여러 패치노트를 실시간으로 검색하고, 그중 건브레이커 관련 항목만 추출한 뒤, 시간순으로 병합해야 한다.

즉, 현재 구조는 source 단위 검색에는 강하지만 topic 단위 누적 질문에는 비효율적이다.

v0.6에서는 이 누적 작업을 미리 수행하여 다음과 같은 문서를 생성한다.

- `wiki/jobs/gunbreaker.md`

그러면 “7.x 건브레이커 변경 이력” 질문은 여러 패치노트 전체를 매번 재검색하지 않고, 직업별 derived wiki 문서 하나를 중심으로 답변할 수 있다.

## 4. 범위

### 포함 범위

- 확장자 판별 로직 추가
- extractor interface 정의
- extractor registry 구현
- `.txt`, `.md`, `.html`, `.csv`, `.xlsx` extractor 구현
- pending source 자동 처리 loop 구현 또는 보강
- unsupported extension error 처리
- source 처리 성공, 실패, 재시도 상태 기록
- source summary 생성 후 FTS 및 graph 갱신 보장
- derived wiki generator 설계
- 직업별 변경 이력 문서 생성
- `wiki/jobs/*.md`를 FTS 인덱싱 대상으로 포함
- regression test 작성
- README 및 handoff 문서 업데이트

### 제외 범위

- 이미지 OCR
- 스캔 PDF OCR
- PDF 표 자동 추출
- 복잡한 DOCX 스타일 보존
- Excel 차트 해석
- Excel 수식 의미 분석
- Discord command integration
- 웹 크롤러 신규 추가
- 완전 자동 패치노트 수집 scheduler

## 5. 목표 디렉터리 구조

권장 구조는 다음과 같다.

/mnt/d/ffixiv-bot-storage/

sources/

raw source files

wiki/

source_summaries/

jobs/

raids/

items/

systems/

/mnt/d/programming/ffxiv-claw-bot/

tools/

process_[source.py](http://source.py)

process_pending_[sources.py](http://sources.py)

generate_derived_[wiki.py](http://wiki.py)

generate_job_[wiki.py](http://wiki.py)

src/

source_processing/

extractor_[registry.py](http://registry.py)

extractors/

[text.py](http://text.py)

[markdown.py](http://markdown.py)

[html.py](http://html.py)

[csv.py](http://csv.py)

[xlsx.py](http://xlsx.py)

derived_wiki/

job_[index.py](http://index.py)

job_wiki_[generator.py](http://generator.py)

[templates.py](http://templates.py)

## 6. 처리 흐름

v0.6의 전체 처리 흐름은 다음과 같다.

source file 등록

-> extension detection

-> extractor registry에서 extractor 선택

-> normalized text 생성

-> source ingest

-> compile_wiki

-> wiki/source_summaries/<source_id>.md 생성

-> FTS 인덱싱

-> graph 생성

-> derived wiki generator 실행

-> wiki/jobs/*.md 갱신

-> derived wiki도 FTS 인덱싱

v06.1 hardening note: when `process_source.py --build-derived-wiki` or `process_pending_sources.py --build-derived-wiki` generates job wiki pages, the same pipeline run must call `tools.compile_wiki.index_wiki_documents()` so generated `wiki/jobs/*.md` pages are immediately present in `wiki_fts`.

## 7. Extractor 설계

모든 extractor는 동일한 interface를 따라야 한다.

권장 반환 모델:

ExtractedSource

title: str

text: str

metadata: dict

필수 metadata:

- `source_path`
- `extension`
- `extracted_at`
- `extractor_name`

형식별 추가 metadata:

- CSV: `row_count`, `column_count`, `columns`
- XLSX: `sheet_count`, `sheet_names`, `total_row_count`
- HTML: `title`, `removed_elements`
- Official FFXIV job guide HTML: `official_job`, `source_kind=official_job_guide`

## 8. 형식별 처리 규칙

### TXT

- UTF-8 우선
- 실패 시 명확한 decoding error 기록
- 내용은 그대로 normalized text로 사용

### Markdown

- 원본 Markdown 구조를 최대한 유지
- frontmatter가 있다면 metadata로 분리 가능
- heading 구조는 유지

### HTML

- `script`, `style`, `nav`, `footer` 제거
- 본문 텍스트 중심 추출
- 제목이 있으면 title metadata에 저장
- 링크 텍스트는 가능하면 보존
- Official FFXIV job guide로 감지되면 cross-job menu/nav 텍스트를 본문에서 제거한다.
- Official FFXIV job guide는 현재 job slug를 `official_job` metadata로 기록한다.

### CSV

- header를 보존한다
- Markdown table 또는 TSV-like text로 변환한다
- 열 이름이 사라지지 않아야 한다

예시 출력:

# Source: dungeon_rewards.csv

| Dungeon | Boss | Item |
| --- | --- | --- |
| The Aetherfont | Lyngbakr | Hypostatic Gear |

### XLSX

- workbook의 모든 sheet를 순회한다
- sheet name을 heading으로 보존한다
- 빈 sheet는 skip하되 metadata에 기록한다
- 표는 Markdown table 형태로 변환한다
- 수식 자체를 해석하지 않는다
- 가능하면 셀에 저장된 값 또는 표시 값을 사용한다
- v0.6/v06.1의 XLSX 지원은 기본 표 추출이다. 날짜 표시 형식, 수식 cached value 부재, 병합 셀, 숨김 행/열, 여러 줄 셀의 표현, 빈 첫 행 뒤 header 추론은 고급 Excel 처리 범위로 남긴다.

예시 출력:

# Source: item_drop_table.xlsx

## Sheet: Dungeon Drops

| Dungeon | Boss | Item | Drop Rate |
| --- | --- | --- | --- |
| The Aetherfont | Lyngbakr | Hypostatic Gear | Unknown |

## 9. Extractor Registry

확장자별 처리는 registry로 분리한다.

EXTRACTORS = {

".txt": extract_text_file,

".md": extract_markdown_file,

".html": extract_html_file,

".htm": extract_html_file,

".csv": extract_csv_file,

".xlsx": extract_xlsx_file,

}

처리 규칙:

- 지원하지 않는 확장자는 `UnsupportedSourceExtensionError`를 발생시킨다.
- 이 에러는 source 상태에 `error`로 기록한다.
- 실패 stage는 `extract`로 남긴다.

## 10. Pending Source Automation Loop

`process_pending_sources.py`는 pending 상태의 source를 순차적으로 처리한다.

권장 CLI:

python tools/process_pending_[sources.py](http://sources.py) --limit 10

python tools/process_pending_[sources.py](http://sources.py) --source-type local_file --limit 10

python tools/process_pending_[sources.py](http://sources.py) --retry-errors --max-retry 3

python tools/process_pending_[sources.py](http://sources.py) --dry-run

필수 동작:

- pending source 조회
- source별 lock 또는 in_progress 상태 설정
- `process_source.py` 또는 내부 처리 함수를 호출
- 성공 시 processed / graph_built / wiki_built 상태 기록
- 실패 시 error stage, message, traceback summary 기록
- retry_count 증가
- dry-run에서는 실제 처리 없이 대상 목록만 출력

## 11. Derived Wiki Generation

Derived wiki는 source별 요약을 다시 주제별 문서로 재구성한 결과물이다.

### 1차 대상: 직업별 변경 이력

생성 대상:

- `wiki/jobs/paladin.md`
- `wiki/jobs/warrior.md`
- `wiki/jobs/dark_knight.md`
- `wiki/jobs/gunbreaker.md`
- `wiki/jobs/white_mage.md`
- `wiki/jobs/scholar.md`
- `wiki/jobs/astrologian.md`
- `wiki/jobs/sage.md`
- `wiki/jobs/monk.md`
- `wiki/jobs/dragoon.md`
- `wiki/jobs/ninja.md`
- `wiki/jobs/samurai.md`
- `wiki/jobs/reaper.md`
- `wiki/jobs/viper.md`
- `wiki/jobs/bard.md`
- `wiki/jobs/machinist.md`
- `wiki/jobs/dancer.md`
- `wiki/jobs/black_mage.md`
- `wiki/jobs/summoner.md`
- `wiki/jobs/red_mage.md`
- `wiki/jobs/pictomancer.md`
- `wiki/jobs/blue_mage.md`, 선택

### 직업별 문서 형식

각 문서는 다음 구조를 따른다.

# Gunbreaker 변경 이력

## 개요

이 문서는 source summaries를 기반으로 Gunbreaker 관련 변경 사항을 시간순으로 정리한다.

## 7.0

### 액션 변경

- 변경 사항

### 시스템 영향

- 변경 사항

### 출처

- source_id: patch_7_0

## 7.1

### 액션 변경

- 변경 사항

### 출처

- source_id: patch_7_1

## 누적 요약

- 7.x 전체 변경 흐름
- 플레이 스타일 영향
- 주요 버프/너프 축

필수 조건:

- 각 변경 항목은 가능한 한 patch version과 source_id를 가진다.
- 근거가 없는 추론은 derived wiki에 확정 정보처럼 쓰지 않는다.
- source summary에 없는 정보는 생성하지 않는다.
- 동일 변경 사항이 여러 source에 중복 등장하면 중복 제거한다.

## 12. Derived Wiki Generator CLI

권장 CLI:

python tools/generate_derived_[wiki.py](http://wiki.py) --kind jobs

python tools/generate_derived_[wiki.py](http://wiki.py) --kind jobs --job gunbreaker

python tools/generate_derived_[wiki.py](http://wiki.py) --kind jobs --patch-range 7.0..7.5

python tools/generate_derived_[wiki.py](http://wiki.py) --kind jobs --dry-run

또는 직업 전용 CLI를 별도로 둔다.

python tools/generate_job_[wiki.py](http://wiki.py) --all

python tools/generate_job_[wiki.py](http://wiki.py) --job gunbreaker

python tools/generate_job_[wiki.py](http://wiki.py) --dry-run

## 13. FTS 인덱싱 규칙

현재 FTS가 source summaries만 대상으로 한다면 v0.6에서 대상을 확장한다.

인덱싱 대상:

- `wiki/source_summaries/*.md`
- `wiki/jobs/*.md`
- 향후 `wiki/raids/*.md`
- 향후 `wiki/items/*.md`
- 향후 `wiki/systems/*.md`

권장 metadata:

- `wiki_type`: `source_summary`, `job`, `raid`, `item`, `system`
- `topic`: 예: `gunbreaker`
- `patch_range`: 예: `7.0..7.5`
- `source_ids`: 참조 source id 목록

## 14. 상태 관리

source 처리 상태는 최소한 다음 상태를 표현할 수 있어야 한다.

- `pending`
- `in_progress`
- `processed`
- `wiki_built`
- `graph_built`
- `derived_wiki_built`
- `error`

실패 기록 필드 권장:

- `error_stage`
- `error_message`
- `retry_count`
- `last_attempt_at`
- `last_success_at`

실패 stage 예시:

- `extract`
- `ingest`
- `compile_wiki`
- `fts_index`
- `graph_build`
- `derived_wiki_generate`

## 15. Acceptance Criteria

v0.6 완료 조건은 다음과 같다.

1. `.txt`, `.md`, `.html`, `.htm`, `.csv`, `.xlsx` source를 등록하고 처리할 수 있다.
2. 지원하지 않는 확장자는 명확한 error 상태로 남는다.
3. pending source 여러 개를 `process_pending_sources.py`로 일괄 처리할 수 있다.
4. source 처리 성공 시 source summary, FTS, graph가 갱신된다.
5. 직업별 derived wiki 문서를 생성할 수 있다.
6. `wiki/jobs/gunbreaker.md` 같은 파일이 실제로 생성된다.
7. 직업별 derived wiki 문서는 patch version과 source_id를 보존한다.
8. FTS 검색 대상에 `wiki/jobs/*.md`가 포함된다.
9. “7.x 건브레이커 변경 이력” 같은 질문이 source summaries 20개를 직접 뒤지는 방식이 아니라, job wiki 문서를 우선 참조할 수 있는 구조가 된다.
10. 모든 주요 기능에 regression test가 있다.

## 16. 테스트 계획

필수 테스트:

- txt extractor가 원문을 그대로 추출하는지
- markdown extractor가 heading 구조를 유지하는지
- html extractor가 script/style/nav/footer를 제거하는지
- csv extractor가 header와 row를 보존하는지
- xlsx extractor가 single sheet를 추출하는지
- xlsx extractor가 multi sheet를 추출하는지
- unsupported extension이 error 상태로 기록되는지
- pending loop가 성공한 source를 processed 계열 상태로 변경하는지
- pending loop가 실패한 source의 retry_count를 증가시키는지
- generated job wiki가 `wiki/jobs/<job>.md`에 저장되는지
- job wiki가 source_id와 patch version을 포함하는지
- FTS가 source_summaries와 jobs wiki를 모두 인덱싱하는지

## 17. Task Breakdown

### v06-1. Extension detection and extractor interface

- source path에서 extension 판별
- ExtractedSource 모델 정의
- extractor 공통 interface 정의

### v06-2. Extractor registry

- extension -> extractor mapping 구현
- unsupported extension error 정의

### v06-3. Text, Markdown, HTML extractor

- `.txt`, `.md`, `.html`, `.htm` 처리 구현
- HTML noise 제거 규칙 테스트

### v06-4. CSV extractor

- CSV를 Markdown table 또는 structured text로 변환
- header 보존 테스트

### v06-5. XLSX extractor

- 표준 라이브러리 기반 workbook zip/XML parsing
- sheet별 heading 생성
- empty sheet 처리
- multi sheet 테스트

### v06-6. Pending source loop

- pending source 조회
- limit, dry-run, retry-errors 옵션
- 상태 전이 및 실패 기록

### v06-7. Process source integration

- 기존 `process_source.py`와 extractor layer 연결
- ingest, compile_wiki, FTS, graph 단계 순서 보장

### v06-8. Derived wiki generator foundation

- source summaries 로딩
- patch version, source_id, topic metadata 수집
- derived wiki output writer 구현

### v06-9. Job wiki generator

- 직업 목록 정의
- 직업별 관련 summary 수집
- `wiki/jobs/<job>.md` 생성
- patch별 변경 이력 template 적용

### v06-10. FTS indexing expansion

- source_summaries 외에 jobs wiki도 인덱싱
- wiki_type/topic metadata 추가
- Official FFXIV job guide source_summary는 `job` metadata를 해당 job slug로 저장한다.
- 일반 source_summary는 파일 stem을 job metadata로 오인하지 않는다.

### v06-11. Regression tests

- extractor tests
- pending loop tests
- job wiki generation tests
- FTS indexing tests

### v06-12. Documentation update

- README 업데이트
- CLI 사용법 문서화
- CURRENT_HANDOFF 업데이트

## 18. 구현 원칙

- `process_source.py`에 확장자별 세부 로직을 직접 몰아넣지 않는다.
- extractor는 독립적으로 테스트 가능해야 한다.
- derived wiki generation은 source processing과 분리한다.
- source summary는 원본 source의 1차 요약이다.
- derived wiki는 여러 source summary를 읽어 주제별로 재구성한 2차 산출물이다.
- 정보가 불확실하면 derived wiki에 확정 문장으로 쓰지 않는다.
- 모든 derived wiki 항목은 가능한 한 source_id를 가진다.

## 19. 최종 기대효과

v0.6이 완료되면 시스템은 다음 상태가 된다.

- 다양한 파일 형식의 원본 자료를 그대로 저장하고 처리할 수 있다.
- source별 요약만 있는 상태에서 벗어나 주제별 wiki 문서를 자동 생성할 수 있다.
- 직업별 변경 이력 질문에 대해 매번 여러 패치노트를 실시간으로 병합하지 않아도 된다.
- 이후 Discord command, scheduler, watcher를 붙일 때 내부 파이프라인이 단순해진다.
- `ffxiv-claw-bot`가 단순 검색 도구에서 누적 지식 베이스에 가까워진다.

## 20. 요약

v0.6은 단순한 자동 처리 루프가 아니다.

정확한 목표는 다음이다.

다양한 source 파일을 자동으로 정규화하고,

source 단위 요약을 만든 뒤,

다시 직업별/주제별 derived wiki로 재구성하는 파이프라인을 구축한다.

1차 구현 우선순위는 다음이다.

multi-format extractor

-> pending source loop

-> source_summaries 안정화

-> job wiki generator

-> jobs wiki FTS indexing
