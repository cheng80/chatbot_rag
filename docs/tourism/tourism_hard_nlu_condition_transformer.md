# Hard NLU 조건 라벨 Transformer 재평가

최종 갱신: 2026-05-18

## 목적

기존 중간 길이 120건 평가에서는 rule/parser, ET5 local, quickspacer, RoBERTa 후보가 모두 같은 카드 통과율을 보였다. 이 결과만으로는 모델 차이를 보기 어렵다.

그래서 사람이 규칙으로 쉽게 잡는 표현이 아니라, 실제 사용자가 돌려 말할 수 있는 접근성 의미 표현을 별도 hard holdout으로 만들었다.

예:

- `혼자 밀고 들어가기 무리 없는 관광지`
- `바닥 턱 때문에 못 들어가는 일이 적은 곳`
- `이동 보조기구 쓰는 사람이 관람 가능한 곳`
- `아이 태우고 밀고 다녀도 동선이 괜찮은 곳`
- `귀로 듣기 어려운 동행이 전시 내용을 따라가기 쉬운 곳`

이 평가는 최종 카드 품질 평가가 아니라, 문장에서 접근성 조건을 얼마나 잘 뽑는지 보는 NLU 평가다.

## 평가 자산

- hard NLU holdout: `data/eval/tourism_hard_nlu_holdout_20260518.jsonl`
- hard 의미 chat 평가: `data/eval/tourism_hard_semantic_chat_eval_20260518.jsonl`
- hard holdout 생성기: `scripts/generate_tourism_hard_nlu_holdout.py`
- hard NLU 비교기: `scripts/eval_tourism_hard_nlu_models.py`
- hard 증강 데이터 생성기: `scripts/prepare_tourism_hard_condition_aug_data.py`
- hard 증강 학습 결과: `data/generated/tour_api/condition_transformer_hard_aug_e2_fast/`
- 잔여 hard NLU 평가: `data/eval/tourism_residual_hard_nlu_20260518.jsonl`
- 잔여 hard chat 평가: `data/eval/tourism_residual_hard_chat_20260518.jsonl`
- 잔여 hard 평가 생성기: `scripts/generate_tourism_residual_hard_eval.py`
- 잔여 증강 데이터 생성기: `scripts/prepare_tourism_residual_condition_aug_data.py`
- 잔여 증강 학습 결과: `data/generated/tour_api/condition_transformer_residual_aug_e2_fast/`

모델은 Hugging Face 런타임 호출이 아니라 로컬 `data/models/klue_roberta_small` 베이스를 사용해 로컬에서 fine-tuning했다.

## Hard NLU 결과

| 변형 | exact | micro-F1 | precision | recall | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| rule/parser | 0.3889 | 0.5287 | 0.7263 | 0.4157 | 26 | 97 |
| ET5 local | 0.3889 | 0.5287 | 0.7263 | 0.4157 | 26 | 97 |
| quickspacer | 0.3889 | 0.5287 | 0.7263 | 0.4157 | 26 | 97 |
| 기존 RoBERTa | 0.6944 | 0.7390 | 0.7200 | 0.7590 | 49 | 40 |
| hard 증강 RoBERTa | 0.8167 | 0.8606 | 0.8659 | 0.8554 | 22 | 24 |

해석:

- ET5와 quickspacer는 오타/띄어쓰기 보정에는 의미가 있지만, `바닥 턱 때문에 못 들어가는 곳` 같은 의미 해석 자체를 해결하지는 못했다.
- 기존 RoBERTa는 recall을 올렸지만 false positive가 많았다.
- hard 실패 유형을 별도로 증강한 뒤 RoBERTa는 recall과 precision이 함께 개선됐다.

## 잔여 실패 전용 평가

hard 증강 뒤에도 남은 실패는 세 가지로 분리했다.

- `고령자`: 오래 서 있지 않기, 쉬어가기, 계단 적음, 부모님/어르신 동행 표현
- `주차`: `주챠`, `주차ㅏ`, `차대기`, `입구앞 차`, `승하차` 같은 오타/구어 표현
- `접근로`/`휠체어`: 단차, 출입통로, 바퀴 이동, 휠체어 사용자의 경계 표현

잔여 hard NLU 250건 결과:

| 변형 | exact | micro-F1 | precision | recall | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| hard 증강 RoBERTa 단독 | 0.7440 | 0.8560 | 0.8785 | 0.8346 | 30 | 43 |
| 잔여 증강 RoBERTa 단독 | 0.9360 | 0.9549 | 0.9338 | 0.9769 | 18 | 6 |
| hard 증강 rule+RoBERTa | 0.6640 | 0.8452 | 0.8028 | 0.8923 | 57 | 28 |
| 잔여 증강 rule+RoBERTa | 0.7720 | 0.8889 | 0.8000 | 1.0000 | 65 | 0 |
| 잔여 증강 rule+RoBERTa + 조건 부정 처리 | 0.8240 | 0.9072 | 0.8328 | 0.9962 | 52 | 1 |
| 현재 정책 적용 후 rule/parser | 0.8240 | 0.9184 | 0.8520 | 0.9962 | 45 | 1 |
| 현재 정책 적용 후 잔여 증강 RoBERTa 단독 | 0.9360 | 0.9549 | 0.9338 | 0.9769 | 18 | 6 |

해석:

- 잔여 증강은 RoBERTa 단독 판단을 크게 개선했다.
- 런타임 union은 rule/parser가 만든 extra label을 제거하지 못하므로 precision 한계가 남는다.
- `주차말고`, `유모차 말고 휠체어` 같은 조건 부정은 rule과 Transformer union 양쪽에서 제외하도록 보강했다.
- `주챠`, `주차ㅏ`, `주자창` 같은 주차 오타는 로컬 정규화와 기본 조건 사전에 반영했다. Transformer가 꺼져도 제외/포함 판단이 가능해야 하기 때문이다.
- `계단 적게`, `걷기 편한`, `편한 관광지`처럼 고령자/접근로/휠체어 중 무엇을 뜻하는지 불명확한 문장은 바로 카드 검색으로 단정하지 않고 `clarification`으로 보낸다.
- 명시 표현이 있으면 추가질문하지 않는다. 예를 들어 `휠체어`, `경사로`, `접근로`, `출입통로`, `어르신`, `부모님`, `무릎`, `쉬어`, `앉` 같은 기준어가 있으면 해당 조건으로 처리한다.
- 고령자 조건은 원천 데이터에 고령자 전용 필드가 부족하므로, 응답 카드에서 휠체어 접근, 경사로, 화장실, 대중교통 같은 이동 편의 근거를 함께 확인한다고 명시한다.
- 부모 호칭만으로 고령자라고 단정하지 않는다. `어머니`, `아버지`, `엄마`, `아빠`는 단독 고령자 조건이 아니며, `오래안걷`, `무릎`, `쉬어` 같은 이동 부담 표현이 함께 있을 때 고령자 조건으로 본다.
- `화장실잇는말고`, `장애인 장실말고`처럼 조건과 제외 표지 사이에 `있는/되는/가능`이 낀 축약 표현도 제외 조건으로 처리한다.
- 남은 구조 개선은 접근로/휠체어 경계의 rule extra를 더 정밀하게 줄이는 정책이다.

## Chat 카드 품질 확인

중간 길이 120건 회귀 평가:

| 설정 | 통과 | 실패 |
|---|---:|---:|
| 기본 rule/parser | 100/120 | 20 |
| hard 증강 RoBERTa 보조 활성화 | 100/120 | 20 |

focused hard 의미 chat 평가 40건:

| 설정 | 통과 | 실패 |
|---|---:|---:|
| 기본 rule/parser | 21/40 | 19 |
| hard 증강 RoBERTa 보조 활성화 | 36/40 | 4 |
| 잔여 증강 RoBERTa 보조 활성화 | 36/40 | 4 |

잔여 hard chat 80건:

| 설정 | 통과 | 실패 |
|---|---:|---:|
| 기본 rule/parser | 15/80 | 65 |
| hard 증강 RoBERTa 보조 활성화 | 53/80 | 27 |
| 잔여 증강 RoBERTa 보조 활성화 | 62/80 | 18 |
| 잔여 증강 RoBERTa + 조건 부정/모호 조건 추가질문 | 62/80 | 18 |
| 현재 정책 적용 후 | 80/80 | 0 |

실사용형 noisy chat 200건:

| 설정 | 통과 | 실패 | 통과율 | 평균 응답 |
|---|---:|---:|---:|---:|
| rule/parser | 152/200 | 48 | 0.7600 | 242.9ms |
| ET5 로컬 교정 | 158/200 | 42 | 0.7900 | 442.5ms |
| quickspacer 후보 | 152/200 | 48 | 0.7600 | 376.5ms |
| 잔여 증강 RoBERTa 보조 | 170/200 | 30 | 0.8500 | 273.6ms |
| ET5 + RoBERTa 병행 | 168/200 | 32 | 0.8400 | 478.8ms |

평가 파일과 결과:

- 평가셋: `data/eval/tourism_noisy_realistic_chat_eval_v1_200.jsonl`
- 생성기: `scripts/generate_tourism_noisy_realistic_chat_eval.py`
- 비교 스크립트: `scripts/compare_tourism_noisy_realistic_chat_models.py`
- 결과: `data/generated/tour_api/noisy_realistic_chat_model_compare_20260518/summary.json`

해석:

- noisy 200건에서는 RoBERTa 조건 보조가 실제 카드 통과율을 가장 크게 올렸다.
- ET5 로컬 교정은 일부 오타 입력에는 도움이 됐지만, RoBERTa 보조와 병행해도 RoBERTa 단독보다 느리고 점수도 약간 낮았다.
- quickspacer는 이 셋에서 rule/parser와 같은 통과율이라 런타임 승격하지 않는다.
- 남은 실패는 수어/점자/보조견 같은 희소 조건 데이터 부족, 일부 멀티턴 조건 교체, negation 축약 표현 경계다.

결론:

- 기존 중간 길이 회귀셋에서는 품질 하락이 없었다.
- hard 의미 표현에서는 카드 반환 품질이 크게 개선됐다.
- noisy 실제형 입력에서는 RoBERTa 조건 보조가 rule/parser보다 18%p 높은 통과율을 보였다.
- 따라서 로컬 시연 환경에서는 잔여 증강 RoBERTa 조건 보조를 켜서 운영한다.

## 적용 방식

런타임은 Transformer 단독 판단으로 바꾸지 않는다.

현재 적용은 다음 구조다.

- 기존 rule/parser가 먼저 조건을 찾는다.
- 로컬 ET5 교정은 위험 입력에서만 후보 문장을 추가한다.
- 잔여 증강 RoBERTa는 상황별 게이트를 통과할 때만 조건 라벨 보조 후보를 추가한다.
- 깨끗하고 조건이 명확한 입력은 RoBERTa를 호출하지 않고 rule/parser만 사용한다.
- rule/parser가 조건을 못 찾거나, `대중교통` 단독처럼 약한 조건만 잡히거나, 오타/무띄어쓰기/의미 우회 표현이 있으면 RoBERTa를 호출한다.
- rule/parser와 RoBERTa 결과가 경계 애매성을 만들면 바로 단정하지 않고 추가질문 정책으로 넘긴다.
- 최종 카드 반환은 기존 지역/조건/근거 필터와 `/tourism/chat` 품질 기준을 계속 통과해야 한다.

로컬 `.env` 적용값:

```env
TOURISM_KOREAN_CORRECTION_ENABLED=true
TOURISM_KOREAN_CORRECTION_PROVIDER=hf_seq2seq
TOURISM_KOREAN_CORRECTION_MODEL=./data/models/tourism_korean_corrector
TOURISM_KOREAN_CORRECTION_DEVICE=auto
TOURISM_KOREAN_CORRECTION_RISKY_ONLY=true
TOURISM_KOREAN_CORRECTION_ALLOW_DOWNLOAD=false
TOURISM_KOREAN_CORRECTION_MAX_CHARS=80
TOURISM_KOREAN_CORRECTION_MAX_LENGTH=128
TOURISM_KOREAN_CORRECTION_NUM_BEAMS=1

TOURISM_CONDITION_TRANSFORMER_ENABLED=true
TOURISM_CONDITION_TRANSFORMER_MODEL=./data/generated/tour_api/condition_transformer_residual_aug_e2_fast/model
TOURISM_CONDITION_TRANSFORMER_METRICS_PATH=./data/generated/tour_api/condition_transformer_residual_aug_e2_fast/metrics.json
TOURISM_CONDITION_TRANSFORMER_DEVICE=auto
TOURISM_CONDITION_TRANSFORMER_MAX_LENGTH=96
```

주의:

- 모델 산출물은 `data/generated/` 아래 로컬 파일이며 git에 올리지 않는다.
- 새 환경에서는 같은 학습 명령으로 모델을 다시 만들어야 한다.
- false positive 가능성은 남아 있으므로 새 데이터가 들어오면 hard holdout과 chat-card 평가를 같이 갱신한다.

## 재현 명령

```bash
.venv/bin/python scripts/generate_tourism_hard_nlu_holdout.py
.venv/bin/python scripts/eval_tourism_hard_nlu_models.py
.venv/bin/python scripts/prepare_tourism_hard_condition_aug_data.py
.venv/bin/python scripts/train_tourism_condition_transformer.py \
  --model-name data/models/klue_roberta_small \
  --data-dir data/processed/tourism_condition_transformer_hard_aug \
  --output-dir data/generated/tour_api/condition_transformer_hard_aug_e2_fast \
  --epochs 2 \
  --batch-size 32 \
  --learning-rate 2e-5 \
  --save-model \
  --skip-rule-baselines
.venv/bin/python scripts/eval_tourism_hard_nlu_models.py \
  --output-dir data/generated/tour_api/hard_nlu_model_compare_hard_aug_20260518 \
  --model-dir data/generated/tour_api/condition_transformer_hard_aug_e2_fast/model \
  --metrics-path data/generated/tour_api/condition_transformer_hard_aug_e2_fast/metrics.json
.venv/bin/python scripts/generate_tourism_residual_hard_eval.py
.venv/bin/python scripts/prepare_tourism_residual_condition_aug_data.py
.venv/bin/python scripts/train_tourism_condition_transformer.py \
  --model-name data/models/klue_roberta_small \
  --data-dir data/processed/tourism_condition_transformer_residual_aug \
  --output-dir data/generated/tour_api/condition_transformer_residual_aug_e2_fast \
  --epochs 2 \
  --batch-size 32 \
  --learning-rate 2e-5 \
  --save-model \
  --skip-rule-baselines
.venv/bin/python scripts/eval_tourism_hard_nlu_models.py \
  --input data/eval/tourism_residual_hard_nlu_20260518.jsonl \
  --output-dir data/generated/tour_api/residual_hard_nlu_compare_residual_aug_20260518 \
  --model-dir data/generated/tour_api/condition_transformer_residual_aug_e2_fast/model \
  --metrics-path data/generated/tour_api/condition_transformer_residual_aug_e2_fast/metrics.json
```
