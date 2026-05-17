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

결론:

- 기존 중간 길이 회귀셋에서는 품질 하락이 없었다.
- hard 의미 표현에서는 카드 반환 품질이 크게 개선됐다.
- 따라서 로컬 시연 환경에서는 hard 증강 RoBERTa 조건 보조를 켜서 운영한다.

## 적용 방식

런타임은 Transformer 단독 판단으로 바꾸지 않는다.

현재 적용은 다음 구조다.

- 기존 rule/parser가 먼저 조건을 찾는다.
- 로컬 ET5 교정은 위험 입력에서만 후보 문장을 추가한다.
- hard 증강 RoBERTa는 조건 라벨 보조 후보를 추가한다.
- 최종 카드 반환은 기존 지역/조건/근거 필터와 `/tourism/chat` 품질 기준을 계속 통과해야 한다.

로컬 `.env` 적용값:

```bash
TOURISM_CONDITION_TRANSFORMER_ENABLED=true
TOURISM_CONDITION_TRANSFORMER_MODEL=./data/generated/tour_api/condition_transformer_hard_aug_e2_fast/model
TOURISM_CONDITION_TRANSFORMER_METRICS_PATH=./data/generated/tour_api/condition_transformer_hard_aug_e2_fast/metrics.json
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
```
