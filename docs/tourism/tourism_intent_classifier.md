# 관광 챗봇 의도 분류기

마지막 갱신: 2026-05-16

## 목적

현재 `/tourism/chat`은 규칙 기반 지역/조건 파싱을 기본으로 한다. 하지만 채팅은 단발 Q&A가 아니므로 `더 보여줘`, `그중 시장 말고`, `유모차 말고 휠체어`, `중구로 좁혀줘` 같은 짧은 후속 발화가 계속 들어온다.

의도 분류기는 이 후속 발화를 보조 감지하는 shadow classifier다. 규칙셋을 대체하지 않고, 대화 맥락을 이어받아야 하는지 판단할 때 `ml_intent`, `ml_intent_confidence`를 참고한다.

ML 실험을 해석할 때는 `docs/tourism/ml_evaluation_governance.md`를 먼저 적용한다. validation 1.0000, focused holdout 1.0000, 단일 accuracy 상승은 채택 근거가 아니다. train/validation/test gap, hard holdout, per-label 오류, special errors, latency를 같이 봐야 한다.

## 현재 구현

- 모델 파일: `data/processed/tourism_intent_classifier.json`
- 학습셋: `data/processed/tourism_intent_training.jsonl`
- seed 발화: `data/eval/tourism_intent_seed_utterances.jsonl`
- 생성 발화: `data/eval/tourism_intent_generated_utterances.jsonl`
- AI Hub 추출 발화: `data/eval/tourism_intent_aihub_utterances.jsonl`
- AI Hub 독립 holdout: `data/eval/tourism_intent_aihub_holdout.jsonl`
- 구현: `app/services/tourism_intent_classifier.py`
- 생성셋 생성: `scripts/generate_tourism_intent_utterances.py`
- AI Hub 발화 추출: `scripts/extract_aihub_tourism_intent_utterances.py`
- adversarial holdout 생성: `scripts/generate_tourism_intent_adversarial_holdout.py`
- 학습셋 생성: `scripts/build_tourism_intent_training_set.py`
- 모델 학습: `scripts/train_tourism_intent_classifier.py`
- 독립 평가: `scripts/eval_tourism_intent_classifier.py`

분류기는 명확한 후속 발화를 먼저 rule override로 잡고, 나머지는 문자 2-4gram과 whitespace token을 쓰는 Multinomial Naive Bayes로 분류한다. 외부 ML 패키지 없이 동작하므로 FastAPI 런타임 설치 부담이 없다.

## 적용 범위

런타임은 다음 intent가 confidence `0.58` 이상일 때 대화 맥락 사용 신호로 본다.

- `show_more`
- `live_topup`
- `ask_source`
- `add_condition`
- `replace_condition`
- `exclude_preference`
- `narrow_region`
- `change_region`
- `unsupported_request`

사용자가 새 지역을 명시하면 이전 지역보다 새 지역을 우선한다. 사용자가 지역을 말하지 않고 후속 조건만 말하면 같은 `session_id`의 마지막 성공 응답 지역/조건/선호를 얇게 이어받는다.

## 학습 데이터

현재 학습셋은 프로젝트 내부 평가셋, seed/생성 발화, AI Hub 원본에서 추출한 고신뢰 발화에서 만든다.

- `data/eval/tourism_100_questions.jsonl`
- `data/eval/tourism_challenge_questions.jsonl`
- `data/eval/tourism_conversation_challenge.jsonl`
- `data/eval/tourism_intent_seed_utterances.jsonl`
- `data/eval/tourism_intent_generated_utterances.jsonl`
- `data/eval/tourism_intent_aihub_utterances.jsonl`

AI Hub 원본은 `data/external/aihub/raw/`에 두고 git에는 포함하지 않는다. `data/eval/tourism_intent_aihub_holdout.jsonl`은 학습에 넣지 않는 독립 holdout이다.
`data/eval/tourism_intent_adversarial_holdout.jsonl`도 학습에 넣지 않는 평가 전용 파일이다. 기존 회귀셋을 반복 학습하는 착시를 줄이기 위해 짧은 후속 질문, 조건 추가/교체, 지역 변경, 미지원 요청을 일부러 헷갈리게 만든다.

`data/eval/tourism_expanded_questions.jsonl`, `data/eval/tourism_expanded_conversation_challenge.jsonl`은 챗봇 품질 평가 전용이다. 이 파일들은 의도 분류기 학습에 넣지 않는다.

2026-05-16 기준:

| 항목 | 값 |
|---|---:|
| seed 발화 | 163 |
| 생성 발화 | 13,200 |
| AI Hub 학습 발화 | 2,700 |
| AI Hub 독립 holdout | 497 |
| 최종 학습 rows | 16,254 |
| train rows | 12,999 |
| test rows | 3,255 |
| 내부 holdout accuracy | 0.9164 |
| AI Hub holdout accuracy | 0.9115 |
| adversarial holdout rows | 2,420 |
| adversarial holdout accuracy | 0.8438 |
| AI Hub + adversarial combined accuracy | 0.8553 |

label은 `recommend_places`, `show_more`, `live_topup`, `ask_source`, `add_condition`, `replace_condition`, `exclude_preference`, `change_region`, `narrow_region`, `clarify_region`, `unsupported_request`다.

## Ablation 결과

2026-05-16에 `scripts/benchmark_tourism_intent_ablation.py`로 rule-only, 프로젝트 seed/generated, AI Hub 추가, Hugging Face external 추가 조건을 비교했다. 평가 대상은 학습에 넣지 않은 `data/eval/tourism_intent_aihub_holdout.jsonl` 497건과 `data/eval/tourism_intent_adversarial_holdout.jsonl` 2,420건이다.

| 조건 | 학습 rows | 전체 accuracy | AI Hub holdout | adversarial holdout |
|---|---:|---:|---:|---:|
| rule-only | 0 | 0.5605 | 0.3742 | 0.5988 |
| project seed/generated | 13,554 | 0.7854 | 0.4245 | 0.8595 |
| project + AI Hub | 16,254 | 0.8745 | 0.9034 | 0.8686 |
| project + AI Hub + HF external | 25,362 | 0.8632 | 0.8793 | 0.8599 |

판정:

- AI Hub 발화는 의미가 있다. project seed/generated 대비 전체 accuracy가 0.7854에서 0.8745로 올랐고, AI Hub holdout은 0.4245에서 0.9034로 크게 올랐다.
- rule-only는 전체 0.5605에 그쳐 후속 발화 분류 보조에는 부족하다.
- Hugging Face external 발화를 그대로 섞은 조건은 현재 holdout에서 0.8745에서 0.8632로 떨어졌다. 따라서 기본 런타임 모델에는 넣지 않고 실험/재라벨링 후보로만 둔다.

결과 파일은 `data/generated/tour_api/intent_ablation_latest.json`에 생성된다. 이 파일은 생성 산출물이므로 커밋 대상이 아니다.

## Latency 결과

2026-05-16에 `scripts/benchmark_tourism_latency.py`로 분류기와 direct fallback 답변 시간을 측정했다.

| 항목 | 값 |
|---|---:|
| classifier load | 19.1482ms |
| classifier predict count | 12,000 |
| classifier predict mean | 0.0040ms |
| classifier predict p50 | 0.0044ms |
| classifier predict p95 | 0.0055ms |
| classifier predict max | 0.2064ms |
| direct fallback chat count | 80 |
| direct fallback chat mean | 39.5892ms |
| direct fallback chat p50 | 3.4295ms |
| direct fallback chat p95 | 95.6137ms |
| direct fallback chat max | 1165.8930ms |

분류기 모델은 `get_tourism_query_service()` 캐시를 통해 프로세스당 한 번 로드된다. 예측 시간은 p95 0.0055ms 수준이라 사용자 답변 지연에는 사실상 영향을 주지 않는다. 현재 지연은 Chroma 검색 초기화, 후보 카드 구성, 지역별 후보 수, live 조회 여부가 만든다.

결과 파일은 `data/generated/tour_api/latency_benchmark_latest.json`에 생성된다. 이 파일도 생성 산출물이므로 커밋 대상이 아니다.

## 문맥 해석 classifier

2026-05-16에 기존 intent classifier와 별도로 문맥 해석 계층을 추가했다. 이 계층은 카드를 직접 고르지 않고, 사용자 발화를 추천 필터가 해석할 수 있는 구조 신호로 바꾸는 shadow classifier다.

라벨은 다음 9개로 시작한다.

| label | 의미 |
|---|---|
| `strict_and` | 둘 다/모두/반드시 만족 |
| `soft_and` | 여러 조건을 말했지만 완화 가능 |
| `or_condition` | 수어 또는 자막처럼 OR 조건 |
| `add_condition` | 이전 추천에 조건 추가 |
| `replace_condition` | 이전 조건 교체 |
| `exclude_condition` | 특정 조건/장소 유형 제외 |
| `family_context` | 아이/가족/영유아 맥락 |
| `mobility_context` | 걷기 힘듦/이동 편함/계단 회피 |
| `specific_facility_required` | 점자블록/주차/화장실/기저귀 교환대처럼 필수 근거 |

이 라벨은 자연어 문맥 전체를 덮는 완성형 분류가 아니다. 추천 로직의 행동을 바꾸는 위험한 판단 축만 우선 분리한 것이다. 새 실패 유형이 반복되면 `time_constraint`, `weather_context`, `crowd_avoidance`, `route_accessibility`, `uncertain_requirement` 같은 라벨을 추가한다.

현재 파일:

- 구현: `app/services/tourism_context_classifier.py`
- 학습셋 생성: `scripts/generate_tourism_context_interpretation_data.py`
- 학습: `scripts/train_tourism_context_classifier.py`
- 평가: `scripts/eval_tourism_context_classifier.py`
- 학습셋: `data/processed/tourism_context_training.jsonl`
- hard holdout: `data/eval/tourism_context_hard_holdout.jsonl`
- 모델 파일: `data/processed/tourism_context_classifier.json`

2026-05-17 기준 기본 학습셋은 4,400건, 학습 템플릿과 분리한 hard holdout은 4,800건이다. 이후 hard-style extra train과 blind-style extra train을 추가해 fine-tuning split은 train 6,886건, validation 1,200건, locked test 4,800건으로 갱신했다. `유모차`의 이동/가족 맥락 분리, 시설명 단독 문장, OR/strict 경계, `주차 말고 주제가 독특한 곳`, `추측하지 말고`, `A는 그만하고 B` 같은 문맥 반례를 추가했다. 교체 문장은 버린 조건이 아니라 새 조건 쪽의 시설/이동/가족 라벨을 정답으로 보도록 보정했다.

| 모델 | exact match | micro-F1 | 평균 예측 시간 | 판단 |
|---|---:|---:|---:|---|
| rule-only | 1.0000 | 1.0000 | 0.03ms 안팎 | independent validation 기준 경계 회귀셋 통과. 품질 지표로 단독 사용 금지 |
| Naive Bayes | 0.8929 | 0.9572 | 0.98ms 안팎 | extra train 반영 후 단독 NB 개선 |
| LinearSVC + char n-gram | 0.6062 | 0.8314 | 0.33ms 안팎 | 단독 모델은 여전히 구조 라벨 recall이 부족 |
| LogisticRegression + char n-gram | 0.6921 | 0.8741 | 0.33ms 안팎 | 단독 모델 중 최고지만 런타임 판단자로는 부족 |
| Hybrid LinearSVC | 1.0000 | 1.0000 | 0.36ms 안팎 | independent validation 기준 경계 회귀셋 통과 |
| Hybrid LogisticRegression | 1.0000 | 1.0000 | 0.36ms 안팎 | independent validation 기준 경계 회귀셋 통과 |

실패 분석 뒤 명확한 구조 표현을 rule로 보강하고, Linear 예측과 병합하는 hybrid 후처리를 추가했다. 최신 locked test 기준 Hybrid LogisticRegression은 exact 0.9706, micro-F1 0.9860이며 주요 잔여 bucket은 `soft_and` 누락과 `add_condition` 과잉이다. `soft_and`는 단순 복합 조건이 아니라 참고/선택/완화 의도가 명시된 문장으로 좁혔고, `아니면 제외/근거 없으면 빼줘`는 단순 제외가 아니라 strict 필수 조건으로 분리했다.

`specific_facility_required`의 locked test 1.0000은 성능 증명으로 보지 않는다. 이 수치를 의심해 `data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl` 980건을 추가했고, 최초 hybrid exact 0.7102/micro-F1 0.8809로 약점이 드러났다. `추측 말고`, `조건은 묻지 않아`, `둘 중 하나만 되는 곳은 제외` 경계를 보강한 뒤 최신 adversarial holdout은 exact 0.9929, micro-F1 0.9950이다. 이 focused 결과는 품질 점수에서 제외하고 새 반례를 계속 추가하는 경계 방어선으로만 사용한다.

재실험 기준:

- hard-style validation split을 별도로 만든 뒤 epoch/threshold/model selection에 사용한다.
- locked hard holdout 4,800건은 최종 비교용으로 유지한다.
- LinearSVC, LogisticRegression, KoBERT/KLUE-RoBERTa는 같은 train/hard-validation/locked-test 조건으로 다시 비교한다.
- `scripts/audit_tourism_ml_experiment.py`가 `missing_hard_validation`을 내면 해당 결과는 exploratory로만 취급한다.

2차 후보 검토:

- Hugging Face에서 확인한 실제 후보는 `klue/roberta-base`, `klue/roberta-small`, `bespin-global/klue-roberta-small-3i4k-intent-classification`이다.
- `klue/roberta-base`는 110.7M parameters, `klue/roberta-small`은 68.1M parameters다.
- `bespin-global/klue-roberta-small-3i4k-intent-classification`은 한국어 intent classification fine-tuned 모델이지만 license가 `cc-by-nc-4.0`이라 상용/공개 서비스 기본 후보로는 주의가 필요하다.
- 한때 현재 작성된 locked test에서 hybrid LogisticRegression이 1.0000까지 올라 숫자상 headroom이 없어 보였지만, 이후 fresh rotating blind에서는 micro-F1 0.8163으로 떨어졌다. 같은 rotating 파일을 보고 룰을 보강한 뒤 0.9919까지 올랐지만, 이 수치는 tuned diagnostic이다. 다음 2차 모델 비교 전에는 새로운 independent/rotating holdout을 먼저 추가해야 한다.

결론: MVP 기본 런타임은 규칙+기존 query filter를 유지하고, 문맥 해석 shadow 결과를 로그/QA에 누적한다. KoBERT/KLUE-RoBERTa fine-tuning은 이제 파일럿 실험을 진행할 수 있는 데이터 규모에는 도달했지만, 기본 경로 교체는 hybrid LogisticRegression 대비 micro-F1 +0.02 이상, exact 상승, latency 허용 범위 확인 뒤 결정한다.

### 독립 validation 재설계

2026-05-17에 기존 validation 1.0000 문제를 실패 신호로 보고 split 기준을 다시 잡았다. 무작위 split이나 같은 template family 공유를 허용하지 않고, 별도 생성 family 10개로 독립 validation 1,200건을 만들었다.

| split | rows | 용도 |
|---|---:|---|
| train | 6,886 | fine-tuning 학습. 기존 학습셋 + hard-style extra train + blind-style extra train |
| validation | 1,200 | 생성 family가 train과 겹치지 않는 독립 hard validation |
| test | 4,800 | locked hard test. 최종 비교 전용 |

파일:

- `data/processed/context_finetune/train.jsonl`
- `data/processed/context_finetune/validation.jsonl`
- `data/processed/context_finetune/test.jsonl`
- `data/processed/context_finetune/labels.json`

각 row는 `text`, `labels`, `label_vector`, `label_text`, `category`, `source`, `template_family`를 가진다. `scripts/prepare_tourism_context_finetune_data.py --validation-ratio 0 --hard-validation-input data/eval/tourism_context_independent_validation.jsonl --strict-family-split`는 train/validation 사이 family overlap과 text overlap이 있으면 실패한다.

독립 validation은 한 차례 1.0000 착시를 줄였지만, 이후 경계 표현을 다시 rule로 정리하면서 현재 작성된 validation은 다시 1.0000이 됐다. 따라서 이 validation은 모델 일반화 점수가 아니라 경계 회귀셋으로만 본다.

| 모델 | independent validation exact | independent validation micro-F1 | 판단 |
|---|---:|---:|---|
| rule-only | 1.0000 | 1.0000 | 현재 작성된 validation family 통과. 품질 점수 아님 |
| LinearSVC | 0.5300 | 0.7637 | 단독 선형 모델도 부족 |
| LogisticRegression | 0.5892 | 0.8065 | validation 기준 최고 단독 모델 |
| Hybrid LogisticRegression | 1.0000 | 1.0000 | rule 구조 신호 병합 뒤 경계 회귀셋 통과 |

이 validation은 점수를 높이기 위한 목표셋이 아니라 실패 유형을 찾는 진단셋이다. 현재는 sample mismatch가 0건이므로, 다음 작업은 같은 파일을 더 돌리는 것이 아니라 새로운 family와 사람이 쓴 듯한 멀티턴 holdout을 추가해 다시 깨는 것이다.

### LLM blind holdout

사람이 직접 쓴 holdout을 당장 확보할 수 없으므로, 기존 generator family를 재사용하지 않는 Codex LLM blind holdout을 별도 작성했다.

| 평가셋 | rows | 모델 | exact | micro-F1 | 판단 |
|---|---:|---|---:|---:|---|
| `tourism_context_blind_holdout.jsonl` | 80 | rule-only | 0.4750 | 0.7304 | 최초 blind. 회귀셋 1.0000 착시가 깨짐 |
| `tourism_context_blind_holdout.jsonl` | 80 | LogisticRegression 단독 | 0.5125 | 0.7512 | 최초 blind 최고 기준선 |
| `tourism_context_blind_holdout.jsonl` | 80 | Hybrid LogisticRegression | 0.4500 | 0.7296 | 최초 blind에서 rule 병합 일부 악화 |
| `tourism_context_blind_holdout.jsonl` | 80 | Hybrid LinearSVC | 0.6250 | 0.8340 | 보강 후 tuned diagnostic. 최종 품질 점수 아님 |
| `tourism_context_rotating_blind_holdout_20260517.jsonl` | 80 | Hybrid LinearSVC | 0.5750 | 0.8163 | 최초 fresh blind. 약점 확인 |
| `tourism_context_rotating_blind_holdout_20260517.jsonl` | 80 | Hybrid LinearSVC | 0.9750 | 0.9919 | 같은 파일 보강 후 tuned diagnostic |

blind holdout에서 드러난 약점은 `둘 중 하나라도 빠지면`, `엘베`, `패스`, `애기`, `유아 의자`, `후보 적을 때만 가산점`, `주차 말고 주제` 같은 실제 발화형 표현이다. 이 파일에서 찾은 bucket은 train-only extra data 생성에 사용했으므로, 이후 품질 판단은 같은 파일 반복 점수가 아니라 새 rotating blind 점수로 본다.

같은 기준으로 실제 `/tourism/chat` 카드 응답을 보는 `tourism_context_blind_chat_eval.jsonl` 10건을 추가했다. 최초 fallback-only direct 실행 결과는 9/10 통과였고, `전주에서 시장 골목 말고 조용한 곳만 보고 싶어`가 `card_count_low`로 실패했다. 시장 제외 파싱, 취소/제외 표현 window, 선호 조건 hard filter를 보정한 뒤 최신 fallback-only direct 실행은 10/10 통과한다. 이는 context label 정확도와 별개로 실제 후보 검색/랭킹/부족 안내를 함께 봐야 한다는 신호다.

### 2차 fine-tuning 파일럿 결과

2026-05-17에 `requirements-ml.txt`로 PyTorch/Transformers 의존성을 분리 설치하고, `klue/roberta-small` multi-label classifier 파일럿과 grid 실험을 실행했다. 학습 스크립트는 `scripts/train_tourism_context_transformer.py`, grid runner는 `scripts/grid_tourism_context_transformer.py`이고, 결과 원본은 git ignore 대상인 `data/generated/tour_api/context_transformer_pilot/metrics.json`, `data/generated/tour_api/context_transformer_grid_latest.json`에 쓴다.

실행:

```bash
.venv/bin/python -m pip install -r requirements-ml.txt
.venv/bin/python scripts/train_tourism_context_transformer.py --epochs 2 --batch-size 16 --model-name klue/roberta-small
.venv/bin/python scripts/grid_tourism_context_transformer.py --epochs 3,5 --batch-sizes 16,32 --learning-rates 1e-5,2e-5
```

초기 파일럿 결과:

| 모델 | exact match | micro-F1 | 평균 예측 시간 | 판단 |
|---|---:|---:|---:|---|
| Hybrid LogisticRegression 기준선 | 0.8927 | 0.9379 | 0.3518ms | 초기 기준선 |
| KLUE-RoBERTa small 단독 | 0.6746 | 0.8499 | 1.0012ms | hard holdout 일반화 부족 |
| KLUE-RoBERTa small + rule hybrid | 0.8894 | 0.9383 | 1.0012ms | micro-F1은 거의 같지만 exact/latency에서 기준선 우위 |

Hard-style extra train 반영 뒤 초기 grid 결과는 validation이 1.0000에 가까워 실패 신호로 판정했다.

| run | validation exact / micro-F1 | standalone test exact / micro-F1 | hybrid test exact / micro-F1 | 기준선 대비 이득 | 평균 예측 시간 | 판단 |
|---|---:|---:|---:|---:|---:|---|
| e3_b16_lr1e-5 | 1.0000 / 1.0000 | 0.6829 / 0.8430 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 1.0186ms | 미채택 |
| e3_b16_lr2e-5 | 1.0000 / 1.0000 | 0.7129 / 0.8563 | 0.8969 / 0.9414 | +0.0000 / -0.0005 | 1.0094ms | 미채택 |
| e3_b32_lr1e-5 | 0.9993 / 0.9998 | 0.6790 / 0.8351 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 0.8759ms | 미채택 |
| e3_b32_lr2e-5 | 1.0000 / 1.0000 | 0.6821 / 0.8446 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 0.8565ms | best 동률, 미채택 |
| e5_b16_lr1e-5 | 1.0000 / 1.0000 | 0.7277 / 0.8651 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 1.0124ms | 미채택 |
| e5_b16_lr2e-5 | 1.0000 / 1.0000 | 0.7223 / 0.8535 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 1.0196ms | 미채택 |
| e5_b32_lr1e-5 | 1.0000 / 1.0000 | 0.6983 / 0.8526 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 0.8763ms | 미채택 |
| e5_b32_lr2e-5 | 1.0000 / 1.0000 | 0.7204 / 0.8611 | 0.8969 / 0.9419 | +0.0000 / +0.0000 | 0.8863ms | 미채택 |

판정:

- validation은 1.0000까지 올라갔지만 hard holdout은 단독 micro-F1 0.8499에 그쳤다. 이는 문맥 이해가 충분히 된 것이 아니라 쉬운 train/validation 템플릿을 외운 신호에 가깝다.
- hard-style extra train을 넣고 epoch/batch/lr grid를 돌려도 hybrid test는 최고 기준선과 동률일 뿐, 채택 기준인 micro-F1 +0.02와 exact 상승을 만족하지 못했다.
- rule hybrid를 붙이면 기준선 수준으로 복구되지만, 이 성능은 transformer가 새 문맥을 해결했다기보다 기존 rule 후처리의 효과가 크다. latency도 선형 기준선보다 약 2.5-3배 높다.
- 따라서 현재 `klue/roberta-small` 파일럿과 grid 결과는 기본 런타임 교체 대상이 아니다. 다음 딥러닝 실험은 모델 epoch를 늘리는 것이 아니라, train/validation/test를 생성 batch와 템플릿 family 단위로 분리하고, 실제 독립 LLM/human-style holdout을 만든 뒤 다시 비교해야 한다.
- 실험 감사는 `.venv/bin/python scripts/audit_tourism_ml_experiment.py`로 실행한다. 현재 결과는 validation-hard gap 때문에 `do_not_adopt_runtime`으로 판정된다.
- Codex/LLM으로 hard-style 학습셋을 생성할 때는 `.venv/bin/python scripts/build_tourism_context_llm_generation_prompt.py`로 프롬프트를 만들고, `.venv/bin/python scripts/validate_tourism_context_llm_dataset.py --input ...`으로 schema/라벨/중복/누수를 검수한 뒤 `prepare_tourism_context_finetune_data.py --extra-train-input ...`으로만 병합한다. 세부 절차는 `docs/tourism/context_llm_dataset_generation.md`를 따른다.

독립 validation 적용 뒤 같은 `klue/roberta-small`, epoch 3, batch 32, lr 2e-5 조건으로 재실험했다.

| 모델 | validation exact / micro-F1 | locked test exact / micro-F1 | 평균 예측 시간 | 판단 |
|---|---:|---:|---:|---|
| Hybrid LogisticRegression 기준선 | - | 1.0000 / 1.0000 | 0.36ms 안팎 | 현재 경계 회귀셋 통과 기준선. 품질 점수 아님 |
| KLUE-RoBERTa small 단독 | 0.8417 / 0.9241 | 0.7165 / 0.8594 | 0.8859ms | validation은 현실화됐지만 test 일반화 부족 |
| KLUE-RoBERTa small + rule hybrid | - | 0.8969 / 0.9474 | 0.8859ms | 기준선과 동률 이하, latency 불리 |

감사 결과는 `do_not_adopt_runtime`이다. validation-hard micro-F1 gap 0.0647, 기준선 대비 +0.02 미달, exact 미개선, latency 2배 이상 악화가 동시에 잡혔다. 따라서 지금 조정할 대상은 epoch/batch가 아니라 독립 family 확대, 라벨 모호성 정리, 오류 bucket 기반 data generation이다.

### SuperGemma4 문맥 라벨링 실험

2026-05-17에 이전 hard holdout 1,320건에서 `hybrid LogisticRegression`이 틀린 221건만 추출해 SuperGemma4로 JSON 라벨링을 시켰다. 이후 hard holdout은 4,800건으로 확장됐으므로, 이 수치는 SuperGemma4의 최종 채택 지표가 아니라 초기 selective 호출 실험 결과로만 본다.

실행:

```bash
.venv/bin/python scripts/eval_supergemma_context_labels.py
```

결과:

| 항목 | 값 |
|---|---:|
| 대상 모델 | `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` |
| hybrid mismatch rows | 221 |
| SuperGemma 단독 exact on mismatch | 0.3303 |
| baseline full exact | 0.8326 |
| selective full exact | 0.8879 |
| baseline full micro-F1 | 0.9179 |
| selective full micro-F1 | 0.9105 |
| latency mean | 2191.1ms |
| latency p50 | 2159.8ms |
| latency p95 | 3028.6ms |
| latency max | 5866.4ms |

판정:

- SuperGemma4는 `replace_condition`처럼 문장 의미가 필요한 일부 오답을 맞혀 full exact match를 `0.8326`에서 `0.8879`로 올렸다.
- 하지만 과잉/누락 라벨이 늘어 full micro-F1은 `0.9179`에서 `0.9105`로 내려갔다.
- 특히 `strict_and_missed` 30건, `specific_facility_missed` 12건, `mobility_context`/`specific_facility_required` 과잉이 남았다.
- 따라서 현재 프롬프트 방식의 SuperGemma4는 기본 런타임 보조 판단자로 채택하지 않는다.
- 다만 평균 약 2.2초, p95 약 3.0초 수준이라 “개발/QA용 재라벨링 보조”나 “오답 후보 설명 생성”에는 사용할 가치가 있다.

## Gemini independent holdout

2026-05-16에 Gemini로 AI-generated independent holdout을 만들고, 같은 Gemini 모델로 2차 라벨 검수를 돌렸다. 이 데이터는 사람 작성 holdout이 아니므로 모델 학습에 넣지 않고 평가/문제 탐색에만 쓴다.

| 항목 | 값 |
|---|---:|
| 생성 모델 | `gemini-2.5-flash` |
| raw 생성 rows | 770 |
| 2차 검수 통과 rows | 676 |
| 2차 검수 탈락 rows | 94 |
| 개선 전 classifier accuracy | 0.5488 |
| 1차 개선 후 classifier accuracy | 0.7308 |
| 2차 hard holdout 보강 후 classifier accuracy | 0.8536 |

검수 통과 row 수와 현재 classifier baseline:

| intent | rows | accuracy |
|---|---:|---:|
| `add_condition` | 65 | 0.7846 |
| `ask_source` | 69 | 0.8986 |
| `change_region` | 62 | 0.6774 |
| `clarify_region` | 35 | 1.0000 |
| `exclude_preference` | 53 | 0.7547 |
| `live_topup` | 66 | 0.6061 |
| `narrow_region` | 61 | 0.6721 |
| `recommend_places` | 69 | 0.7971 |
| `replace_condition` | 58 | 0.7414 |
| `show_more` | 70 | 0.5571 |
| `unsupported_request` | 68 | 0.6765 |

`clarify_region` 35/35는 표본이 작고 특정 생성/검수 분포에 묶인 부분 집합 결과라 단독 품질 지표로 쓰지 않는다.

판정:

- Gemini verified holdout에서 드러난 약점을 바탕으로 일반화 가능한 rule override를 보강했다. 2026-05-16 현재 전체 accuracy는 0.8536이다.
- 기존 AI Hub/adversarial holdout도 0.8553에서 0.8745로 올라 회귀는 발생하지 않았다.
- 3차 change/replace 보강 뒤 Gemini verified holdout은 0.8536, AI Hub/adversarial holdout은 0.9229다. 다만 Gemini 기준 `change_region`, `replace_condition`은 단발 문장만으로는 label 경계가 애매한 실제 문장이 남아 별도 대화 맥락 평가가 필요하다.
- 이 holdout으로 개선을 반복하면 독립성이 약해지므로, 다음부터는 개선 전/후 수치를 명확히 남기고 학습셋에는 넣지 않는다.

## Hard intent holdout

2026-05-16에 `show_more`, `live_topup`, `unsupported_request`, `clarify_region`, `narrow_region` 경계 케이스를 의도적으로 많이 섞은 deterministic hard holdout을 추가했다. 이 파일도 학습셋에 넣지 않고 rule 변경 전/후 회귀 확인용으로만 쓴다.

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_intent_hard_holdout.jsonl` |
| 생성 스크립트 | `scripts/generate_tourism_intent_hard_holdout.py` |
| rows | 990 |
| label별 rows | 90 |
| 2차 보강 전 accuracy | 0.8566 |
| 2차 보강 후 accuracy | 0.9939 |
| change/replace 보강 후 accuracy | 0.9747 |

2차 보강은 다음 오분류를 줄이는 데 집중했다.

- `조건을 추가해줘`, `까지 봐줘` 같은 후속 조건 추가를 live 보강으로 오인하지 않게 했다.
- `현재 카드 다음 5곳`, `다른 옵션`, `남은 정보` 같은 표현을 `show_more`로 잡게 했다.
- `실시간 혼잡도`, `버스 소요시간`, `영업 여부`, `티켓/예매/웨이팅` 같은 범위 밖 요청을 `unsupported_request`로 우선 판정한다.
- `중구/동구/고성군`처럼 광역이 빠진 중복 지명은 조건 단어가 섞여도 `clarify_region`을 먼저 반환한다.
- `부산 중구 여행 정보`처럼 광역이 붙은 명시 추천은 `narrow_region`으로 과잉 분류하지 않는다.

## Region clarify stress holdout

Gemini verified holdout의 `clarify_region`은 35건뿐이라 단독 지표로는 신뢰하기 어렵다. 이를 보완하기 위해 애매 지명 전용 holdout을 두 종류로 분리했다. 두 파일 모두 학습셋에 넣지 않고 평가 전용으로만 쓴다.

첫째는 deterministic rule-boundary stress다. 이 지표는 의도적으로 규칙 경계를 정확히 확인하는 contract/regression 테스트다. `pytest`처럼 깨지면 안 되는 정책 계약으로만 쓰고, 모델 품질 점수나 실사용 일반화 성능 지표에는 포함하지 않는다. 1.0000이 나온다면 "좋은 모델"이라는 뜻이 아니라 현재 작성된 경계 규칙을 어기지 않았다는 뜻이다.

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_intent_region_clarify_stress.jsonl` |
| 생성 스크립트 | `scripts/generate_tourism_intent_region_clarify_stress.py` |
| 전체 rows | 960 |
| `clarify_region` rows | 600 |
| `recommend_places` 반례 rows | 180 |
| `narrow_region` 반례 rows | 180 |
| 현재 전체 accuracy | 1.0000 |
| 현재 `clarify_region` accuracy | 1.0000 |
| 품질 점수 포함 여부 | 제외 |

이 stress set은 다음 정책 경계가 깨졌는지만 확인한다.

둘째는 자연형 region clarify holdout이다. 이 파일은 `중구라면 어디 중구 말하는 거야`, `강서구는 서울인지 부산인지`, `중구 중에서도 서울 중구만`처럼 템플릿 냄새를 줄인 축약/반문/혼동 표현을 섞어 1.000 착시를 피하는 주 지표로 쓴다.

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_intent_region_clarify_natural_holdout.jsonl` |
| 생성 스크립트 | `scripts/generate_tourism_intent_region_clarify_natural_holdout.py` |
| 전체 rows | 600 |
| `clarify_region` rows | 300 |
| `recommend_places` 반례 rows | 140 |
| `narrow_region` 반례 rows | 100 |
| `change_region` 반례 rows | 60 |
| 현재 전체 accuracy | 0.9800 |
| 현재 `clarify_region` accuracy | 1.0000 |

판정:

- Gemini의 `clarify_region` 35건 문제는 자연형 holdout 300건과 rule-boundary 600건으로 보완한다.
- `region_clarify_stress`의 1.0000은 contract/regression 통과 결과이며 품질 점수에서 제외한다. 이 수치는 실사용 가능성을 주장하는 근거가 아니라, 새 반례를 추가하기 전의 최소 방어선이다.
- 실질 추적 지표는 `region_clarify_natural_holdout`의 전체 0.9800으로 본다. 부분 집합인 `clarify_region` 300/300 통과는 보조 정보이며, 1.0000이라고 해서 단독 품질 지표로 쓰지 않는다. 부분 셋이 계속 1.0000이면 더 까다로운 반례를 추가해야 한다.
- 새 AI-generated holdout을 만들 때는 Gemini API 대신 Codex `gpt-5.4-mini` 또는 `gpt-5.3-codex-spark` 계열로 별도 파일을 만들고, 기존 Gemini/hard/stress/natural 파일과 섞지 않는다.

## Change/replace follow-up holdout

`change_region`과 `replace_condition`은 단발 문장만 보면 `recommend_places`, `exclude_preference`와 경계가 흔들리기 쉽다. 그래서 실제 채팅 후속 질문에 가까운 지역 변경, 조건 교체, 단순 제외, 조건 추가 반례를 섞은 focused regression holdout을 추가했다.

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_intent_change_replace_natural_holdout.jsonl` |
| 생성 스크립트 | `scripts/generate_tourism_intent_change_replace_natural_holdout.py` |
| 전체 rows | 600 |
| `change_region` rows | 180 |
| `replace_condition` rows | 180 |
| 반례 rows | 240 |
| 현재 전체 accuracy | 1.0000 |
| 품질 점수 포함 여부 | 제외 |

이 결과는 `region_clarify_stress`처럼 실사용 일반화 지표로 보지 않는다. `A 말고 B`, `다른 지역으로`, `조건 추가`, `단순 제외`의 정책 경계가 깨졌는지 빠르게 확인하는 회귀 방어선으로만 쓴다.

## Change/replace chat judgment holdout

실사용 가능 판단은 의도 분류 단독 accuracy가 아니라 `/tourism/chat`의 최종 응답을 기준으로 본다. 그래서 지역 변경, 조건 교체, 단순 제외, 더 보기 유지, 맥락 없는 조건 요청을 실제 API 응답 카드/답변으로 채점하는 멀티턴 판단셋을 추가했다.

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_change_replace_chat_holdout.jsonl` |
| 생성 스크립트 | `scripts/generate_tourism_change_replace_chat_holdout.py` |
| 전체 rows | 201 |
| 평가 방식 | `/tourism/chat` direct 호출 |
| 현재 결과 | 201/201 통과 |
| 품질 판단 사용 | 가능, 단 표본 수와 함께 표기하고 단독 점수로는 사용하지 않음 |

이 셋은 다음을 카드/답변 기준으로 확인한다.

- 지역 전환 후 이전 지역 카드가 남지 않는지
- 조건 교체 후 새 조건 근거가 있는 카드가 반환되는지
- 단순 제외가 조건 교체나 지역 변경으로 오인되지 않는지
- 조건 교체/제외 후 `더 보기`에서도 지역과 조건이 유지되는지
- 지역 맥락이 없는 조건 교체/제외 요청은 억지 추천 대신 지역 확인으로 이어지는지
- 간접 접근성 표현, 과거 지명 뒤 지역 전환, 광역/시군구 전환, 조사형 제외 표현이 대화 맥락에서 깨지지 않는지

현재 201/201 통과지만 같은 생성기에서 만든 focused 멀티턴 셋이므로 단독 품질 점수로 과대 해석하지 않는다. 이 셋은 focused intent holdout보다 실사용 판단에 가깝고, 다음 보강은 지역/조건 조합을 더 넓히면서 실패 케이스를 별도 backlog로 분리하는 것이다.

201건 확장 과정에서 실제 결함을 수정했다.

- `서귀포시 말고 제주시`처럼 `말고` 앞 지역이 짧은 alias로 먼저 잡히는 문제를 수정했다.
- `시장 말고 실내 박물관`처럼 `말고` 뒤의 새 선호를 제외 선호로 오인하지 않게 했다.
- `replace_condition` 후속 질문에서 이전 조건/선호가 계속 누적되어 검색을 왜곡하던 병합 규칙을 교체 방식으로 바꿨다.
- `남제주군 말고 제주시`처럼 과거 지명이 `말고` 앞에 있을 때도 legacy alias가 계속 우선되는 문제를 수정했다.
- `강릉 말고 서울`처럼 시군구에서 광역으로 바꿀 때 이전 `sigungu_code`가 새 지역에 섞이는 문제를 수정했다.
- `숙박은 빼고`, `카페는 빼고`처럼 조사가 붙은 제외 표현을 놓치는 문제를 수정했다.
- `더 보기`에서 후보 리스트가 전체 fallback으로 풀리지 않도록 광역/시군구 지역 필터를 주소 기준으로 유지하게 했다. 유효 후보가 20장을 넘어도 임의 상한을 두지 않는다. 20장 이상 반환 케이스는 전수 검사해 지역 오류와 요청 조건 근거 누락이 없음을 확인했다.

Adversarial chat holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_adversarial_chat_holdout.jsonl` |
| rows | 42 |
| 생성 스크립트 | `scripts/generate_tourism_adversarial_chat_holdout.py` |
| 평가 명령 | `TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_adversarial_chat_holdout.jsonl --output data/generated/tour_api/eval_runs/tourism_adversarial_chat_holdout_latest.jsonl` |
| 현재 결과 | 42/42 통과 |

이 파일은 홍보용 품질 점수가 아니라 실패 탐색용이다. 조사형 제외, 이중 `말고`, 과거 지명 후 지역 전환, 맥락 없는 후속 표현, 중복 지명 clarification처럼 실제 대화에서 깨지기 쉬운 경계를 따로 모은다.

생성/검수 명령:

```bash
GEMINI_API_KEY=... .venv/bin/python scripts/generate_tourism_intent_gemini_holdout.py --target 770
GEMINI_API_KEY=... .venv/bin/python scripts/verify_tourism_intent_gemini_holdout.py --batch-size 25 --timeout 90 --max-retries 4
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_gemini_holdout_verified.jsonl
```

주의:

- Gemini API holdout은 현재 생성된 676건을 고정 평가 자산으로 둔다.
- API limit과 키 관리 부담 때문에 신규 AI-generated independent holdout은 Gemini API를 기본으로 쓰지 않는다.
- 새 holdout을 만들어야 하면 Codex에서 `gpt-5.4-mini` 또는 `gpt-5.3-codex-spark` 계열을 사용해 생성하고, 기존 Gemini holdout과 hard holdout에는 섞지 않는다.
- 새 AI 생성 holdout도 학습셋에 바로 넣지 않고, 평가 전용 파일로 분리한 뒤 자동 검수/중복 제거/label별 분포 확인을 거친다.

산출물:

- `data/eval/tourism_intent_gemini_holdout.jsonl`: raw 생성본
- `data/eval/tourism_intent_gemini_holdout_verified.jsonl`: 2차 검수 통과본
- `data/generated/tour_api/gemini_holdout_report.json`: raw 생성 리포트
- `data/generated/tour_api/gemini_holdout_verified_report.json`: 검수 리포트

## 재생성 명령

프로젝트 루트에서 실행한다.

```bash
.venv/bin/python scripts/generate_tourism_intent_utterances.py
.venv/bin/python scripts/extract_aihub_tourism_intent_utterances.py
.venv/bin/python scripts/build_tourism_intent_training_set.py
.venv/bin/python scripts/train_tourism_intent_classifier.py
.venv/bin/python scripts/benchmark_tourism_intent_ablation.py
.venv/bin/python scripts/benchmark_tourism_latency.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_gemini_holdout_verified.jsonl
.venv/bin/python scripts/generate_tourism_intent_hard_holdout.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_hard_holdout.jsonl
.venv/bin/python scripts/generate_tourism_intent_region_clarify_stress.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_region_clarify_stress.jsonl
.venv/bin/python scripts/generate_tourism_intent_region_clarify_natural_holdout.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_region_clarify_natural_holdout.jsonl
```

빠른 검증:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_conversation_challenge.jsonl
.venv/bin/python -m pytest tests/test_tourism_intent_classifier.py tests/test_tourism_chat_service.py tests/test_tourism_query_service.py -q
```

전체 검증:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_100_questions.jsonl
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_challenge_questions.jsonl
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_conversation_challenge.jsonl
.venv/bin/python scripts/eval_tourism_intent_classifier.py
.venv/bin/python -m pytest -q
```

## 외부 데이터셋

AI Hub에서 받은 원본 3종 중 현재 모델에는 `용도별 목적대화 데이터`, `한국어 대화`, `웰니스 대화 스크립트 데이터셋`을 약한 규칙으로 재라벨링한 발화 일부를 반영한다. 기본 모델에는 `add_condition`, `recommend_places`, `unsupported_request`에 해당하는 고신뢰 발화만 넣고, AI Hub validation split은 독립 holdout으로 분리한다.

Hugging Face 데이터셋은 `data/eval/tourism_intent_external_utterances.jsonl`로 추출할 수 있지만 기본 학습에는 넣지 않는다. 실험할 때만 `scripts/build_tourism_intent_training_set.py --include-external`을 사용한다.

| 데이터셋 | 용도 |
|---|---|
| `neuralfoundry-coder/clinc150-ko` | 한국어 intent/out-of-scope 분류 기준선 |
| `AIWORKX/KoSGD` | 한국어 목적지향 대화, schema-guided intent/DST 참고 |
| `wicho/kor_3i4k` | 한국어 짧은 발화 intent 분류 참고 |
| `bitext/Bitext-travel-llm-chatbot-training-dataset` | 영어 travel chatbot intent/발화 패턴 참고 |

링크:

- <https://hf.co/datasets/neuralfoundry-coder/clinc150-ko>
- <https://hf.co/datasets/AIWORKX/KoSGD>
- <https://hf.co/datasets/wicho/kor_3i4k>
- <https://hf.co/datasets/bitext/Bitext-travel-llm-chatbot-training-dataset>

## 다음 고도화

1. 생성셋과 별도인 사람이 직접 쓴 holdout challenge를 label별 100개 이상 만든다.
2. `clarify_region`, `replace_condition`, `unsupported_request`의 실제 사용자 표현을 더 모은다.
3. Hugging Face 데이터셋은 그대로 섞지 말고 관광 챗봇 intent taxonomy에 맞춰 재라벨링하거나 증강용으로만 사용한다.
4. 모델 confidence가 낮으면 규칙 기반 결과만 사용한다.
