# ADR 0001: Use SQLite FTS Before Vector DB

## Status

Accepted

## Context

FFXIV 지식 검색은 patch, job, raid, skill, item, macro 같은 고유명사를 많이 다룬다.

초기 MVP에서 embedding과 vector DB를 도입하면 모델 선택, 인덱스 운영, 재색인, 비용, 테스트 복잡도가 함께 늘어난다.

## Decision

초기 버전에서는 vector DB나 embedding을 쓰지 않고 SQLite FTS5 + metadata + graph traversal을 먼저 사용한다.

## Consequences

좋은 영향:

- 초기 구현이 가볍다.
- 로컬에서 실행하기 쉽다.
- embedding 모델 운영 비용이 없다.
- keyword/metadata 기반 검색은 테스트하기 쉽다.

트레이드오프:

- 의미 기반 검색이 약할 수 있다.
- 표현이 다른 자연어 질문의 recall이 낮을 수 있다.

필요성이 확인되면 v0.4 이후 embedding/vector DB를 검토한다.
