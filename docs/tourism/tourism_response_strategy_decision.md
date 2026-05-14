# 관광 챗봇 응답 전략 결정 기록

마지막 갱신: 2026-05-15

## 왜 남기는가

초기 engineering review에서는 `/tourism/chat`을 offline-index 기반으로 고정하는 방향을 선택했다. 이후 실제 서비스 요구를 다시 검토하면서, 현재 구현은 **live TourAPI 우선 + Chroma/Markdown fallback** 방식으로 바뀌었다.

이 문서는 나중에 품질, 쿼터, 속도, 시연 안정성을 다시 검토할 때 어느 방식으로 돌아갈지 판단하기 위한 비교 기록이다.

## 두 방식 요약

### 예정 방식: offline-index 우선

```text
TourAPI 샘플 수집
  -> Markdown 생성
  -> Chroma 재색인
  -> 사용자 질문
  -> Chroma 검색
  -> Markdown 카드 파싱
  -> 답변 반환
```

요청 시점에는 외부 TourAPI를 호출하지 않는다. 미리 수집해 둔 Markdown과 Chroma 인덱스가 사실상 응답 재료다.

### 현재 방식: live-first + fallback

```text
사용자 질문
  -> 지역/조건/확장 의도 구조화
  -> 동명이 지역이면 지역 선택 후보 반환
  -> TourAPI areaBasedList2 후보 조회
  -> 상위 후보 detailCommon2 + detailWithTour2 조회
  -> TourismPlaceCard 정규화
  -> 실패/결과 없음이면 Chroma/Markdown fallback
  -> 답변 반환
```

요청 시점에 live TourAPI를 우선 사용한다. 같은 지역 반복 요청은 프로세스 메모리 캐시로 줄이고, API 장애나 결과 없음에는 수집해 둔 fallback 데이터를 사용한다.

## 핵심 차이

| 항목 | offline-index 우선 | live-first + fallback |
|---|---|---|
| 데이터 신선도 | 수집 시점에 고정 | 요청 시점 기준으로 더 신선함 |
| 지역 커버리지 | 수집한 지역/파일에 제한 | TourAPI가 지원하는 지역까지 확장 가능 |
| API 호출량 | 요청 중 0회 | 요청마다 후보/상세 호출 발생 |
| 응답 속도 | 빠르고 예측 가능 | 네트워크와 API 상태에 영향 |
| 장애 대응 | API 장애와 무관하게 안정 | fallback 없으면 API 장애 영향 큼 |
| 구현 복잡도 | 낮음 | 캐시, 쿼터, timeout, fallback 상태 필요 |
| 테스트 난이도 | fixture 중심으로 단순 | live/mock/fallback 경로를 모두 테스트해야 함 |
| 시연 안정성 | 네트워크 영향을 덜 받음 | live 실패 시 fallback 설계가 중요 |
| 사용자 기대 | “저장된 후보 중 추천”에 가까움 | “현재 공공데이터를 조회해 추천”에 가까움 |

## offline-index 우선의 장점

- 요청 중 외부 API를 호출하지 않아 빠르고 안정적이다.
- 공모전 시연 중 네트워크, 공공데이터포털 장애, 쿼터 문제에 덜 민감하다.
- pytest와 고정 fixture로 회귀 테스트를 만들기 쉽다.
- Chroma/RAG 흐름을 명확하게 보여줄 수 있다.
- 같은 질문을 반복해도 호출 비용이 없다.

## offline-index 우선의 단점

- 수집하지 않은 지역은 답할 수 없거나 빈약하게 답한다.
- “부산 중구”, “인천 중구”, “제주”처럼 지역 조합이 넓어질수록 사전 수집 부담이 커진다.
- 사용자는 채팅으로 자유롭게 묻기 때문에, 미리 모아 둔 지역만 답하는 방식은 서비스처럼 보이기 어렵다.
- 데이터가 오래되면 실제 공공데이터와 다를 수 있다.
- 답변 품질 문제가 모델 문제가 아니라 수집 범위 문제인데도 사용자에게는 구분되지 않는다.

## live-first + fallback의 장점

- 사용자가 묻는 지역을 기준으로 바로 후보를 가져와 지역 커버리지가 넓다.
- “현재 공공데이터 기반 추천”이라는 제품 설명과 더 잘 맞는다.
- fallback 데이터는 전국 전체 DB가 아니라 최소 안전망만 있으면 된다.
- 동명이 지역 선택, 시군구 확장, 조건 랭킹 같은 상담 흐름과 잘 맞는다.
- 나중에 캐시를 SQLite/JSON/Markdown으로 영속화하면 호출량과 신선도 균형을 잡을 수 있다.

## live-first + fallback의 단점

- `areaBasedList2`, `detailCommon2`, `detailWithTour2` 호출량이 누적된다.
- 공공데이터포털 일일 트래픽 제한에 직접 영향을 받는다.
- 요청 속도가 API 응답 시간에 묶인다.
- API timeout이나 502 같은 외부 실패가 사용자 경험에 들어올 수 있다.
- 테스트가 더 복잡하다. live 성공, live 실패, Chroma fallback, Markdown fallback, 지역 선택 경로를 모두 고정해야 한다.
- 현재 프로세스 메모리 캐시는 서버 재시작 후 사라진다.

## 현재 방식에서 특히 조심할 점

- 오늘처럼 fallback 수집과 UI 테스트를 함께 하면 같은 날 호출량이 빠르게 늘어난다.
- 공공데이터포털 화면에서 엔드포인트별 1,000건/일이라 보여도, 운영상 서비스 단위 제한이나 지연 집계가 있을 수 있다.
- live UI를 외부 터널로 열어 두면 다른 사람이 버튼을 누르는 것만으로도 TourAPI 호출이 발생한다.
- 시연 중에는 필요하면 `TOURISM_LIVE_LOOKUP_ENABLED=false`로 live 조회를 끄고 fallback만 사용할 수 있어야 한다.
- fallback Markdown은 전체 관광 DB가 아니라 지역별 최소 안전망이다. 품질 평가는 별도로 해야 한다.

## 현재 선택

현재 선택은 **live-first + Chroma/Markdown fallback**이다.

단, 무조건 live-only가 아니라 조건부 권장안이다.

| 상황 | 권장 모드 |
|---|---|
| 개발/QA/시연 전 준비 | live-first + fallback |
| 공공데이터 호출량이 불안정함 | fallback-only 또는 live 제한 |
| 시연장 네트워크가 불안함 | `TOURISM_LIVE_LOOKUP_ENABLED=false`로 끄고 fallback-only |
| 장기 운영 | live-first + 영속 캐시 + fallback |

이유:

- 2026-06-10 전까지 앱보다 기본 서비스 완성이 우선이다.
- 사용자는 선택형 카드뿐 아니라 자유 채팅으로 지역과 조건을 입력한다.
- 전국 모든 장소를 미리 쌓는 방식은 시간과 호출량 대비 효율이 낮다.
- 지역별 fallback은 최소 안전망으로 충분하고, 실제 응답은 live 조회가 더 자연스럽다.

최종 권장 구조:

```text
1. 질문 구조화
2. live TourAPI 조회
3. 결과를 TourismPlaceCard로 카드화
4. 결과를 캐시
5. 실패하면 Chroma/Markdown fallback
```

offline-index 우선은 폐기할 방식이 아니라 **비상/시연 안정 모드**로 남긴다.

## 되돌림 기준

다음 조건 중 하나가 반복되면 offline-index 우선 방식으로 되돌리는 것을 검토한다.

- 하루 1,000건 제한 때문에 QA나 시연 중 live 조회를 안정적으로 유지하기 어렵다.
- live 응답 시간이 사용자 체감상 너무 느리다.
- 공공데이터포털 timeout/502가 자주 발생한다.
- live 결과 품질이 수집 fallback보다 낮거나, 음식점/비관광 후보가 과하게 섞인다.
- 심사/시연 환경에서 외부 API 호출이 불가능하거나 불안정하다.

## 되돌릴 때 해야 할 일

1. `.env`에 `TOURISM_LIVE_LOOKUP_ENABLED=false`를 둔다.
2. `/tourism/chat`의 기본 설명을 offline-index 우선으로 되돌린다.
3. `/tourism-ui/` 상태 문구를 `색인 응답` 중심으로 수정한다.
4. fallback Markdown 수집 배치를 더 넓히고 `scripts/rebuild_index.py`를 실행한다.
5. `lookup_mode=live`를 기대하는 테스트를 offline-index 기대값으로 수정한다.
6. README, GOAL, MVP plan, progress 문서를 offline-index 기준으로 다시 갱신한다.

## 현재 후속 과제

- live TourAPI 응답 캐시를 프로세스 메모리에서 영속 캐시로 옮길지 검토한다.
- `lookup_mode`별 응답 품질을 20문항 eval에 포함한다.
- live 결과가 음식점 위주로 치우치는지 확인하고, 관광지 content type 또는 키워드 필터가 필요한지 검토한다.
- 외부 터널 시연 중 live 호출을 켤지, fallback-only로 둘지 데모 전에 결정한다.
