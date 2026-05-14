# GOAL

무장애·가족 친화 관광정보 AI 챗봇 MVP를 완성한다.

## 완성 기준

1. 한국관광공사 무장애 여행 정보 OpenAPI 샘플 수집이 가능하다.
2. 수집 데이터를 정규화해 RAG 색인에 넣을 수 있다.
3. 사용자가 자연어로 질문하면 관광지 3~5개를 추천한다.
4. 답변에는 접근성·가족 친화 근거와 출처가 포함된다.
5. 관광지 카드 응답 schema가 있다.
6. pytest와 기본 API 스모크 테스트가 통과한다.

단, 시군구처럼 좁은 지역을 사용자가 명시한 경우에는 추천 품질을 위해 자동 확장하지 않는다. 해당 시군구에서 3개 미만만 확인되면 부족 안내와 함께 확인된 결과만 제공한다. 사용자가 `근처`, `주변`, `가까운`, `인근`처럼 확장 의도를 밝힌 경우에만 상위 광역 지역 후보를 함께 포함한다.

## 진행 원칙

- 1차 주제는 무장애·가족 친화 관광정보 챗봇이다.
- 데이터 수집이 어렵거나 접근성/영유아 가족 관련 필드가 부족하면 2차 대안으로 반려동물 동반 관광정보 챗봇을 검토한다.
- Anaconda/conda는 사용하지 않는다.
- 프로젝트 `.venv`를 사용한다.
- 경로는 항상 프로젝트 상대 경로를 우선한다.
- 구현 전후로 gstack 스킬을 `/plan-ceo-review` -> `/plan-eng-review` -> `/plan-design-review` -> `/qa` -> `/review` 순서로 활용한다.

## 현재 우선순위

1. 한국관광공사 국문 관광정보 서비스_GW 샘플 수집 흐름을 기준으로 TourAPI 연결을 안정화한다.
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
- 수집 스크립트는 `KorWithService2/areaBasedList2`에서 후보를 가져오고, 접근성 필드가 확보된 항목만 RAG용 Markdown으로 생성한다.
- 2026-05-15 live 수집 결과 서울/부산/강릉 각 5건, 총 15건의 무장애 Markdown을 생성했다.
- curated 샘플은 API 실패 대비와 테스트용 fallback으로 유지한다.
- 지역 응답 정책은 2026-05-15에 코드와 테스트로 반영했다. 예: `서울 강남구에서 휠체어 관광지 추천해줘`는 강남구 2건만 반환하고 부족 안내를 제공한다. `서울 강남구 근처에서 휠체어 관광지 추천해줘`는 서울 범위 확장 안내와 함께 5건을 반환한다.

## 다음 세션 첫 확인 명령

```bash
cd /Users/cheng80/Desktop/chatbot_rag
.venv/bin/python scripts/fetch_tour_area_codes.py
.venv/bin/python scripts/fetch_accessible_tourism_samples.py
.venv/bin/python scripts/rebuild_index.py
.venv/bin/python -m pytest
```
