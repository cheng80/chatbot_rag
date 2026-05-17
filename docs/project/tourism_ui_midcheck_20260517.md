# Tourism UI Midcheck QA - 2026-05-17

목적: 앱형 UI 개편 중간 점검. 완료 후 정식 QA와 별개로, 현재 상태에서 개발 모드 20회와 릴리즈 모드 20회를 실제 브라우저 입력 흐름으로 확인했다.

## 환경

- Server: `http://127.0.0.1:8000`
- 실행 중이던 에디터 내장 터미널의 `uvicorn` 서버를 사용했다. Codex 숨은 세션에서 서버를 새로 띄우지 않았다.
- fallback-only가 아니라 live TourAPI 사용 가능 모드 기준이다. 결과에서 `live_top_up` 4회가 관측되어 fallback-only가 아님을 확인했다.
- Browser plugin skill은 설치되어 있었지만, 이 세션에서 `node_repl/js` 실행 도구가 노출되지 않았다. 대안으로 `.venv`에 Playwright를 설치해 Chromium 브라우저 자동화를 수행했다.
- Computer Use로 Google Chrome에서 개발 모드와 릴리즈 모드를 열어 시각 확인했다.

## 요약

| 항목 | 결과 |
|---|---:|
| 전체 | 38/40 통과 |
| 개발 모드 `/tourism-ui/` | 18/20 통과 |
| 릴리즈 모드 `/tourism-ui/?mode=release` | 20/20 통과 |
| lookup mode | cache 22, live_top_up 4, sample 5, indexed 7, clarification 1, unknown 1 |
| latency p50 | 301.65ms |
| latency p95 | 486.7ms |
| 개발 모드 내부 진단 | 노출 확인 |
| 릴리즈 모드 내부 진단 | 숨김 확인 |

스크린샷과 원본 JSON은 로컬 생성물에 있다.

- `data/generated/tour_api/ui_qa/debug_midcheck_20260517.png`
- `data/generated/tour_api/ui_qa/release_midcheck_20260517.png`
- `data/generated/tour_api/ui_qa/tourism_ui_midcheck_20260517.json`
- `data/generated/tour_api/ui_qa/tourism_ui_midcheck_20260517.md`

## 실패

| ID | 질문 | 결과 | 판단 |
|---|---|---|---|
| DEBUG-18 | `수어 안내나 자막 안내 있는 곳으로 다시 찾아줘` | `lookup_mode=unknown`, 카드 0장, 후속 제안 없음 | 이전 지역/조건 맥락에서 후보가 없을 때 부족 안내 또는 live top-up 제안으로 빠져야 한다. |
| DEBUG-20 | `오늘 환율 알려줘` | `lookup_mode=cache`, 관광 카드 1장 | 관광 범위 밖 질문이므로 `unsupported`로 처리해야 한다. |

## 개발 모드 20회

| ID | 통과 | Lookup | 카드 | 질문 |
|---|---:|---|---:|---|
| DEBUG-01 | true | cache | 5 | 서울 강남구에서 휠체어 관광지 추천해줘 |
| DEBUG-02 | true | cache | 5 | 더 보기 |
| DEBUG-03 | true | cache | 1 | 그중 시장 말고 실내 위주로 다시 보여줘 |
| DEBUG-04 | true | cache | 1 | 부산 중구에서 시장 먹거리 유모차로 갈만한 곳 추천해줘 |
| DEBUG-05 | true | live_top_up | 1 | 최신 정보 더 찾기 |
| DEBUG-06 | true | cache | 2 | 중구에서 휠체어 관광지 추천해줘 |
| DEBUG-07 | true | cache | 2 | 부산 중구에서 휠체어 관광지 추천해줘 |
| DEBUG-08 | true | cache | 1 | 그중 카페 말고 가족이 걷기 편한 곳으로 바꿔줘 |
| DEBUG-09 | true | cache | 3 | 해운대 좌동에서 아이랑 유모차로 갈만한 관광지 추천해줘 |
| DEBUG-10 | true | live_top_up | 3 | 최신 정보 더 찾기 |
| DEBUG-11 | true | sample | 3 | 제주시에서 점자블록 있는 관광지 추천해줘 |
| DEBUG-12 | true | indexed | 1 | 점자블록은 필수 아니고 조용한 곳 위주로 보여줘 |
| DEBUG-13 | true | indexed | 1 | 서귀포시에서 휠체어랑 유모차 둘 다 되는 곳만 보여줘 |
| DEBUG-14 | true | clarification | 0 | 둘 다 아니어도 유모차로 이동 편한 곳이면 좋아 |
| DEBUG-15 | true | indexed | 2 | 창원 마산합포구에서 이동약자 관광지 추천해줘 |
| DEBUG-16 | true | indexed | 3 | 마산시는 말고 창원 의창구 쪽으로 바꿔줘 |
| DEBUG-17 | true | indexed | 1 | 강릉에서 보조견 동반 가능한 관광지 추천해줘 |
| DEBUG-18 | false | unknown | 0 | 수어 안내나 자막 안내 있는 곳으로 다시 찾아줘 |
| DEBUG-19 | true | cache | 1 | 서울에서 기저귀 교환대 있는 가족 관광지 추천해줘 |
| DEBUG-20 | false | cache | 1 | 오늘 환율 알려줘 |

## 릴리즈 모드 20회

| ID | 통과 | Lookup | 카드 | 질문 |
|---|---:|---|---:|---|
| RELEASE-01 | true | cache | 5 | 제주에서 휠체어 접근 가능한 관광지 추천해줘 |
| RELEASE-02 | true | cache | 20 | 제주시로 좁혀서 더 보기 |
| RELEASE-03 | true | cache | 2 | 그중 카페 말고 산책하기 편한 곳 |
| RELEASE-04 | true | cache | 3 | 부산 중구에서 시장 먹거리 중심으로 추천해줘 |
| RELEASE-05 | true | cache | 1 | 유모차로 갈 수 있는 곳도 같이 봐줘 |
| RELEASE-06 | true | live_top_up | 5 | 부산 중구 최신 정보 더 찾기 |
| RELEASE-07 | true | cache | 1 | 서울 용산구에서 아이랑 비 오는 날 실내 관광지 추천해줘 |
| RELEASE-08 | true | cache | 1 | 기저귀 교환대가 있으면 좋고 필수는 아니야 |
| RELEASE-09 | true | cache | 5 | 서울 중구로 바꿔줘 |
| RELEASE-10 | true | cache | 3 | 휠체어 동선 확인되는 곳만 보여줘 |
| RELEASE-11 | true | sample | 3 | 인천 중구에서 부모님이랑 갈 무장애 관광지 추천해줘 |
| RELEASE-12 | true | sample | 2 | 주차 가능한 곳 위주로 더 보기 |
| RELEASE-13 | true | sample | 2 | 대구에서 점자블록과 보조견 둘 다 되는 곳만 찾아줘 |
| RELEASE-14 | true | sample | 2 | 둘 다 없으면 점자블록 근거 있는 곳만 |
| RELEASE-15 | true | cache | 5 | 강릉에서 조용한 볼거리 추천해줘 |
| RELEASE-16 | true | cache | 1 | 시장 말고 박물관이나 전시 위주로 |
| RELEASE-17 | true | cache | 1 | 계룡시에서 휠체어 관광지 추천해줘 |
| RELEASE-18 | true | live_top_up | 1 | 최신 정보 더 찾기 |
| RELEASE-19 | true | indexed | 5 | 남제주군에서 유모차 관광지 추천해줘 |
| RELEASE-20 | true | indexed | 5 | 서귀포시로 다시 안내해줘 |

## 다음 조치

1. `수어 안내나 자막 안내` 후속 질문은 지역 없는 `다시 찾아줘` 표현에서 이전 조건을 누적하지 않도록 보강했다. 카드가 없을 때도 지역/조건을 넓히는 후속 제안을 반환한다.
2. `오늘 환율 알려줘` 같은 비관광 질문은 ML intent의 `unsupported_request`를 query의 unsupported 판정으로 반영해 관광 카드가 나오지 않도록 보강했다. 단 `응급실은 말고 관광지만 계속`처럼 부정된 범위 밖 단어는 기존 관광 맥락을 유지한다.
3. 코드 보강 뒤 `.venv/bin/python -m pytest -q` 기준 275건 통과를 확인했다.
4. 실제 FastAPI 서버(`http://127.0.0.1:8000`)에 연결해 같은 조건으로 Playwright Chromium 재QA를 실행했다. 결과는 개발 모드 20/20, 릴리즈 모드 20/20, 전체 40/40 통과다.
5. 재QA 원본은 `data/generated/tour_api/ui_qa/regression_20260517_fixed/tourism_ui_regression_20260517_fixed.json`, 요약은 `data/generated/tour_api/ui_qa/regression_20260517_fixed/tourism_ui_regression_20260517_fixed.md`에 있다. 대표 스크린샷은 같은 폴더의 `debug_initial.png`, `debug_final.png`, `release_initial.png`, `release_final.png`, `mobile_cards_viewport.png`다.
