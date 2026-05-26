# Tourism Live Update Lookup Plan

마지막 갱신: 2026-05-25

## 구현 상태

2026-05-25에 1차 구현을 완료했다. 기본값은 기존 `cache_first`이고, 새 정책은 `TOURISM_LOOKUP_STRATEGY=live_update`일 때만 활성화된다.

구현된 범위:

- 5초 grace wait 후 fallback 선응답
- 15초 background timeout
- 세션별 live update job registry
- 새 요청 시 이전 running job과 pending update 폐기
- 승인 문구 요청 시 pending live update 반영
- timeout, pending, update 상태용 `lookup_mode`
- frontend suggested message 버튼을 통한 “최신 결과 업데이트 보기” 승인 흐름
- 강제 지연/무응답/cancel unit test

검증:

- `.venv/bin/python -m pytest -q`
- 결과: `361 passed, 2 warnings`

## 목적

현재 `/tourism/chat`은 live Markdown cache, RAG index, raw fallback sample을 먼저 보고, 후보가 없거나 사용자가 live 보강을 요청할 때 TourAPI를 호출한다. 검토하려는 변경은 단순 `api_first`가 아니라, TourAPI를 먼저 시도하되 5초 안에 결과가 없으면 즉시 cache/RAG/fallback 응답을 반환하고, live 작업은 최대 15초까지만 유지해 다음 사용자 요청에서 업데이트 후보로 제시하는 방식이다.

이 문서는 구현 전 수정량과 안전한 분기 전략을 정리한다. 바로 기본 운영값을 바꾸지 않고, 설정 플래그로 기존 `cache_first`와 새 `live_update` 전략을 함께 유지한 뒤 eval과 latency를 비교한다.

## 현재 경로

현재 `TourismChatService`의 후보 조회 순서는 다음과 같다.

1. live Markdown cache
2. RAG index
3. raw fallback sample
4. live TourAPI on miss
5. live top-up 요청 시 TourAPI 보강

이 구조는 시연 안정성과 API 호출량 절감을 우선한다. 단점은 cache/fallback이 오래됐거나 지역 후보가 부족할 때 최신 TourAPI 후보를 늦게 본다는 점이다.

## 목표 경로

`live_update` 모드의 후보 조회 순서는 다음과 같다.

1. 새 요청 시작 시 같은 `session_id`의 이전 live 작업을 취소한다.
2. live TourAPI 작업을 시작한다.
3. 최대 5초까지 live 결과를 기다린다.
4. 5초 안에 성공하고 조건 근거가 맞으면 live 결과를 반환한다.
5. 5초 안에 결과가 없거나 실패하면 기존 cache/RAG/fallback 결과를 즉시 반환한다.
6. 5초를 넘긴 live 작업은 최대 15초까지만 유지한다.
7. 15초 안에 live 결과가 준비되면 세션별 pending update로 저장한다.
8. 다음 요청에서 pending update가 있으면 “새로운 업데이트가 있습니다. 반영할까요?” 형태로 사용자에게 승인 옵션을 제시한다.
9. 사용자가 승인하면 저장된 live 결과로 새 카드 응답을 반환한다.
10. 사용자가 다른 새 요청을 보내면 이전 pending update와 live 작업은 폐기한다.

API 호출은 다음 조건을 모두 만족할 때만 먼저 시도한다.

- `TOURISM_LIVE_LOOKUP_ENABLED=true`
- TourAPI service key가 있음
- 지역 코드가 확정됨
- unsupported, clarification, non-tourism, general-tourism-only 응답이 아님

## 설정

새 설정을 추가한다.

```env
TOURISM_LOOKUP_STRATEGY=cache_first
TOURISM_LIVE_FIRST_WAIT_SECONDS=5.0
TOURISM_LIVE_BACKGROUND_TIMEOUT_SECONDS=15.0
```

허용값:

- `cache_first`: 기존 동작. cache/RAG/fallback 우선, miss 또는 live top-up 요청 시 API 호출
- `live_update`: live TourAPI를 먼저 시도하되 5초 안에 안 끝나면 fallback 응답을 먼저 반환하고, 15초 안에 완료된 live 결과는 다음 요청에서 승인형 업데이트로 제시

초기 기본값은 `cache_first`로 둔다. `live_update`는 eval과 latency 확인 후 기본 전환 여부를 결정한다.

## 구현 단계

1. 설정 추가
   - `app/core/config.py`에 `tourism_lookup_strategy` 추가
   - 허용값 검증은 우선 service 내부에서 단순 문자열 비교로 시작
   - `.env.example`, 관련 문서에 기본값 기록

2. live 작업 레지스트리 추가
   - `TourismChatService` 내부에 세션별 live 작업 상태를 관리한다.
   - key는 `session_id`를 기본으로 하고, session이 없으면 요청 단위로 즉시 fallback만 사용하거나 임시 key를 쓴다.
   - 상태 필드:
     - `task` 또는 `future`
     - `query_fingerprint`
     - `created_at`
     - `deadline_at`
     - `status`: `running`, `ready`, `failed`, `timeout`, `cancelled`
     - `cards`
     - `query`

3. 새 요청 시 취소 정책
   - 같은 `session_id`에 running live 작업이 있으면 새 요청 시작 전에 취소한다.
   - 같은 `session_id`에 ready pending update가 있어도 사용자가 업데이트 승인 의도를 보이지 않으면 폐기한다.
   - clarification, unsupported, non-tourism 요청은 live 작업을 만들지 않는다.

4. 후보 조회 순서 분리
   - `TourismChatService.handle()`의 긴 후보 조회 구간을 helper로 분리
   - 예: `_lookup_candidates_cache_first(...)`, `_lookup_candidates_live_update(...)`
   - 기존 경로의 동작을 먼저 helper로 옮겨 테스트를 유지한 뒤 live-update helper를 추가

5. 5초 grace fallback 조건 정의
   - API 예외, timeout, quota 초과, 빈 결과는 fallback으로 내려감
   - API 후보가 있어도 `_cards_cover_requested_conditions()` 실패 시 fallback으로 내려감
   - 5초 안에 API 후보가 유효하면 live 결과를 반환
   - 5초를 넘기면 사용자 응답은 cache/RAG/fallback으로 반환하고, live 작업은 15초까지만 계속 유지
   - 15초 안에 완료된 결과만 pending update로 저장
   - 15초 초과, 실패, 취소 결과는 조용히 폐기

6. 업데이트 승인 처리
   - 다음 요청에서 사용자가 “업데이트 보기”, “반영해줘”, “최신 결과 보여줘”처럼 승인 의도를 보이면 pending live 결과를 반환한다.
   - 승인 전 일반 요청이면 pending update는 버린다.
   - pending update를 알리는 응답은 기존 답변 흐름을 깨지 않도록 `suggested_messages` 또는 별도 response field를 사용한다.
   - response schema 변경이 부담되면 1차 구현은 `suggested_messages`에 “최신 결과 반영하기”를 넣고, 이후 UI 필드를 추가한다.

7. lookup mode 정리
   - 5초 안 live 성공: `live`
   - API 실패 후 cache 성공: `cache`
   - API 실패 후 index 성공: `indexed`
   - API 실패 후 sample 성공: `sample`
   - fallback을 먼저 반환했지만 live 작업이 계속 중인 경우: 기존 lookup mode 유지 + `live_update_pending=true` 같은 필드 추가 검토
   - pending update 승인 후 반환: `live_update`
   - 1차 구현에서 schema 변경을 피하면 `lookup_mode=live_top_up`을 재사용할 수 있지만, 의미가 어긋나므로 `live_update` 추가가 더 명확하다.

8. timeout과 호출량 가드
   - 사용자 응답 대기 한도는 `TOURISM_LIVE_FIRST_WAIT_SECONDS=5.0`
   - live 작업 전체 한도는 `TOURISM_LIVE_BACKGROUND_TIMEOUT_SECONDS=15.0`
   - TourAPI 자체 timeout이 20초면 background 전체 timeout보다 길어 취소가 늦을 수 있으므로, live-update 모드에서는 TourAPI client timeout을 15초 이하로 맞추는 방안을 검토한다.
   - quota 초과가 예상되면 live 작업을 만들지 않고 fallback만 반환한다.

9. 테스트
   - `cache_first`가 기존 테스트를 통과하는지 확인
   - `live_update`에서 5초 안 API 성공 시 live 결과를 반환하는지 확인
   - 5초 초과 시 fallback 결과를 반환하고 live 작업 상태를 유지하는지 확인
   - 15초 안 완료된 live 결과가 pending update로 저장되는지 확인
   - 새 요청이 들어오면 이전 running 작업과 pending update를 취소/폐기하는지 확인
   - 승인 의도 요청에서 pending live 결과를 반환하는지 확인
   - 15초 초과 live 작업은 timeout 처리되어 폐기되는지 확인
   - API 실패 시 cache/RAG/sample 순서로 내려가는지 확인
   - API 후보가 조건 근거를 못 맞추면 fallback으로 내려가는지 확인
   - `TOURISM_LIVE_LOOKUP_ENABLED=false`이면 live-update 설정이어도 fallback-only가 되는지 확인

10. 평가
   - `cache_first`와 `live_update`를 같은 eval set으로 비교
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

작게 구현해도 2일 내외로 본다.

- 설정 추가와 문서 반영
- `TourismChatService` 후보 조회 helper 분리
- live 작업 레지스트리 추가
- 5초 grace fallback과 15초 background timeout 처리
- pending update 승인 처리
- 핵심 unit test 추가

운영 기본값 전환까지는 3-5일 정도로 본다.

- timeout과 quota 정책 보정
- live API 실패/지연 상황 수동 점검
- hard/noisy eval 비교
- lookup mode와 warning 문구 확정
- 운영 문서 업데이트

## 리스크

- live-update는 매 질문마다 live 호출 가능성이 커져 일일 quota를 빠르게 소모할 수 있다.
- `detailCommon2`, `detailWithTour2` 상세 호출이 카드당 2회라 지역별 5장만 만들어도 endpoint 호출량이 커진다.
- 네트워크 지연은 5초까지만 사용자 응답 지연으로 노출되지만, 백그라운드 작업이 쌓이면 서버 리소스를 잡아먹을 수 있다.
- TourAPI 결과는 최신성이 장점이지만, 접근성 상세가 비어 있으면 오히려 fallback보다 카드 품질이 낮을 수 있다.
- 기존 eval의 `lookup_mode` 기대값이 바뀔 수 있다.
- 현재 `/tourism/chat` 라우트와 service는 동기 구조다. background live 작업은 thread executor 또는 별도 작업 레지스트리로 다뤄야 하며, 단순 `asyncio.Task`만으로는 취소/수명 관리가 불안정할 수 있다.
- 새 요청 시 이전 작업을 취소하는 정책 때문에, 사용자가 fallback 응답 직후 바로 다른 질문을 하면 이전 live update는 버려진다. 이는 의도한 정책으로 문서화한다.

## 채택 기준

`live_update`를 기본값으로 바꾸려면 다음 조건을 만족해야 한다.

1. residual hard와 challenge eval이 기존 수준을 유지한다.
2. noisy realistic eval에서 실패가 늘지 않는다.
3. p95 latency가 허용 가능한 범위다.
4. API quota 예상 사용량이 운영 시나리오를 감당한다.
5. API 실패, 5초 초과, 15초 초과, 새 요청 cancel 시 fallback 응답이 기존과 동등하게 유지된다.
6. pending update가 다른 사용자 질문이나 다른 지역/조건 질문에 섞이지 않는다.

조건을 만족하지 못하면 기본값은 `cache_first`로 유지하고, 사용자가 “최신 정보”를 요청할 때만 live top-up을 쓰는 현 구조를 유지한다.
