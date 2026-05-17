# 문맥 해석 LLM hard-style 학습셋 생성 절차

마지막 갱신: 2026-05-17

## 목적

현재 KoBERT/KLUE-RoBERTa 파일럿은 validation 1.0000, hard holdout micro-F1 0.8499로 과적합/검증셋 설계 실패 신호가 뚜렷하다. 원인은 모델 epoch 부족만이 아니라 train/validation 문장이 너무 쉬운 생성 템플릿에 가까운 점이다.

이 문서는 Codex 같은 LLM에게 hard-style 학습 문장을 만들게 하되, 시장 일반 ML/DL 평가 원칙에 맞게 누수와 과적합을 막는 절차를 정의한다.

## 원칙

1. LLM 생성 문장을 바로 학습에 넣지 않는다.
2. JSONL schema 검증, 라벨 검증, 중복 검증, 기존 train/holdout overlap 검증을 통과해야 한다.
3. 기존 hard holdout 문장을 그대로 train에 넣지 않는다.
4. validation 1.0000을 목표로 하지 않는다. 오히려 hard-style validation에서 적당히 어려워야 한다.
5. LLM은 “비슷한 문장 많이 만들기”가 아니라 실패할 만한 문맥 반례를 만들어야 한다.

## 파일

| 파일 | 역할 |
|---|---|
| `scripts/build_tourism_context_llm_generation_prompt.py` | Codex/LLM에 줄 hard-style 생성 프롬프트 생성 |
| `scripts/validate_tourism_context_llm_dataset.py` | LLM JSONL schema, 라벨, 중복, overlap 검수 |
| `scripts/prepare_tourism_context_finetune_data.py` | 검수된 extra train JSONL을 fine-tuning split에 병합 |
| `docs/tourism/ml_evaluation_governance.md` | ML 평가 운영 기준 |

생성 prompt와 실험 결과는 `data/generated/tour_api/` 아래에 쓰며 git ignore 대상이다.

## 1. LLM 생성 프롬프트 만들기

```bash
.venv/bin/python scripts/build_tourism_context_llm_generation_prompt.py --target-rows 300 --batch-id 001
```

출력 예:

```text
data/generated/tour_api/context_llm_prompts/context_llm_generation_prompt_001.md
```

이 프롬프트를 Codex에 주고 JSONL만 출력하게 한다. 출력은 예를 들어 다음 파일에 둔다.

```text
data/generated/tour_api/context_llm_batches/context_llm_batch_001.raw.jsonl
```

## 2. LLM 결과 검수

```bash
.venv/bin/python scripts/validate_tourism_context_llm_dataset.py \
  --input data/generated/tour_api/context_llm_batches/context_llm_batch_001.raw.jsonl \
  --output data/processed/tourism_context_llm_hard_training.valid.jsonl \
  --min-rows 250 \
  --fail-on-reject
```

검수 항목:

- 필수 field 존재
- 허용 라벨만 사용
- `strict_and`와 `or_condition` 동시 사용 금지
- `soft_and`와 action/strict/or 라벨 동시 사용 금지
- 입력 내 중복 제거
- 기존 train/hard holdout 문장 overlap 차단

`--fail-on-reject`는 하나라도 거절된 row가 있으면 exit code 2로 종료한다. 대량 생성 초기에는 이 옵션을 빼고 거절 샘플을 먼저 보는 것이 좋다.

## 3. fine-tuning split에 병합

검수된 파일만 extra train으로 넣는다.

```bash
.venv/bin/python scripts/prepare_tourism_context_finetune_data.py \
  --extra-train-input data/processed/tourism_context_llm_hard_training.valid.jsonl
```

이 스크립트는 train/test text overlap을 다시 확인한다. overlap이 있으면 실패한다.

## 4. 학습과 감사

```bash
.venv/bin/python scripts/train_tourism_context_transformer.py --epochs 3 --batch-size 16 --model-name klue/roberta-small
.venv/bin/python scripts/audit_tourism_ml_experiment.py
```

감사 결과가 `do_not_adopt_runtime`이면 런타임 채택을 하지 않는다.

## 좋은 LLM 생성 예시

```json
{"id":"LLMCTX000001","text":"수유실 있으면 좋긴 한데 그거 없다고 빼지는 말고 유모차로 이동 쉬운 데 위주로 봐줘","labels":["soft_and","mobility_context"],"category":"soft_family_mobility","required_terms":[],"optional_terms":["수유실","유모차"],"excluded_terms":[],"risk_tags":["soft-vs-required","family-vs-mobility"],"rationale":"수유실은 선택 조건이고 유모차 이동성이 핵심"}
```

```json
{"id":"LLMCTX000002","text":"주차 말고 주제가 독특한 전시를 찾는 거야","labels":[],"category":"facility_word_as_topic","required_terms":[],"optional_terms":[],"excluded_terms":[],"risk_tags":["facility-word-not-facility"],"rationale":"주차는 시설 조건이 아니라 제외된 화제"}
```

```json
{"id":"LLMCTX000003","text":"아까 점자블록은 내려놓고 이번엔 자막 안내가 실제로 적힌 곳만","labels":["replace_condition","specific_facility_required"],"category":"replace_to_specific_facility","required_terms":["자막 안내"],"optional_terms":[],"excluded_terms":["점자블록"],"risk_tags":["active-replacement-span"],"rationale":"점자블록은 과거 조건이고 자막 안내가 새 필수 시설"}
```

## 나쁜 생성 예시

```json
{"text":"서울에서 휠체어 관광지 추천","labels":["mobility_context"]}
```

문제:

- id/category/terms/rationale가 없다.
- 너무 쉬운 문장이라 hard-style 학습셋 목적에 맞지 않는다.

```json
{"id":"LLMCTX000004","text":"수어 안내 또는 자막 안내 둘 다 되는 곳","labels":["or_condition","strict_and","specific_facility_required"],"category":"bad_conflict","required_terms":["수어 안내","자막 안내"],"optional_terms":[],"excluded_terms":[],"risk_tags":[],"rationale":"둘 다와 또는이 섞임"}
```

문제:

- `or_condition`과 `strict_and`가 충돌한다.
- 문장 자체도 라벨이 모호하다. 이런 row는 학습에 넣지 않는다.

## 다음 보강 방향

1. `soft_and`와 `specific_facility_required` 경계를 많이 생성한다.
2. `replace_condition`에서 old/new span을 명확히 분리한 문장을 늘린다.
3. `유모차`를 family/mobility/시설 대여 맥락으로 나누는 문장을 늘린다.
4. 아무 라벨도 없어야 하는 negative near-miss를 최소 10% 유지한다.
5. hard-style validation을 별도 파일로 분리하는 다음 단계가 필요하다.
