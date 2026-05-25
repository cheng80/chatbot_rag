# Tourism API-First Lookup Plan

마지막 갱신: 2026-05-25

## 목적

현재 `/tourism/chat`은 live Markdown cache, RAG index, raw fallback sample을 먼저 보고, 후보가 없거나 사용자가 live 보강을 요청할 때 TourAPI를 호출한다. 검토하려는 변경은 이 순서를 뒤집어 TourAPI를 먼저 시도하고, 응답 지연, 실패, 0건, 조건 근거 부족 시 기존 cache/RAG/fallback 경로로 내려가는 것이다.

이 문서는 구현 전 수정량과 안전한 분기 전략을 정리한다. 바로 기본 운영값을 바꾸지 않고, 설정 플래그로 `cache_first`와 `api_first`를 함께 유지한 뒤 eval과 latency를 비교한다.

## 현재 경로

현재 `TourismChatService`의 후보 조회 순서는 다음과 같다.

1. live Markdown cache
2. RAG index
3. raw fallback sample
4. live TourAPI on miss
5. live top-up 요청 시 TourAPI 보강

이 구조는 시연 안정성과 API 호출량 절감을 우선한다. 단점은 cache/fallback이 오래됐거나 지역 후보가 부족할 때 최신 TourAPI 후보를 늦게 본다는 점이다.

## 목표 경로

`api_first` 모드의 후보 조회 순서는 다음과 같다.

1. live TourAPI
2. live Markdown cache
3. RAG index
4. raw fallback sample
5. 필요 시 후보 병합과 더 보기 처리

API 호출은 다음 조건을 모두 만족할 때만 먼저 시도한다.

- `TOURISM_LIVE_LOOKUP_ENABLED=true`
- TourAPI service key가 있음
- 지역 코드가 확정됨
- unsupported, clarification, non-tourism, general-tourism-only 응답이 아님

## 설정

새 설정을 추가한다.

```env
TOURISM_LOOKUP_STRATEGY=cache_first
```

허용값:

- `cache_first`: 기존 동작. cache/RAG/fallback 우선, miss 또는 live top-up 요청 시 API 호출
- `api_first`: API 우선, 실패 또는 부적합 시 기존 fallback 체인 사용

초기 기본값은 `cache_first`로 둔다. `api_first`는 eval과 latency 확인 후 기본 전환 여부를 결정한다.

## 구현 단계

1. 설정 추가
   - `app/core/config.py`에 `tourism_lookup_strategy` 추가
   - 허용값 검증은 우선 service 내부에서 단순 문자열 비교로 시작
   - `.env.example`, 관련 문서에 기본값 기록

2. 후보 조회 순서 분리
   - `TourismChatService.handle()`의 긴 후보 조회 구간을 helper로 분리
   - 예: `_lookup_candidates_cache_first(...)`, `_lookup_candidates_api_first(...)`
   - 기존 경로의 동작을 먼저 helper로 옮겨 테스트를 유지한 뒤 api-first helper를 추가

3. API-first fallback 조건 정의
   - API 예외, timeout, quota 초과, 빈 결과는 fallback으로 내려감
   - API 후보가 있어도 `_cards_cover_requested_conditions()` 실패 시 fallback으로 내려감
   - API 후보와 fallback 후보를 무조건 병합하지 않고, 첫 구현은 API 후보가 유효하면 API 결과를 우선 반환
   - 카드 수가 `DEFAULT_CARD_LIMIT`보다 적고 fallback에 더 적합한 후보가 있으면 보강 병합은 별도 단계로 둠

4. lookup mode 정리
   - API 우선 성공: `live`
   - API 실패 후 cache 성공: `cache`
   - API 실패 후 index 성공: `indexed`
   - API 실패 후 sample 성공: `sample`
   - API 호출은 했지만 fallback을 사용한 경우 `degraded=true`와 warning을 유지
   - 필요하면 추후 `live_fallback_cache` 같은 세분화 mode를 추가하지만, 1차 구현에서는 기존 enum에 맞춘다

5. timeout과 호출량 가드
   - 현재 `TOUR_API_TIMEOUT=20.0`은 API-first 사용자 응답에는 길다
   - 1차 구현에서는 설정값을 바꾸지 않고, eval/수동 테스트에서 timeout 영향을 측정
   - 후속으로 `TOURISM_LIVE_FIRST_TIMEOUT` 또는 API-first 전용 짧은 timeout을 검토

6. 테스트
   - `cache_first`가 기존 테스트를 통과하는지 확인
   - `api_first`에서 API 성공 시 cache/index/sample을 호출하지 않는지 확인
   - API 실패 시 cache/RAG/sample 순서로 내려가는지 확인
   - API 후보가 조건 근거를 못 맞추면 fallback으로 내려가는지 확인
   - `TOURISM_LIVE_LOOKUP_ENABLED=false`이면 API-first 설정이어도 fallback-only가 되는지 확인

7. 평가
   - `cache_first`와 `api_first`를 같은 eval set으로 비교
   - 필수 eval:
     - `tourism_residual_hard_chat_20260518.jsonl`
     - `tourism_challenge_questions.jsonl`
     - `tourism_noisy_realistic_chat_eval_v1_200.jsonl`
   - 지표:
     - pass count
     - lookup mode 분포
     - TourAPI 호출량
     - p50/p95 latency
     - 조건 근거 누락/지역 누수/unsupported 카드 반환

## 예상 수정량

작게 구현하면 1일 내외다.

- 설정 추가와 문서 반영
- `TourismChatService` 후보 조회 helper 분리
- api-first helper 추가
- 핵심 unit test 추가

운영 기본값 전환까지는 2-3일 정도로 본다.

- timeout과 quota 정책 보정
- live API 실패/지연 상황 수동 점검
- hard/noisy eval 비교
- lookup mode와 warning 문구 확정
- 운영 문서 업데이트

## 리스크

- API-first는 매 질문마다 live 호출 가능성이 커져 일일 quota를 빠르게 소모할 수 있다.
- `detailCommon2`, `detailWithTour2` 상세 호출이 카드당 2회라 지역별 5장만 만들어도 endpoint 호출량이 커진다.
- 네트워크 지연이 사용자 응답 지연으로 직접 노출된다.
- TourAPI 결과는 최신성이 장점이지만, 접근성 상세가 비어 있으면 오히려 fallback보다 카드 품질이 낮을 수 있다.
- 기존 eval의 `lookup_mode` 기대값이 바뀔 수 있다.

## 채택 기준

`api_first`를 기본값으로 바꾸려면 다음 조건을 만족해야 한다.

1. residual hard와 challenge eval이 기존 수준을 유지한다.
2. noisy realistic eval에서 실패가 늘지 않는다.
3. p95 latency가 허용 가능한 범위다.
4. API quota 예상 사용량이 운영 시나리오를 감당한다.
5. API 실패 시 fallback 응답이 기존과 동등하게 유지된다.

조건을 만족하지 못하면 기본값은 `cache_first`로 유지하고, 사용자가 “최신 정보”를 요청할 때만 live top-up을 쓰는 현 구조를 유지한다.
