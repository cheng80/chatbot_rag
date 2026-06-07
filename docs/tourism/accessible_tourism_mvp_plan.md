# 무장애·가족 친화 관광정보 AI 챗봇 MVP 플랜

## 1. 결정

1차 주제는 **무장애·가족 친화 관광정보 AI 챗봇**으로 진행한다.

2차 대안은 **반려동물 동반 관광정보 AI 챗봇**으로 둔다. 단, 2차 전환은 한국관광공사 무장애 여행 정보에서 접근성·영유아 가족 관련 필드를 안정적으로 확보하지 못할 때만 검토한다.

## 2. 스킬 진행 결과

### `/plan-ceo-review`

추천 모드: **SELECTIVE EXPANSION**

이유:

- 기존 로컬 RAG 챗봇은 이미 동작한다.
- 공모전용 서비스 방향은 정해졌지만, 데이터 확보 가능성과 MVP 범위는 아직 좁혀야 한다.
- 과한 기능 확장보다 “공공데이터 기반 근거 답변 + 관광지 카드”를 확실히 만드는 것이 심사 대응에 유리하다.

제품 포지션:

```text
장애인, 고령자, 유아 동반 가족이 관광지를 찾을 때 필요한 접근성 정보를
한국관광공사 OpenAPI와 RAG로 근거 기반 상담 형태로 제공하는 AI 챗봇
```

1차 성공 기준:

- 사용자가 자연어로 지역과 조건을 말하면 기본 관광지 3~5개를 추천한다.
- 후보가 5개보다 많으면 후속 질문 버튼으로 `더 보기`를 제공하고, 사용자가 요청하면 확인된 후보를 가능한 만큼 보여준다.
- 각 추천에는 접근성 또는 가족 친화 근거가 포함된다.
- 관광지 카드에는 출처, 주소, 이미지, 전화번호, 핵심 편의정보가 표시된다.
- 문서나 API에 없는 내용은 추측하지 않는다.
- 시군구 결과가 부족할 때 의미 없는 타 지역 추천을 자동으로 섞지 않는다. “근처/주변/가까운/인근”은 해당 시군구 안의 가까운 후보 선호로 처리하고, 사용자가 “서울 전체로 넓혀줘”, “범위 넓혀줘”처럼 명시적으로 요청한 경우에만 상위 광역 지역으로 넓힌다.
- `아빠`, `어머니`, `부모님` 같은 관계 호칭만으로 나이를 추정하지 않는다. 휠체어 이용자와 고령자는 별도 조건으로 취급한다.

NOT in scope:

- 여행 일정 자동 생성
- 로그인/회원 기능
- 결제/예약
- 전체 관광 데이터 대량 운영 파이프라인
- 다국어 응답
- 지도 기반 경로 최적화

### `/plan-eng-review`

핵심 구현 흐름:

```text
사용자 질문
  -> 지역/조건/확장 의도 구조화
  -> 동명이 지역이면 지역 선택 후보 반환
  -> 이전 live 조회 Markdown 캐시 확인
  -> Chroma 색인과 로컬 Markdown fallback 확인
  -> TourAPI areaBasedList2 후보 소량 조회
  -> 상위 후보 detailCommon2 + detailWithTour2 조회
  -> 응답 정규화
  -> 필요 시 LLM 추론 보조로 후보 재랭킹/재질문/상담 문장 정리
  -> live 결과를 live_markdown에 저장
  -> 답변 + 관광지 카드 + 출처 + 진단 정보 반환
```

권장 1차 구현 접근:

```text
`/tourism/chat`은 지역이 확정되면 이전 live 조회 Markdown 캐시를 먼저 확인한다.
live 캐시에 없으면 Chroma 색인과 로컬 Markdown fallback을 확인한다.
그래도 같은 지역 카드가 없고 API 키가 있으면 live TourAPI 후보 조회를 사용한다.
반복 요청은 프로세스 메모리 캐시와 `data/generated/tour_api/live_markdown/` Markdown 캐시로 줄인다.
`data/raw/tourism_accessible/`는 계획 수집한 fallback/색인 후보로 유지하고,
데이터 신선도는 MVP 이후 주기적 갱신 배치로 해결한다.
```

이유:

- 저장된 live 캐시, Chroma, Markdown fallback을 먼저 써서 일일 호출량을 줄인다.
- fallback에 없는 지역만 live API로 보강해 지역 커버리지를 넓힌다.
- 저장된 샘플/Chroma fallback을 유지해 API 장애 중에도 시연 가능성을 남긴다.
- OpenAPI에 없는 편의정보는 여전히 추측하지 않고 `확인 필요`로 남긴다.
- LLM 추론 보조는 데이터를 새로 만드는 단계가 아니라, 이미 확인된 후보를 복합 사용자 상황에 맞게 정리하는 보조 단계로 제한한다.

추론 보조 사용 기준:

- 명확한 지역/조건/동명이 지역 선택/조회 순서는 규칙 기반과 cache/Chroma/API로 처리한다.
- `오래 걷기 힘든 분`, `비 오면 편한 곳`, `너무 붐비지 않는 곳`, `아이랑 쉬기 좋은 곳`처럼 상황 설명이 섞이면 후보 카드 생성 뒤 LLM 추론 보조를 검토한다.
- `강남구 바닷가`처럼 잘못된 전제는 없는 후보를 만들지 않고, 필요하면 대체 질문이나 조건 완화 제안만 생성한다.
- LLM은 `TourismPlaceCard`에 없는 접근성 정보를 단정하지 않는다.
- 현재 기본 SuperGemma GGUF 모델은 Gemma 4 기반 8B급이지만 Ollama native `think=true`를 지원하지 않는 것으로 확인됐다. 2026-05-15 1차 벤치마크에서는 공식 `gemma4:e4b`와 `huihui_ai/gemma-4-abliterated:e4b`가 native thinking을 반환했지만 30초 이상 지연돼 MVP 기본값으로는 보류했다. `qwen3:4b`는 thinking capability가 있으나 현재 프롬프트 계약을 지키지 못했다.

새 구성 요소:

```text
app/services/tour_api_service.py
  - 한국관광공사 OpenAPI 호출
  - timeout, HTTP error, malformed response 처리

app/services/tourism_query_service.py
  - 지역, 동행자, 접근성 조건, 카테고리 추출
  - 초기 버전은 규칙 기반 + LLM 보조 가능

app/services/tourism_normalizer.py
  - TourAPI 응답을 내부 표준 관광지 카드 구조로 변환

app/schemas/tourism.py
  - TourismPlaceCard
  - AccessibilityInfo
  - TourismChatResponse 확장용 schema

scripts/fetch_accessible_tourism_samples.py
  - 지역/키워드별 샘플 수집
  - 접근성 필드가 확인된 항목만 `data/raw/tourism_accessible/*.md` 생성
  - API 원본/진단 JSON은 `data/generated/tour_api/`에 저장

scripts/fetch_tour_area_codes.py
  - `KorWithService2/areaCode2`로 전국 광역/시군구 코드를 수집
  - `data/processed/tour_area_codes.json` 캐시 생성
  - 중복되는 시군구 별칭은 자동 매핑에서 제외
```

기존 재사용:

- `EmbeddingService`
- `VectorStore`
- `Retriever`
- `PromptBuilder`
- `LLMService`
- `RAGService`
- `scripts/rebuild_index.py`
- `notebooks/model_comparison_template.ipynb`

API 설계:

```text
POST /tourism/chat
  request:
    message: string
    session_id?: string

  response:
    answer: string
    cards: TourismPlaceCard[]
    sources: Source[]
    lookup_mode: "cache" | "live" | "indexed" | "sample" | "clarification" | "unknown"
    degraded: boolean
    warnings: string[]
    suggested_messages: string[]
    reasoning_assist_used: boolean
    reasoning_assist_notes: string[]
```

MVP에서는 기존 `/chat`을 유지하고 `/tourism/chat`을 별도 추가하는 쪽을 권장한다. 기존 일반 RAG 테스트와 관광 챗봇 테스트를 분리할 수 있기 때문이다.

응답 이벤트는 `data/generated/tour_api/query_card_events.jsonl`에 JSONL로 기록한다. 기본값은 원문 질문을 저장하지 않고 `message_hash`만 저장하며, 필요할 때만 `TOURISM_QUERY_EVENT_LOG_INCLUDE_MESSAGE=true`로 원문 저장을 켠다. 이벤트 로그 분석은 `notebooks/tourism_event_log_analysis.ipynb`에서 수행한다. 이 노트북은 `matplotlib` 차트와 한글 폰트 설정을 포함한다. 이벤트 양이 많아지거나 대시보드가 필요해지면 Post-MVP에서 SQLite로 흡수한다.

실패 처리:

| 실패 | 처리 |
|---|---|
| TourAPI 키 없음 | live 조회를 건너뛰고 cache/Chroma/로컬 샘플 fallback |
| TourAPI timeout/쿼터 | `degraded=true`, `warnings` 진단, 기존 캐시/로컬 샘플 유지 |
| 결과 없음 | “조건에 맞는 관광지를 확인하지 못했습니다” + 조건 완화 제안 |
| 시군구 결과 3개 미만 | 자동 확장하지 않고 확인된 결과만 반환 + 명시적 상위 지역 확장 제안 |
| 명시적 범위 확장 요청 | `서울 전체로 넓혀줘`, `범위 넓혀줘`처럼 말한 경우만 상위 광역 지역 후보 포함 + 답변에 확장 사실 명시 |
| 중구/남구 등 동명이 시군구 단독 입력 | 추천을 생성하지 않고 광역 지역 선택 후보와 `suggested_messages` 반환 |
| 접근성 필드 누락 | 누락을 명시하고 추측하지 않음 |
| Retriever/Ollama/Chroma 실패 | live TourAPI 또는 로컬 샘플 fallback + `degraded=true` + `warnings` 진단 |
| API 내부 예외 | 원문 예외를 노출하지 않고 안정적인 오류 code/message 반환 |
| 지역 코드 캐시 누락/손상 | fallback은 유지하되 `warnings`로 캐시 상태를 노출 |

테스트 범위:

- 질문 조건 추출 단위 테스트
- TourAPI 응답 정규화 단위 테스트
- 접근성 필드 누락 테스트
- `/tourism/chat` 통합 테스트
- Ollama 없는 환경을 위한 mock 서비스 테스트
- card Markdown codec round-trip 테스트
- safe error response 테스트
- degraded fallback 및 지역 코드 캐시 진단 테스트
- 동명이 시군구 단독 입력은 지역 선택 안내를 반환하고, 광역+시군구 입력은 해당 시군구로 확정하는 테스트

### `/plan-design-review`

디자인 방향:

```text
조용하고 실용적인 관광 상담 도구
```

첫 화면은 랜딩 페이지가 아니라 바로 사용 가능한 챗봇 화면이 좋다.

핵심 화면:

1. 챗봇 화면
2. 관광지 카드 리스트
3. 관광지 상세 정보
4. 조건 필터 패널

카드 필수 정보:

- 관광지명
- 주소
- 대표 이미지
- 추천 이유
- 접근성/가족 친화 태그
- 전화번호 또는 문의 정보
- 출처: 한국관광공사 OpenAPI

접근성 태그 예시:

```text
휠체어 접근
장애인 주차
유모차 대여
수유실
영유아 동반
고령자 추천
실내 활동
```

UI 원칙:

- 답변 텍스트보다 카드의 근거 정보가 더 잘 보여야 한다.
- 접근성 정보는 아이콘+짧은 라벨로 스캔 가능하게 한다.
- “확인 필요” 상태를 숨기지 않는다.
- 모바일에서 카드 1열, 데스크톱에서 2열까지 허용한다.

## 3. 1차 구현 순서

1. TourAPI 키/환경변수 정리
2. 무장애 여행 정보 API 샘플 호출 스크립트 작성
3. 샘플 응답을 상대 경로로 저장한다. RAG용 Markdown은 `data/raw/tourism_accessible/`, API 진단 JSON은 `data/generated/tour_api/`에 둔다.
4. 정규화 schema와 normalizer 작성
5. 관광 데이터 markdown 또는 JSON-to-text 변환 후 Chroma 재색인
6. `/tourism/chat` 엔드포인트 추가
7. `/tourism/chat`에서 질문 구조화 후 live TourAPI 후보 조회를 우선 사용
8. TourAPI 실패/쿼터/결과 없음 시 Chroma와 로컬 Markdown fallback 유지
9. 관광지 카드 응답 schema 추가
10. 공모전용 질문 20개 평가셋 작성 (별도 TODO)
11. 현재 기본 Unsloth Gemma4, 이전 SuperGemma4, `gemma3` 비교 실행 (별도 TODO)
12. Flutter 또는 간단한 web client에서 챗봇+카드 표시 (별도 TODO)

## 4. 2차 대안 전환 기준

반려동물 동반 관광정보 챗봇으로 전환하는 기준:

- 무장애 API에서 접근성 필드가 실제 응답에 거의 없다.
- 지역별 결과가 너무 적어 추천 품질이 떨어진다.
- 영유아/가족 친화 정보가 카드 근거로 쓰기 어렵다.
- OpenAPI 인증이나 호출 제한 때문에 MVP 시연 안정성이 낮다.

전환하지 않는 기준:

- 접근성 필드가 일부 누락되어도 “확인 필요”로 명시 가능하다.
- 최소 3개 지역에서 추천 카드 3개 이상을 만들 수 있다.
- 출처와 근거 문장을 안정적으로 구성할 수 있다.

## 5. 바로 다음 작업

다음 작업은 구현 전 데이터 검증이다.

```bash
python scripts/fetch_accessible_tourism_samples.py
```

이 스크립트가 해야 할 일:

- 서울, 부산, 강릉 등 3개 지역 샘플 조회
- 휠체어/유모차/고령자/아이 동반 관련 필드 존재 여부 출력
- 결과를 `data/raw/tourism_accessible/`에 저장
- 접근성 필드가 없는 기본 관광정보는 RAG용 Markdown으로 저장하지 않는다.
- “1차 진행 가능 / 2차 검토 필요” 판정 요약 출력

현재 확인된 API 상태:

- `KorService2`의 `areaCode2`, `searchKeyword2`, `areaBasedList2`는 200 OK로 호출 가능하다.
- `areaBasedList2`에는 `listYN=Y`를 넣지 않는다.
- `KorWithService2`의 `areaCode2`, `areaBasedList2`, `detailWithTour2`는 승인 반영 후 200 OK로 호출 가능하다.
- 전국 시군구 코드는 수동 하드코딩하지 않고 `data/processed/tour_area_codes.json` 캐시로 관리한다.
- 2026-05-15 기준 수집 스크립트 기본값은 서울/부산/강릉 각 20건, 실행당 최대 150 API 호출로 조정했다.
- curated 무장애·가족 친화 Markdown 샘플은 API 실패 대비와 테스트 fallback으로 유지한다.
- 2026-05-15 기준 `/tourism/chat`은 지역이 확정되고 API 키가 있으면 live TourAPI 후보 조회를 먼저 사용하고, 실패 시 Chroma/Markdown fallback을 사용한다.
- 2026-05-18 기준 시군구 추천 정책을 조정했다. 강남구 단독 질문과 강남구 근처 질문은 강남구 결과와 부족 안내를 우선 반환하고, `서울 전체로 넓혀줘`처럼 명시적 확장 요청이 있을 때만 서울 범위 후보를 포함한다.
- 2026-05-15 기준 동명이 시군구 선택 정책을 반영했다. `중구` 단독 질문은 추천 대신 서울/인천/대전/대구/부산/울산 중구 후속 질문 후보를 반환하고, `부산 중구`처럼 광역을 함께 말하면 해당 시군구로 확정한다.
- 2026-05-15 기준 관계 호칭과 접근성 조건을 분리했다. `휠체어 타는 아빠`는 휠체어 조건만 사용하고, 고령자 조건은 `고령자/어르신/노인`처럼 명시될 때만 사용한다.

## 6. 권장 다음 스킬

이 문서 기준 다음 순서는 다음과 같다.

```text
1. /plan-eng-review
2. 구현
3. /qa
4. /plan-design-review 또는 /design-review
5. /review
```

이미 제품 방향은 1차로 확정했으므로, 다음 세션에서는 `/plan-eng-review`로 API 계약과 데이터 모델을 더 잠근 뒤 구현에 들어간다.
