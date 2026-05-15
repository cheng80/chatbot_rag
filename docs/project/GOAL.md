# GOAL

무장애·가족 친화 관광정보 AI 챗봇 MVP를 완성한다.

## 완성 기준

1. 한국관광공사 무장애 여행 정보 OpenAPI를 질문 시점에 소량 조회할 수 있다.
2. 조회 결과를 정규화해 관광지 카드로 반환하고, 필요하면 RAG 색인/로컬 샘플 fallback을 사용할 수 있다.
3. 사용자가 자연어로 질문하면 기본 관광지 3~5개를 추천한다. 후보가 더 있으면 `더 보기` 후속 질문을 제공하고, 사용자가 원하면 확인된 후보를 가능한 만큼 보여준다.
4. 답변에는 접근성·가족 친화 근거와 출처가 포함된다.
5. 관광지 카드 응답 schema가 있다.
6. pytest와 기본 API 스모크 테스트가 통과한다.

단, 시군구처럼 좁은 지역을 사용자가 명시한 경우에는 추천 품질을 위해 자동 확장하지 않는다. 해당 시군구에서 3개 미만만 확인되면 부족 안내와 함께 확인된 결과만 제공한다. 사용자가 `근처`, `주변`, `가까운`, `인근`처럼 확장 의도를 밝힌 경우에만 상위 광역 지역 후보를 함께 포함한다.

## 진행 원칙

- 1차 주제는 무장애·가족 친화 관광정보 챗봇이다.
- 2026-06-10 전까지 앱보다 기본 서비스 완성을 우선한다. 기본 서비스는 `/tourism/chat`, `/tourism-ui/`, Swagger, Cloudflare 터널 시연으로 검증한다.
- 일반 관광 추천은 TourAPI 기본 관광정보를 통해 기반상 가능하지만, MVP의 검증 범위는 무장애·가족 친화 조건 중심 추천으로 제한한다.
- 병원/약국/응급의료기관 API 결합은 “여행 안전 지원” 후속 확장으로 검토한다. MVP에서는 의료 판단이나 증상 기반 추천을 하지 않는다.
- 데이터 수집이 어렵거나 접근성/영유아 가족 관련 필드가 부족하면 2차 대안으로 반려동물 동반 관광정보 챗봇을 검토한다.
- Anaconda/conda는 사용하지 않는다.
- 프로젝트 `.venv`를 사용한다.
- 경로는 항상 프로젝트 상대 경로를 우선한다.
- 구현 전후로 gstack 스킬을 `/plan-ceo-review` -> `/plan-eng-review` -> `/plan-design-review` -> `/qa` -> `/review` 순서로 활용한다.

## 현재 우선순위

1. 한국관광공사 국문 관광정보 서비스_GW live 후보 조회 흐름을 기준으로 TourAPI 연결을 안정화한다.
2. 무장애/접근성 상세 정보는 국문 관광정보 서비스_GW의 기본 관광정보와 무장애 여행 정보 API를 분리해 검증한다.
3. 수집 응답에서 접근성·영유아 가족 관련 필드 존재 여부를 확인한다.
4. 진행 가능하면 TourAPI 응답 정규화와 RAG 색인 흐름을 구현한다.
5. 부족하면 반려동물 동반 관광정보 API/데이터 가능성 검토한다.

## 현재 API 확인 메모

- 공공데이터포털 참고 주소: https://www.data.go.kr/data/15101578/openapi.do
- `.env`에는 `TOUR_API_SERVICE_KEY`, `TOUR_API_ACCESSIBLE_SERVICE_KEY`, `TOUR_API_BASE_URL`, `TOUR_API_ACCESSIBLE_BASE_URL`, `TOUR_API_MOBILE_OS`, `TOUR_API_MOBILE_APP`, `TOUR_API_TIMEOUT`, `TOURISM_SAMPLE_PATH`를 둔다.
- 현재 공공데이터포털 인증키는 하나이며, 서비스별 설정 분리를 위해 `TOUR_API_SERVICE_KEY`와 `TOUR_API_ACCESSIBLE_SERVICE_KEY`에 같은 키를 넣어 둔다.
- 국문 관광정보 서비스_GW 기본 URL은 `https://apis.data.go.kr/B551011/KorService2`이다.
- 기본 목록/검색/공통 상세 조회용 `KorService2`를 코드에서 `KorWithService2`로 강제 치환하지 않는다.
- 무장애 상세 조회가 필요하면 별도 `TOUR_API_ACCESSIBLE_BASE_URL=https://apis.data.go.kr/B551011/KorWithService2`를 사용한다.
- 2026-05-15 재테스트 결과 `areaCode2`, `searchKeyword2`, `areaBasedList2` 호출은 200 OK를 받았다.
- `areaBasedList2`에 `listYN=Y`를 넣으면 `INVALID_REQUEST_PARAMETER_ERROR(listYN)`가 발생하므로 사용하지 않는다.
- `TourAPIService.area_based_list("1", num_of_rows=3)`는 서울 관광정보 3건을 정상 수신했다.
- 2026-05-15 공공데이터포털 화면에서 `한국관광공사_무장애 여행 정보` 개발계정 승인을 확인했고, 반영 후 `KorWithService2/areaCode2`, `detailWithTour2`, `areaBasedList2` 호출이 200 OK로 확인됐다.
- 전국 시군구 코드는 `scripts/fetch_tour_area_codes.py`로 `data/processed/tour_area_codes.json` 캐시를 생성해 사용한다. 시군구 코드를 전국 수동 맵으로 하드코딩하지 않는다.
- `/tourism/chat`은 지역이 확정되면 이전 live 조회 Markdown 캐시를 먼저 확인한다. live 캐시에 없으면 Chroma 색인과 로컬 Markdown fallback을 확인한다. 그래도 같은 지역 카드가 없고 API 키가 있으면 `KorWithService2/areaBasedList2` 후보를 조회하고, 상위 후보에 대해 `detailCommon2`와 `detailWithTour2`를 호출해 카드를 만든다.
- 같은 지역 반복 요청은 프로세스 메모리 캐시와 `data/generated/tour_api/live_markdown/` Markdown 캐시를 사용해 일일 호출량을 줄인다. `data/raw/tourism_accessible/`는 계획 수집한 fallback/색인 후보로 유지한다.
- 데이터 신선도는 MVP에서는 요청 중 재조회가 아니라 Post-MVP 주기적 갱신 배치로 해결한다.
- 개발/QA 기본 모드는 `cache/fallback-first + live-on-miss`이다. 호출량 또는 시연장 네트워크가 불안하면 `TOURISM_LIVE_LOOKUP_ENABLED=false`로 끄고 fallback-only로 운영한다. 장기 권장은 `cache/fallback-first + 주기적 갱신 + live-on-miss`이다.
- 수집 스크립트는 캐시/시연 안정화용으로 유지한다. 기본값은 서울/부산/강릉 각 20건, 실행당 최대 150 API 호출이다.
- fallback 수집은 `docs/tourism/tourism_data_collection_plan.md`의 `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 배치로 나눠 진행한다.
- 2026-05-15 기준 광역권 fallback 분할 수집과 시군구 fallback 확장 수집을 진행했다. 중복 콘텐츠ID 정리 후 `data/raw/tourism_accessible`에는 643개 Markdown이 있고, Chroma에는 전체 raw 기준 644개 문서/650개 청크가 색인됐다.
- 시군구 fallback은 아직 전국 실사용 지역 250개 기준 완료가 아니다. 현재 TourAPI 지역 코드 234개 중 161개 시군구가 3장 이상 확보됐고, 234개 기준 3장 목표까지 남은 부족분은 약 182장이다.
- offline-index 우선 방식과 cache/fallback-first + live-on-miss 방식의 차이, 장단점, 되돌림 기준은 `docs/tourism/tourism_response_strategy_decision.md`에 기록한다.
- curated 샘플은 API 실패 대비와 테스트용 fallback으로 유지한다.
- 지역 응답 정책은 2026-05-15에 코드와 테스트로 반영했다. 예: `서울 강남구에서 휠체어 관광지 추천해줘`는 강남구 2건만 반환하고 부족 안내를 제공한다. `서울 강남구 근처에서 휠체어 관광지 추천해줘`는 서울 범위 확장 안내와 함께 5건을 반환한다.
- 동명이 시군구 정책도 2026-05-15에 반영했다. 예: `중구에서 휠체어 타시는 어머니를 모시고 다닐수 있는 관광지를 추천해줘`는 추천을 바로 생성하지 않고 서울/인천/대전/대구/부산/울산 중구 선택 후보를 반환한다. `부산 중구에서 ...`처럼 광역 지역을 함께 말하면 부산 중구로 확정해 추천한다.
- MVP UI는 사용자가 먼저 지역 버튼을 선택할 수 있게 돕되, 채팅 자유 입력도 항상 허용한다. 모호 지역이 들어오면 API의 `suggested_messages`를 후속 질문 버튼으로 보여준다. 후속 질문은 사용자의 원래 문장에서 모호한 지역명만 확정 지역명으로 바꿔 질문 맥락을 유지한다.
- 관계 호칭만으로 나이를 추정하지 않는다. `아빠`, `어머니`, `부모님`은 고령자 조건으로 자동 변환하지 않고, `고령자`, `어르신`, `노인`처럼 명시된 표현이 있을 때만 고령자 조건을 붙인다.

## 다음 세션 첫 확인 명령

```bash
.venv/bin/python scripts/fetch_tour_area_codes.py
.venv/bin/python scripts/fetch_accessible_tourism_samples.py
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest
```
