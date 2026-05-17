# Specs

spec은 현재 시스템 동작 계약이다. 테스트와 구현은 spec을 기준으로 작성한다.

spec은 과거 계획이 아니라 현재 유효한 기준이다. 큰 구현 변경은 먼저 spec을 갱신하거나 새 spec을 작성한 뒤 진행한다.

## 규칙

- spec 없이 구현을 크게 바꾸지 않는다.
- spec은 구현이 따라야 하는 입력, 출력, 저장 규칙, 성공 기준을 정의한다.
- 확실하지 않은 내용은 추측하지 않고 `TODO`로 표시한다.
- 코드 변경과 spec 변경이 함께 필요하면 같은 작업 단위에서 관리한다.
- Notion에 있는 설명보다 레포의 `docs/specs/*.md`를 우선한다.

## 현재 spec

- `0001-local-kb-pipeline.md`: v0.1 local KB pipeline
- `0002-graph-layer.md`: v0.2 graph layer
- `0003-google-drive-sync.md`: v0.3 Google Drive sync
- `0004-v05-source-processing-pipeline.md`: v0.5 source processing pipeline
- `0004a-v05.1-source-processing-hardening.md`: v05.1 source processing hardening
- `0005- v06-Multi-format-Source-Processing.md`: v0.6 multi-format source processing
- `0007-v07-grounded-ask-pipeline.md`: v0.7 grounded ask pipeline
- `0008-v08-ffxiv-domain-graphify-layer-spec.md`: v0.8 FFXIV domain graphify layer
- `0009-v08_5_managed_wiki_kb_activation_spec.md`: v0.8.5 managed wiki KB activation
- `0010-openclaw-usecase-skill-routing.md`: OpenClaw use-case skill routing

## 기존 참고 문서

아래 문서는 이전 단계에서 작성된 참고 문서다. 현재 구현 계약은 `0001`부터 시작하는 spec을 우선한다.

- `01-architecture.md`
- `02-tools.md`
- `03-roadmap.md`
- `04-handoff-search-kb.md`
- `05-task-compile-wiki.md`
- `06-log-ingest-url.md`
- `07-log-compile-wiki.md`
- `2026-05-14-graph-layer-design.md`
