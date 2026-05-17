# 중간 길이 질의 모델 비교 결과

최종 갱신: 2026-05-18

## 목적

짧은 단문이 아니라 실제 사용자가 입력할 법한 중간 길이 문장으로 `/tourism/chat` 카드 품질을 비교한다.

비교 대상:

- rule/parser: 도메인 정규화 + 기존 규칙 파서
- ET5 local: 로컬 한국어 교정 후보를 추가한 파서
- quickspacer: 로컬 띄어쓰기 후보를 추가한 파서
- RoBERTa-small candidate: 로컬 KLUE-RoBERTa 조건 multi-label 후보를 추가한 파서

## 평가 자산

- 입력: `data/eval/tourism_context_medium_chat_eval_v4_120.jsonl`
- 생성기: `scripts/generate_tourism_medium_chat_eval_v4.py`
- 비교 실행: `scripts/compare_tourism_medium_chat_models.py`
- 결과: `data/generated/tour_api/medium_chat_model_compare_20260518/summary.json`
- 요약: `data/generated/tour_api/medium_chat_model_compare_20260518/summary.md`

평가셋은 120건이다. 휠체어 오타, 장애인 화장실, 엘리베이터/엘베, 유모차/유아차, 수어/자막, 안내견/점자, 시장 제외, 일반 식당 경계, 무띄어쓰기, 모호 지역, 잘못된 전제, 후속 조건 추가/교체/지역 변경을 포함한다.

## 결과

| 변형 | 카드 품질 통과 | 실패 | 통과율 | 평균 응답 시간 |
|---|---:|---:|---:|---:|
| rule/parser | 100 | 20 | 0.8333 | 209.3ms |
| ET5 local | 100 | 20 | 0.8333 | 313.6ms |
| quickspacer | 100 | 20 | 0.8333 | 354.2ms |
| RoBERTa-small candidate | 100 | 20 | 0.8333 | 252.6ms |

조건 라벨 추출 비교도 네 변형 모두 동일했다.

| 변형 | exact | micro-F1 | false positive | false negative |
|---|---:|---:|---:|---:|
| rule/parser | 0.6167 | 0.8380 | 42 | 4 |
| ET5 local | 0.6167 | 0.8380 | 42 | 4 |
| quickspacer | 0.6167 | 0.8380 | 42 | 4 |
| RoBERTa-small candidate | 0.6167 | 0.8380 | 42 | 4 |

## 해석

이번 120건에서는 ET5, quickspacer, RoBERTa 후보가 실제 카드 품질을 개선하지 못했다. ET5와 quickspacer는 응답 시간이 늘었고, RoBERTa도 통과율 개선이 없었다.

따라서 이 평가셋만 기준으로는 런타임 승격을 하지 않는다. 다만 이 세트는 명시 조건과 기존 룰이 잘 잡는 문장이 많아, 모델 간 차이를 드러내기에는 약했다.

후속으로 `data/eval/tourism_hard_nlu_holdout_20260518.jsonl`과 `data/eval/tourism_hard_semantic_chat_eval_20260518.jsonl`을 추가했다. hard 의미 평가에서는 hard 증강 RoBERTa 보조가 기본 rule/parser보다 뚜렷하게 나았다. 세부 결과는 `docs/tourism/tourism_hard_nlu_condition_transformer.md`에 정리한다.

남은 실패는 모델 선택보다 데이터 커버리지와 후속 정책 문제에 가깝다.

- 청각 접근성: 수어/자막 근거 카드 부족
- 시각 접근성: 안내견/점자 근거 카드 부족
- 일부 지역 엘리베이터/유모차 조건 카드 부족
- 보조견 조건을 유지한 상태에서 지역을 바꾸는 후속질문은 결과가 쉽게 0장이 된다

## 반영한 수정

`서울 전체로 넓혀서 더 찾아줘` 같은 명시적 확장 후속질문이 이전 조건을 잃고 일반 관광지 요청으로 처리되던 문제를 수정했다. 이제 이전 세션의 조건을 유지한 채 상위 지역 확장을 수행한다.

## 다음 작업

1. 청각/시각 접근성 근거 카드 커버리지부터 보강한다.
2. 보조견/점자/수어/자막처럼 희소 조건은 결과 없음 안내와 조건 완화 제안을 더 명확히 한다.
3. hard 의미 표현은 `tourism_hard_nlu_condition_transformer.md` 기준으로 RoBERTa 보조를 평가한다.
4. 조건 라벨 평가는 “무장애” 표현이 휠체어 조건으로 보정되는 현재 정책을 반영해 기대 라벨을 재정리한다.
