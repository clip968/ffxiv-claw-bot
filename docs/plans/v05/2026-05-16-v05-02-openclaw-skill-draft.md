# v0.5-02: OpenClaw Skill Draft

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Skill directory: `docs/skills/`

## Status

**Pending**

## Goal

OpenClaw가 source 처리 요청을 받았을 때 `process_source.py`를 올바르게 호출할 수 있도록 skill 문서를 작성한다.

## Scope

- Skill name / trigger 조건 정의
- Skill responsibility 정의: 사용자 요청 해석 → source type 결정 → category 결정 → title 정리 → 인자 구성 → `process_source.py` 호출
- Source type 판단 규칙: URL → url, 텍스트 메모 → text_note, .md 파일 → markdown_file, .txt → plain_text_file, 기타 → binary_attachment
- Category 판단 규칙: patch_notes, raid_guides, job_guides, macros, personal_notes 등
- Ambiguity handling: category 불명확 시 질문, 파일 미존재 시 질문, source type 불명확 시 질문
- `process_source.py` 우선 호출 규칙: 존재하면 개별 tool 호출 대신 process_source.py 사용
- Output JSON 파싱 및 사용자 보고 포맷
- Notion update: notion_update payload가 있으면 Notion API로 DB 갱신

Out of scope:

- `process_source.py` 구현
- Notion API 호출 구현
- 실제 URL fetch 구현

## Red Test

N/A (documentation-only)

## Checklist

- [ ] `docs/skills/` 디렉터리 존재 확인
- [ ] 기존 skill 파일(SKILL.md 등) 패턴 확인 (AGENTS.md, SKILL.md, TOOLS.md 구조)
- [ ] Skill 문서가 CLAUDE.md와 AGENTS.md에서 참조 가능한 구조인지 확인
- [ ] 기존 v0.4 skill과 충돌하지 않는지 확인
- [ ] `docs/skills/ffxiv-source-processing.md` 작성:
  - [ ] Skill name / trigger 조건
  - [ ] Source type 판단 규칙
  - [ ] Category 판단 규칙
  - [ ] Ambiguity handling
  - [ ] `process_source.py` 호출 규칙
  - [ ] Output JSON 파싱
  - [ ] Notion update 규칙

## Verification

```bash
# 문서 구조 확인
ls docs/skills/ffxiv-source-processing.md
# v0.4 skill과 충돌 확인
grep -r "process_source" docs/skills/ --include="*.md"
```
