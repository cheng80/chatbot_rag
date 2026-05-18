# Tourism Hard Chat Eval v2 Findings

생성일: 2026-05-18

## 목적

기존 noisy realistic 200건은 여러 차례 보강에 사용되어 tuned diagnostic 성격이 강해졌다.  
이번 평가는 남은 실패를 끝까지 줄이는 대신, 새로운 사용자 문장 패턴에서 어떤 문제가 드러나는지 확인하기 위한 hard eval이다.

## 파일

- 평가셋: `data/eval/tourism_hard_chat_eval_v2_200.jsonl`
- 생성기: `scripts/generate_tourism_hard_chat_eval_v2.py`
- 실행 결과: `data/generated/tour_api/eval_runs/hard_chat_v2_200_gated_roberta_20260518.jsonl`

## 구성

총 200건이며 다음 유형을 섞었다.

- 중간 길이 실제 질의
- 오타/무띄어쓰기
- 수어, 자막, 점자블록, 점자안내, 촉지도, 보조견 같은 감각 접근성 조건
- `수어 또는 자막`, `점자나 음성안내` 같은 대체 가능 조건
- 조건 제외/교체
- 멀티턴 후속 질의
- 모호 질의 clarification
- 일반 관광/예약/날씨/환율 같은 MVP 범위 밖 요청

## 결과

현재 gated RoBERTa 조건 보조 기준 결과는 다음과 같다.

| 항목 | 수치 |
|---|---:|
| 전체 | 200 |
| 통과 | 124 |
| 실패 | 76 |
| 통과율 | 62.0% |

실패 유형은 다음과 같다.

| failure class | 건수 | 해석 |
|---|---:|---|
| no_card_output | 72 | 최종 응답 카드가 0장 |
| strict_evidence_unverifiable_no_card | 72 | 카드가 없어 필수 근거 검증 불가 |
| strict_evidence_mismatch | 4 | 카드는 있으나 요구한 정확 근거가 없음 |

## 새로 드러난 문제

## 상세 실패 bucket

단순 실패 사유만 보면 대부분 `card_count_low`와 `card_missing_required_terms`로 보이지만, 실제 원인은 다음처럼 나뉜다.

| bucket | 건수 | 의미 | 우선순위 |
|---|---:|---|---|
| strict_sensory_sparse_data | 28 | 수어, 자막, 점자안내, 촉지도 등 엄격 감각 접근성 조건의 지역별 카드 부족 | 중 |
| or_condition_encoded_as_strict_or_sparse | 23 | `A 또는 B`, `A나 B`가 대체 가능 조건인데 내부에서 AND처럼 해석되거나, OR 후보가 충분히 살아나지 않음 | 높음 |
| multiturn_context_or_policy_loss | 6 | 첫 턴 clarification/unsupported 이후 둘째 턴이 지역 또는 조건 맥락을 잃음 | 높음 |
| accessibility_plus_preference_sparse | 6 | 접근성 조건과 장소 선호가 동시에 들어오면 지역 내 후보가 0장으로 떨어짐 | 중 |
| strict_evidence_mismatch_cards_returned | 4 | 카드는 반환됐지만 요청한 정확 근거가 아니라 더 넓은 시각/청각 접근성 카드가 반환됨 | 높음 |
| multiturn_sparse_followup | 4 | 멀티턴 조건 교체는 됐지만 둘째 조건의 카드 자체가 부족함 | 중 |
| negation_replace_boundary_or_sparse | 2 | `처음엔 A였는데 그건 빼고 B`류에서 제외 조건 근거가 남거나 B 후보가 부족함 | 중 |
| clarification_policy_too_strict_or_expected_wrong | 2 | 평가셋은 카드 반환을 기대했지만 서비스는 clarification을 선택함 | 낮음 |
| unsupported_policy_false_positive | 1 | 접근성 조건이 남아 있는데 일반 관광 unsupported로 빠짐 | 높음 |

이 분류 기준에서는 “카드가 0장”과 “평가 실패”를 분리한다.  
예를 들어 `strict_evidence_mismatch_cards_returned`는 사용자가 카드를 보기는 하지만, 평가상으로는 요청한 정확 근거가 아니므로 실패다.

### 실패가 많은 카테고리

| category | 실패 |
|---|---:|
| hard_v2_sensory_alternative | 13 |
| hard_v2_sensory_strict:자막 | 12 |
| hard_v2_multiturn | 10 |
| hard_v2_sensory_strict:촉지도 | 6 |
| hard_v2_negation_replace | 5 |
| hard_v2_supported:고령자 | 5 |
| hard_v2_sensory_strict:청각장애 | 5 |
| hard_v2_sensory_strict:수어 | 5 |
| hard_v2_supported:보조견 | 4 |
| hard_v2_supported:휠체어 | 3 |
| hard_v2_sensory_strict:점자블록 | 3 |

가장 중요한 신호는 `hard_v2_sensory_alternative` 실패 13건이다.  
이는 단순 데이터 부족이 아니라 `OR 조건 구조화`가 부족하다는 뜻이다.

### 1. 감각 접근성 OR 표현이 AND처럼 처리됨

예:

- `점자나 음성안내`
- `점자블록이나 촉지도`
- `보조견이나 점자 안내`
- `수어 또는 자막`

평가 의도는 “둘 중 하나라도 있으면 허용”이다.  
하지만 현재 query parser는 `required_evidence_terms`를 여러 그룹으로 만들고, chat filter는 모든 그룹을 만족해야 하는 AND처럼 처리한다.  
따라서 실제로는 대체 가능한 조건인데도 카드가 0장이 되는 경우가 있다.

다음 보강 우선순위가 높다.

- OR 근거 그룹을 표현할 구조 추가
- 기존 `required_evidence_terms`는 AND로 유지
- 새 필드 예: `alternative_evidence_terms`
- 필터에서는 `required_evidence_terms` AND + `alternative_evidence_terms` 중 하나 이상으로 처리

### 2. strict sensory 조건은 데이터 커버리지 영향을 강하게 받음

수어, 자막, 점자안내, 촉지도, 보조견 단독 요청은 다수 지역에서 카드가 0장으로 떨어진다.  
이는 파서 문제가 아니라 원천 카드의 근거 필드 분포 문제일 가능성이 크다.

다만 이때도 사용자 응답은 단순 “없음”보다 다음처럼 분리해야 한다.

- 정확 근거 없음
- 같은 범주의 대체 근거 있음
- 지역 확장 필요
- 조건 완화 필요

현재 일부 응답은 대체 근거 안내가 붙지만, 모든 감각 접근성 0장 케이스에 일관되게 붙지는 않는다.

### 3. 멀티턴에서 첫 턴이 clarification이면 둘째 턴 지역 맥락을 잃음

예:

- `제주시많이안걷는관광지추천 / 많이안걷는 말고 턱 적은`
- `대전 계단 적은 관광지 추천 / 그중 엘레베터 되는 곳만`

첫 턴이 ambiguity clarification으로 끝나면 세션에 지역/조건이 기억되지 않는다.  
둘째 턴이 `그중`, `말고` 같은 후속 표현이면 지역이 없다고 다시 묻는 경우가 생긴다.

정책 선택이 필요하다.

- clarification 응답이어도 region은 세션에 보존할지
- ambiguity만 보존하지 않고, 지역과 사용자 원문 조건 후보는 저장할지

### 4. 조건 제외 후 required evidence 제거는 일부 해결됨

이번 작업 전에는 `승강기 말고 애기랑` 같은 문장에서 `엘리베이터`가 제외 조건임에도 `required_evidence_terms`에 남아 카드를 모두 제거했다.  
이번 보강으로 제외 조건의 required evidence는 제거하도록 고쳤고, hard v2에서도 일부 케이스가 통과로 바뀌었다.

남은 케이스는 주로 OR/AND 경계, 데이터 부족, 멀티턴 clarification 이후 맥락 문제다.

## 다음 보강 순서

1. `alternative_evidence_terms` 도입
2. 감각 접근성 OR 표현 파서 보강
3. clarification 이후 region 맥락 저장 정책 검토
4. hard v2를 다시 실행해 OR/멀티턴 개선분만 확인
5. 남은 0장 케이스는 데이터 커버리지 리포트로 분리

### 즉시 수정 후보

다음은 데이터 추가 없이 코드 정책으로 개선할 수 있는 항목이다.

- `수어 또는 자막`, `점자나 음성안내`, `점자블록이나 촉지도`를 `alternative_evidence_terms`로 분리한다.
- `손으로 만져 확인할 안내`, `촉지 안내도`는 `시각장애` 포괄 조건으로 넓히지 않고 `촉지도` strict 조건으로 유지한다. strict 근거가 없으면 카드 반환 대신 정확 근거 부족 안내로 처리한다.
- 첫 턴이 clarification이어도 `region`, `area_code`, `sigungu_code`, 원문 조건 후보는 세션에 저장한다.
- 후속 문장에 `층 이동 쉬운`이 있을 때 `이동`을 지명 후보로 오인하지 않도록 ambiguous region 후보에서 제외한다.
- `유아차 아니고 차 대는 곳`처럼 접근성 조건이 남아 있는 문장은 general tourism unsupported로 보내지 않는다.

### 보류 후보

다음은 성급히 코드로 해결하면 과보정 위험이 있다.

- strict sensory 조건을 무조건 시각장애/청각장애 포괄 조건으로 낮추는 것
- 지역 안에 카드가 없다고 자동으로 광역 확장하는 것
- 장소 선호를 전부 soft ranking으로 낮추는 것

이 셋은 사용자 의도와 다른 카드를 보여줄 가능성이 높으므로, 안내 문구와 후속 제안으로 처리하는 편이 낫다.

## 판단

이번 hard v2는 기존 noisy 200보다 훨씬 많은 실패를 만들었고, 그중 실제 새 이슈가 확인됐다.  
특히 감각 접근성 OR 표현은 모델 학습보다 구조화된 의미 표현이 먼저 필요하다.
