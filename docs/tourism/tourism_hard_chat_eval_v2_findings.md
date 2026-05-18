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

## 판단

이번 hard v2는 기존 noisy 200보다 훨씬 많은 실패를 만들었고, 그중 실제 새 이슈가 확인됐다.  
특히 감각 접근성 OR 표현은 모델 학습보다 구조화된 의미 표현이 먼저 필요하다.
