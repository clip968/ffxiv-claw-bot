# v0.5-02 Plan: OpenClaw Source Processing Skill Draft

## Goal

OpenClaw가 사용자의 source 처리 요청을 안정적으로 해석하고, process_source.py를 호출할 수 있도록 skill-level workflow를 문서화한다.

이번 task의 결과물은 실제 Python 실행기가 아니라 OpenClaw가 따라야 할 운영 규칙이다.

## Background

현재 OpenClaw는 ingest_local.py, local_rebuild.py, status_notification.py, Notion update를 여러 단계로 직접 호출해야 한다.

v0.5에서는 OpenClaw가 다음 역할만 담당하도록 줄인다.

- 사용자 요청 해석
- source_type 판단
- category 판단
- title/body/url/local_path 구성
- process_source.py 호출
- stdout JSON 해석
- Notion update 실행
- 사용자 보고

실제 ingest/rebuild/status payload 생성은 process_source.py가 담당한다.

## Scope

이번 task에서 작성할 문서:

docs/skills/ffxiv-source-processing.md

이 문서는 OpenClaw 전용 skill 문서로 사용한다.

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- process_source.py 구현
- fetch_url.py 구현
- Notion polling 구현
- crawler 구현
- scheduler 구현
- Discord command 구현

## Files to Add

docs/skills/ffxiv-source-processing.md

## Files to Update

agent.md
CLAUDE.md
docs/WORKFLOW.md
docs/handoff/CURRENT_HANDOFF.md

## Skill Responsibility

OpenClaw Source Processing Skill은 다음 책임을 가진다.

1. 사용자 요청에서 source를 식별한다.
2. source_type을 결정한다.
3. category를 결정한다.
4. title을 정리한다.
5. 필요한 인자를 구성한다.
6. process_source.py를 호출한다.
7. 결과 JSON을 파싱한다.
8. notion_update payload가 있으면 Notion DB를 갱신한다.
9. 사용자에게 결과를 요약한다.

## Source Type Decision Rules

### URL

사용자 메시지에 http 또는 https URL이 포함되어 있으면 source_type=url로 처리한다.

예시:

사용자 요청:
이 URL을 patch_notes로 저장해줘. https://example.com/patch-note

OpenClaw 판단:
source_type=url
category=patch_notes
url=https://example.com/patch-note

실행:
python tools/process_source.py --apply --source-type url --category patch_notes --url "https://example.com/patch-note"

### Text Note

사용자가 직접 본문을 제공하고 파일 경로나 URL이 없으면 source_type=text_note로 처리한다.

예시:

사용자 요청:
이 내용을 personal_notes로 저장해줘. P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다.

OpenClaw 판단:
source_type=text_note
category=personal_notes
body=P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다.

실행:
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "P12S Reprisal note" --body "P12S에서는 raidwide 전에 Reprisal을 먼저 사용한다."

### Markdown File

사용자 메시지에 .md 파일 경로가 있으면 source_type=markdown_file로 처리한다.

예시:

사용자 요청:
/mnt/d/ffixiv-bot-storage/incoming/p12s.md 이걸 raid_guides로 넣어줘.

OpenClaw 판단:
source_type=markdown_file
category=raid_guides
local_path=/mnt/d/ffixiv-bot-storage/incoming/p12s.md

실행:
python tools/process_source.py --apply --source-type markdown_file --category raid_guides --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"

### Plain Text File

사용자 메시지에 .txt 파일 경로가 있으면 source_type=plain_text_file로 처리한다.

실행:
python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/path/to/file.txt"

### Binary Attachment

.md 또는 .txt가 아닌 파일은 source_type=binary_attachment 후보로 판단한다.

v0.5에서는 binary_attachment의 완전 자동 처리 범위가 제한되어 있으므로, OpenClaw는 사용자에게 확인해야 한다.

예시 확인 질문:
이 파일은 markdown/text가 아니므로 v0.5에서는 자동 내용 추출이 제한될 수 있습니다. 첨부 파일로 등록만 할까요, 아니면 텍스트로 변환한 내용을 직접 제공하시겠습니까?

## Category Decision Rules

지원 category:

- urls
- documents
- sheets
- patch_notes
- raid_guides
- job_guides
- static_docs
- macros
- bis_sheets
- personal_notes

판단 규칙:

패치노트, 업데이트, hotfix, Lodestone patch 관련 요청:
category=patch_notes

레이드 공략, 기믹, 타임라인, mitigation, savage, ultimate 관련 요청:
category=raid_guides

직업 가이드, opener, rotation, job, BIS가 아닌 운용법 관련 요청:
category=job_guides

매크로, macro, party finder macro 관련 요청:
category=macros

BIS, gearset, meld, sheet 관련 요청:
category=bis_sheets

사용자 개인 메모, 임시 기록, 출처가 불명확한 수동 기록:
category=personal_notes

category가 불명확하면 실행하지 말고 질문한다.

## Ambiguity Handling

다음 경우에는 바로 실행하지 않는다.

- category가 명확하지 않다.
- URL인지 일반 텍스트인지 불명확하다.
- 파일 경로가 존재하는지 확인할 수 없다.
- source_type을 결정할 수 없다.
- 사용자가 “최신 정보 찾아서 넣어줘”라고 했지만 source를 제공하지 않았다.
- binary file을 자동 처리해야 하는지 명확하지 않다.

질문 예시:

이 source를 어떤 category로 저장할까요? 선택지는 patch_notes, raid_guides, job_guides, macros, bis_sheets, personal_notes입니다.

## process_source.py Call Rules

process_source.py가 존재하면 OpenClaw는 기존 개별 tool 호출보다 process_source.py를 우선 사용한다.

기본 실행 형식:

python tools/process_source.py --apply --source-type SOURCE_TYPE --category CATEGORY ...

dry-run 요청이 있으면:

python tools/process_source.py --dry-run --source-type SOURCE_TYPE --category CATEGORY ...

OpenClaw는 process_source.py stdout의 JSON만 신뢰한다.

## Notion Update Rules

process_source.py 결과 JSON에 notion_update가 포함되어 있으면 OpenClaw는 Notion DB를 갱신한다.

OpenClaw가 Notion에 넣어도 되는 값:

- Status
- Graph Status
- Source ID
- Local Source Path
- Wiki Path
- Last Processed
- Last Error
- Next Action

OpenClaw가 Notion에 넣으면 안 되는 값:

- 원문 body 전체
- 대형 attachment data
- raw binary content
- raw HTML 전체
- 불필요한 absolute path

## User Report Format

성공 시:

처리 완료.
status: ok
source_id: ...
graph_status: built
wiki_path: ...
Notion 상태를 Graph Built로 갱신했습니다.

부분 실패 시:

부분 처리 완료.
source_id: ...
status: partial
graph_status: failed
실패 단계: ...
다음 조치: ...

실패 시:

처리 실패.
status: error
실패 단계: ...
원인: ...
다음 조치: ...

## Tests

이번 task는 문서 중심이므로 Python unit test는 필수는 아니다.

대신 다음 smoke scenario를 문서에 포함해야 한다.

1. URL 요청을 process_source.py 명령으로 변환
2. text_note 요청을 process_source.py 명령으로 변환
3. markdown_file 요청을 process_source.py 명령으로 변환
4. category가 불명확한 요청에서 질문
5. source가 없는 “최신 정보 찾아줘” 요청에서 v0.6 범위로 안내

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- docs/skills/ffxiv-source-processing.md가 존재한다.
- source_type 판단 규칙이 문서화되어 있다.
- category 판단 규칙이 문서화되어 있다.
- ambiguity handling이 문서화되어 있다.
- process_source.py 우선 호출 규칙이 문서화되어 있다.
- Notion update payload 사용 규칙이 문서화되어 있다.
- agent.md 또는 CLAUDE.md에서 이 skill 문서를 참조한다.

## Verification

문서 변경 후 다음을 실행한다.

python scripts/check_docs_freshness.py --all

가능하면 다음도 실행한다.

python scripts/finish_task.py --skip-notion-dry-run

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. skill에서 판단 가능한 source_type
3. skill에서 판단 가능한 category
4. 남은 제한 사항