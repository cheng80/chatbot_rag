# 관광 챗봇 ML 평가 운영 기준

마지막 갱신: 2026-05-17

## 목적

이 문서는 의도 분류기, 문맥 해석 classifier, KoBERT/KLUE-RoBERTa fine-tuning 같은 ML 실험을 평가할 때 반드시 확인할 기준을 고정한다. 목표는 높은 점수를 홍보하는 것이 아니라, 실제 서비스에서 잘못된 판단을 줄이는 것이다.

초급자가 문서를 따라가더라도 다음 문제를 그냥 지나치지 않게 해야 한다.

- validation 1.0000을 성능으로 오해
- train/validation split이 같은 템플릿이라 실제 검증이 안 되는 문제
- holdout이 작거나 쉬워서 1.0000이 반복되는 문제
- 과적합, 과소적합, 과대 일반화, 이상치/특이치 누락
- latency와 운영 비용을 무시한 모델 채택
- rule 보강으로 점수를 회피하고 실제 판단셋을 개선하지 않는 문제

## 용어

| 용어 | 이 프로젝트에서의 의미 |
|---|---|
| train | 모델이 직접 학습하는 데이터 |
| validation | epoch, threshold, hyperparameter 선택용 데이터 |
| hard holdout | 학습/검증에 쓰지 않는 독립 평가 데이터. 채택 판단의 핵심 |
| leakage | 같은 템플릿, 같은 문장, 같은 생성 규칙이 train과 validation/test에 섞이는 현상 |
| overfitting | train/validation은 높지만 hard holdout이 낮은 상태 |
| underfitting | train 자체도 낮고 validation/test도 낮은 상태 |
| overgeneralization | 특정 단어를 보면 너무 넓게 라벨을 붙이는 상태 |
| outlier | 데이터 오류, 이상한 문장, API 이상 응답처럼 분포에서 벗어난 케이스 |
| edge case | 실사용에서는 적지만 서비스 품질을 깨는 경계 케이스 |

## 필수 데이터 분리 원칙

1. 학습셋과 평가셋은 파일만 달라서는 부족하다. 문장 생성 템플릿, 지역명 조합, 조건 조합도 분리해야 한다.
2. validation은 train과 같은 템플릿을 무작위 split한 것만으로 만들지 않는다. 최소한 일부는 hard-style validation으로 둔다.
3. hard holdout은 학습, threshold 선택, rule 보정에 직접 쓰지 않는다. 오류 분석 후 새 반례를 만들 때도 기존 hard holdout 문장을 그대로 train에 넣지 않는다.
4. AI-generated 데이터는 실제 사용자 holdout을 대체하지 않는다. 사람이 작성한 문장이 없으면 “AI-generated independent holdout”이라고 명시한다.
5. focused/contract 셋의 1.0000은 실사용 품질 지표가 아니다. 해당 경계가 깨지지 않는지 확인하는 최소 방어선으로만 본다.

## 필수 지표

모델을 비교할 때 accuracy 하나만 보지 않는다.

| 지표 | 이유 |
|---|---|
| exact match | multi-label 전체 판단이 맞는지 확인 |
| micro-F1 | 전체 라벨 단위 성능 |
| per-label precision/recall/F1 | 특정 라벨의 과잉/누락 확인 |
| special errors | 서비스 위험 오류를 직접 추적 |
| sample mismatches | 숫자로 안 보이는 라벨 설계 오류 확인 |
| p50/p95 latency | 응답 시간과 운영 비용 판단 |
| train/validation/test gap | 과적합/과소적합 판단 |

문맥 해석 classifier의 special errors는 최소 다음을 본다.

- `strict_and_missed`
- `strict_and_overcalled`
- `or_as_strict_and`
- `exclude_missed`
- `specific_facility_missed`

## 과적합 판정

다음 중 하나라도 해당하면 overfitting 또는 validation 설계 실패로 기록한다.

| 조건 | 판정 |
|---|---|
| validation exact가 0.98 이상인데 hard holdout exact가 0.90 미만 | validation이 너무 쉬움 |
| validation micro-F1과 hard holdout micro-F1 차이가 0.05 이상 | 일반화 부족 |
| train loss는 계속 내려가는데 hard holdout이 정체/하락 | epoch 증가 중단 |
| validation 1.0000이 반복됨 | split 누수 또는 템플릿 중복 의심 |

2026-05-17 `klue/roberta-small` 초기 파일럿은 validation micro-F1 1.0000, hard holdout micro-F1 0.8499였으므로 과적합/검증셋 설계 실패로 본다. 따라서 이 결과로 런타임을 교체하지 않는다.

같은 날 생성 family 단위 독립 validation 1,200건을 새로 만들고 train 6,215건, validation 1,200건, locked test 4,800건으로 split을 재구성했다. 이후 blind-style extra train을 더해 최신 train split은 6,886건이다. 새 validation에서는 `klue/roberta-small` validation micro-F1이 0.9241로 내려와 1.0000 착시는 사라졌지만, locked test micro-F1은 단독 0.8594, rule hybrid 0.9474로 당시 기준선 0.9688를 넘지 못했다. 이는 “검증셋은 현실화됐지만 모델 채택 조건은 아직 미달”로 기록한다.

## 과소적합 판정

다음 중 하나라도 해당하면 모델 용량, 입력 특징, 학습 epoch, learning rate를 재검토한다.

| 조건 | 판정 |
|---|---|
| train/validation/hard holdout이 모두 낮음 | 모델이 패턴을 못 배움 |
| 핵심 라벨 recall이 계속 낮음 | 학습 데이터 또는 label definition 부족 |
| rule-only보다 ML 단독이 낮음 | 모델 입력/라벨/데이터 설계 재검토 |

단, underfitting처럼 보여도 실제로는 라벨 정의가 모호한 경우가 있으므로 sample mismatch를 먼저 본다.

## 과대 일반화 판정

다음은 과대 일반화로 본다.

- `유모차`만 보면 항상 `family_context`와 `mobility_context`를 동시에 붙임
- `말고`만 보면 항상 exclude/replace로 처리함
- `또는/아니면`과 strict AND를 동시에 붙임
- 시설 단어가 과거 조건에만 있는데 새 조건으로 오해함

이 문제는 모델 epoch를 늘려 해결하지 않는다. label definition, active requirement span, hard examples를 먼저 고친다.

## 이상치와 특이치 관리

이상치/특이치는 제거하기 전에 분류한다.

| 유형 | 처리 |
|---|---|
| 명백한 데이터 오류 | 수정 또는 제외 |
| 실제 사용자 가능 문장 | hard holdout 또는 adversarial set에 유지 |
| API/수집 오류 | 데이터 운영 문서에 기록하고 재수집 기준 추가 |
| 라벨 모호 문장 | 라벨 체계 재검토 대상으로 분리 |

`추측하지 말고`, `A는 그만하고 B`, 과거 지명 뒤 지역 전환, OR/AND 혼합 문장은 실제 사용자 가능 문장이므로 제거하지 않고 hard holdout에 유지한다.

## 모델 채택 기준

새 모델은 다음 조건을 모두 만족해야 런타임 후보가 된다.

| 항목 | 기준 |
|---|---:|
| hard holdout micro-F1 | 현재 기준선보다 최소 +0.02 |
| hard holdout exact match | 현재 기준선보다 상승 |
| special errors | 기존보다 악화 없음 |
| latency | p95가 서비스 허용 범위 안 |
| validation-hard gap | 과적합 경고 없음 |
| 운영 복잡도 | 배포/메모리/의존성 부담 설명 가능 |

2026-05-17 독립 validation split 반영 뒤 문맥 해석 기준선은 locked test 기준 `hybrid LogisticRegression` exact 0.9187, micro-F1 0.9688, 평균 예측 시간 약 0.36ms였다. 이후 `아니면 제외`를 strict 조건으로 분리하고, 가족/이동/soft 선택 조건 라벨 정의를 맞춘 뒤 한때 independent validation 1,200건, locked test 4,800건, 시설 조건 adversarial holdout 980건에서 rule-only와 hybrid 계열이 모두 exact/micro-F1 1.0000까지 올라갔다. 이 수치는 과적합이라기보다 현재 생성형 경계셋이 더 이상 약점을 드러내지 못한다는 신호로 본다.

이 1.0000은 런타임 채택 품질 점수가 아니다. 현재 생성된 경계/계약 테스트를 통과했다는 뜻이며, 실서비스 판단셋으로 쓰려면 새로운 template family, 사람이 직접 쓴 holdout, `/tourism/chat` 카드 적합성 평가에서 다시 깨뜨려야 한다. 문서나 발표에서는 “문맥 경계 회귀셋 통과”로만 표현하고, “문맥 해석 일반화 성능 100%”로 표현하지 않는다.

사람이 직접 쓴 holdout을 지금 확보할 수 없으므로, 2026-05-17에는 Codex가 기존 generator를 보지 않는다는 전제로 별도 blind holdout 80건을 작성했다. 이 파일은 `data/eval/tourism_context_blind_holdout.jsonl`이고, 기존 train/validation/test/adversarial generator family를 재사용하지 않는다. 최초 blind 평가는 다음처럼 1.0000 착시를 바로 깨뜨렸다.

| 평가셋 | 모델 | exact | micro-F1 | 해석 |
|---|---|---:|---:|---|
| blind context holdout 80건 | rule-only | 0.4750 | 0.7304 | 룰 경계 일반화 부족 |
| blind context holdout 80건 | LogisticRegression 단독 | 0.5125 | 0.7512 | 최초 blind 최고 기준선 |
| blind context holdout 80건 | hybrid LogisticRegression | 0.4500 | 0.7296 | rule 병합이 blind에서는 일부 악화 |

특히 `둘 중 하나라도 빠지면`, `엘베`, `패스`, `애기`, `유아 의자`, `후보 적을 때만 가산점`, `주차 말고 주제` 같은 표현에서 strict/OR/soft/family/facility 경계가 깨졌다. 이 결과를 바로 학습에 넣으면 blind holdout이 오염되므로, 이 파일은 우선 현재 일반화 진단셋으로 고정한다.

blind 실패 bucket을 train-only extra data로 보강한 뒤 같은 blind 파일의 최고 결과는 exact 0.6250, micro-F1 0.8340까지 올랐다. 다만 이 파일은 이제 한 차례 오류 분석과 보강에 쓰였으므로 “오염되지 않은 최종 성능”이 아니라 tuned diagnostic으로만 본다. 최신 일반화 신호는 매 cycle 새로 만드는 rotating blind로 본다.

2026-05-17 v2 rotating blind는 `경사로만 있거나 엘리베이터만`, `보조견 테마 전시 말고 동반 가능 표기`, `시설명은 상호/작품명일 뿐`, `보다는/후보가 많을 때만` 같은 경계를 추가로 흔들었다. 최초 결과는 exact 0.6000/micro-F1 0.8245였고, 경계 룰 보강 뒤 exact 0.9250/micro-F1 0.9719가 됐다.

같은 날 v3 rotating blind는 `한 장소에 같이 없으면`, `같은 카드에 적힌 곳만`, `보조 조건`, `필수로 보진 말자`, `유모차 대여`, `작품 설명/별명/캐릭터 near-miss`를 추가했다. 최초 hybrid LinearSVC는 exact 0.6625/micro-F1 0.8560이었다. 라벨 검수 중 `촉지도나 점자 안내`는 OR, `카페 말고`, `공연장은 빼고`는 exclude로 보는 것이 실사용 판단에 맞아 평가셋 라벨을 먼저 수정했다. 이후 경계 룰 보강 결과 hybrid LinearSVC exact 0.9875/micro-F1 0.9960, rule-only 1.0000이 됐다. 이 값도 v3 실패를 보고 고친 tuned diagnostic이므로 다음 채택 판단에는 새 v4 rotating blind가 필요하다.

| 평가셋 | 모델 | exact | micro-F1 | 해석 |
|---|---|---:|---:|---|
| fixed blind 80건 | hybrid LinearSVC | 0.6250 | 0.8340 | 보강 후 진단셋. 최종 품질 점수 아님 |
| rotating blind 80건 | hybrid LinearSVC | 0.5750 | 0.8163 | 최초 fresh blind 기준. 약점 확인 |
| rotating blind 80건 | hybrid LinearSVC | 0.9750 | 0.9919 | 같은 파일을 보고 룰 보강한 뒤의 tuned diagnostic. 최종 품질 점수 아님 |
| rotating blind v2 80건 | hybrid LogisticRegression | 0.6000 | 0.8245 | v1 보강 뒤 새 blind에서 다시 약점 확인 |
| rotating blind v2 80건 | hybrid LinearSVC | 0.9250 | 0.9719 | 같은 v2 파일을 보고 경계 룰 보강한 뒤의 tuned diagnostic. 최종 품질 점수 아님 |
| rotating blind v3 80건 | hybrid LinearSVC | 0.6625 | 0.8560 | v2 보강 뒤 새 blind에서 다시 약점 확인 |
| rotating blind v3 80건 | hybrid LinearSVC | 0.9875 | 0.9960 | 같은 v3 파일을 보고 라벨/룰 보강한 뒤의 tuned diagnostic. 최종 품질 점수 아님 |
| rotating blind v4 80건 | hybrid LinearSVC | 0.7250 | 0.9012 | v3 보강 뒤 새 fresh blind. 현 시점 일반화 진단 기준 |
| rotating blind v4 80건 | hybrid LogisticRegression | 0.7125 | 0.8968 | 계속 비교 대상이지만 v4에서는 LinearSVC보다 낮음 |
| rotating blind v4 80건 | rule-only | 0.7375 | 0.9091 | fresh v4에서는 하이브리드보다 높음. 런타임 교체가 아니라 룰 경계가 아직 핵심이라는 신호 |

같은 날 `/tourism/chat` 실제 응답 blind eval 10건도 추가했다. 파일은 `data/eval/tourism_context_blind_chat_eval.jsonl`이다. 최초 fallback-only direct 실행은 9/10 통과했고, `전주에서 시장 골목 말고 조용한 곳만 보고 싶어`가 `card_count_low`로 실패했다. 원인은 시장 제외 표현이 세부 근거 필수 조건처럼 남고, `조용한` 선호가 hard filter로 작동해 fallback 후보를 비워 버린 것이다. 시장 제외 파싱과 preference ranking을 보정한 뒤 같은 blind chat eval은 10/10 통과한다. 이 평가는 context label 점수와 별개로 실제 카드 후보/답변 품질을 추적한다.

이후 실제 `/tourism/chat` 카드 적합성을 더 직접 보기 위해 `data/eval/tourism_context_blind_chat_eval_v2.jsonl` 15건을 추가했다. strict 시설, OR 감각 접근성, family/mobility, 제외 선호, 잘못된 전제, 미지원 주제, 지역 교체, ambiguous region, 저커버리지 무환각 케이스를 포함한다. fallback-only direct 실행 결과는 15/15 통과다. 따라서 v4 문맥 라벨 진단에서 남은 오류 bucket을 바로 모델 교체 근거로 보지 않고, 실제 카드 품질에 영향을 주는지 먼저 분리해서 본다.

## 실험 등급

모든 실험 결과는 다음 중 하나로 표시한다.

| 등급 | 의미 | 채택 가능 여부 |
|---|---|---|
| exploratory | 데이터/검증 split 설계가 아직 불완전한 탐색 결과 | 불가 |
| baseline_candidate | 같은 hard holdout에서 기존 기준선과 비교한 후보 | 수동 검토 전까지 불가 |
| adoption_candidate | hard validation, locked hard test, latency, special errors를 모두 통과한 후보 | 검토 가능 |

2026-05-17의 hybrid LinearSVC, hybrid LogisticRegression, KLUE-RoBERTa small grid 실험은 모두 `exploratory` 또는 `baseline_candidate`다. 독립 validation과 adversarial holdout까지 경계 보강한 뒤 rule/hybrid 결과가 다시 1.0000이 됐던 구간은 rule-boundary contract 통과로만 본다. 이후 fresh rotating blind에서 micro-F1 0.8163까지 떨어졌고, 같은 파일을 보고 보강한 뒤 0.9919까지 회복했다. v2 rotating blind도 최초 micro-F1 0.8245에서 보강 후 0.9719, v3 rotating blind도 최초 micro-F1 0.8560에서 보강 후 0.9960으로 올랐다. 이 회복 수치는 해당 파일 대응 결과이다. v4 fresh blind에서는 rule-only micro-F1 0.9091, hybrid LinearSVC 0.9012, hybrid LogisticRegression 0.8968로 다시 낮아졌으므로, 현재 결론은 “모델 교체”가 아니라 “남은 boundary bucket을 실제 chat 영향 기준으로 선별”이다. KLUE-RoBERTa small은 최신 rule/hybrid 기준선과 비교해 locked test에서 이득이 없고 latency도 불리하므로 런타임 채택 후보가 아니다.

## 실험 체크리스트

실험 결과를 문서에 적기 전에 다음을 확인한다.

1. train/validation/test row 수를 기록했는가?
2. split 방식과 누수 가능성을 설명했는가?
3. validation만이 아니라 hard holdout 점수를 기록했는가?
4. per-label 결과와 special errors를 봤는가?
5. sample mismatches에서 라벨 정의 오류를 찾았는가?
6. latency를 같이 측정했는가?
7. 기존 기준선과 같은 평가셋으로 비교했는가?
8. 채택/보류 사유를 수치로 적었는가?
9. 1.0000이 나온 셋을 품질 지표로 오해하지 않았는가?
10. 다음에 개선해야 할 데이터/라벨/모델 문제가 분리됐는가?

## 자동 감사

Transformer 파일럿처럼 결과 JSON이 있는 실험은 다음 명령으로 감사한다.

```bash
.venv/bin/python scripts/audit_tourism_ml_experiment.py
```

이 스크립트는 다음 조건을 자동으로 잡는다.

- validation-hard holdout gap
- validation 1.0000 같은 과적합/검증셋 실패 신호
- 기준선 대비 micro-F1 +0.02 미달
- exact match 미개선
- latency 2배 이상 악화
- baseline 비교에 별도 hard validation split이 없는 경우

`do_not_adopt_runtime` 판정이면 exit code 2로 종료한다. 이는 실행 오류가 아니라 런타임 채택을 막는 의도된 실패다.

## 현재 프로젝트 판정

| 항목 | 판정 |
|---|---|
| intent Naive Bayes | 가볍고 빠른 shadow classifier로 유지 |
| context hybrid LogisticRegression/LinearSVC | locked test 최신 exact 0.9548/micro-F1 0.9803, independent validation 최신 exact 0.9242/micro-F1 0.9741. v3 rotating blind는 보강 후 hybrid micro-F1 0.9960, rule-only 1.0000이지만 tuned diagnostic이다. v4 fresh blind는 rule-only micro-F1 0.9091, hybrid LinearSVC 0.9012, hybrid LogisticRegression 0.8968이다. LogisticRegression은 계속 비교 대상이지만 현 fresh set 최고는 아니다 |
| KLUE-RoBERTa small 단독 | 독립 validation은 개선됐지만 locked test 일반화 부족 |
| KLUE-RoBERTa small + rule hybrid | 기준선과 동률 이하이고 latency 불리 |
| SuperGemma4 selective labeling | QA/재라벨링 보조. 런타임 보조 아님 |

다음 ML 개선은 모델 epoch를 늘리는 것이 아니라, v4 failure bucket 중 실제 `/tourism/chat` 카드 품질에 영향을 주는 항목을 먼저 고르는 것이다. 현재 chat blind v2는 15/15 통과했으므로, `mobility_context`, `exclude_condition`, `soft_and`, `strict_and`, `specific_facility_required` 오류를 곧바로 런타임 모델 변경으로 연결하지 않는다. 사람이 직접 쓴 듯한 멀티턴 문장, 조건 우선순위가 애매한 문장, 실제 카드 근거까지 포함한 평가셋을 계속 별도로 만든다. 고정 blind나 rotating blind를 보강에 사용한 뒤에는 같은 파일을 최종 점수로 쓰지 않고, `scripts/generate_tourism_context_rotating_blind_holdout.py`로 새 rotating blind를 만들어 확인한다. Codex/LLM으로 hard-style 학습셋을 생성할 때도 `docs/tourism/context_llm_dataset_generation.md`의 schema 검수, 중복/누수 검사, extra train 병합 절차를 먼저 통과해야 한다.
