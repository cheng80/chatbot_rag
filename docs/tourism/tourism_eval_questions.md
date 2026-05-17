# 관광 챗봇 평가셋

마지막 갱신: 2026-05-17

이 문서는 `/tourism/chat`의 품질을 반복 확인하기 위한 평가셋이다.

- `data/eval/tourism_20_questions.jsonl`: 빠른 smoke test용 최소 평가셋
- `data/eval/tourism_80_questions.jsonl`: 복합 의도, 모호 지역, 경계 요청, 저커버리지 지역을 포함한 확장 평가셋
- `data/eval/tourism_100_questions.jsonl`: 행정구역 예외, 동명이 지역, 조건 동의어, 더보기/최신 정보 보강 정책까지 포함한 자동 채점 평가셋
- `data/eval/tourism_challenge_questions.jsonl`: 이미 통과한 회귀 문항이 아니라 선호/부정 조건, 감각 접근성, 애매 지역, 저커버리지 지역을 더 까다롭게 검증하는 챌린지 평가셋
- `data/eval/tourism_conversation_challenge.jsonl`: 단발 Q&A가 아니라 이어지는 질문에서 이전 지역/조건을 유지하거나 교체하는지 검증하는 멀티턴 챌린지 평가셋
- `data/eval/tourism_expanded_questions.jsonl`: 신규 문제 탐색용 단발 확장 평가셋 274문항
- `data/eval/tourism_expanded_conversation_challenge.jsonl`: 신규 문제 탐색용 멀티턴 확장 평가셋 97시나리오
- `data/eval/tourism_intent_seed_utterances.jsonl`: 대화 후속 질문과 의도 분류 보강용 seed 발화
- `data/eval/tourism_intent_generated_utterances.jsonl`: label별 최소 300건 이상 확보를 위한 재현 가능한 생성 발화
- `data/eval/tourism_intent_adversarial_holdout.jsonl`: 학습에 넣지 않는 intent adversarial holdout 2,420건
- `data/eval/tourism_intent_gemini_holdout_verified.jsonl`: Gemini 생성 후 2차 라벨 검수를 통과한 AI-generated independent holdout 676건
- `data/eval/tourism_intent_hard_holdout.jsonl`: show_more/live_topup/unsupported_request/애매 지역 경계 케이스 중심 deterministic hard holdout 990건
- `data/eval/tourism_intent_region_clarify_stress.jsonl`: Gemini holdout의 `clarify_region` 35건 한계를 보완하기 위한 애매 지명 stress holdout 960건
- `data/eval/tourism_intent_region_clarify_natural_holdout.jsonl`: 1.000 착시를 줄이기 위한 자연형 애매 지명 holdout 600건
- `data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl`: 문맥 해석의 `specific_facility_required` 1.0000 착시를 깨기 위한 시설 조건 adversarial holdout 980건
- `data/eval/tourism_context_blind_holdout.jsonl`: 기존 generator를 재사용하지 않은 LLM blind 문맥 해석 holdout 80건
- `data/eval/tourism_context_rotating_blind_holdout_20260517.jsonl`: 고정 blind 보강 뒤 새로 만든 rotating blind holdout 80건
- `data/eval/tourism_context_rotating_blind_holdout_20260517_v2.jsonl`: 첫 rotating blind 보강 뒤 다시 만든 v2 rotating blind holdout 80건
- `data/eval/tourism_context_rotating_blind_holdout_20260517_v3.jsonl`: v2 보강 뒤 다시 만든 v3 rotating blind holdout 80건
- `data/eval/tourism_context_rotating_blind_holdout_20260517_v4.jsonl`: v3 보강 뒤 다시 만든 v4 rotating blind holdout 80건
- `data/eval/tourism_context_blind_chat_eval.jsonl`: 문맥 해석 약점이 실제 `/tourism/chat` 카드/답변에 미치는지 보는 blind chat eval 10건
- `data/eval/tourism_context_blind_chat_eval_v2.jsonl`: strict/OR/제외/지역교체/저커버리지 케이스를 포함한 실제 `/tourism/chat` 카드 적합성 blind eval 15건
- `data/processed/tourism_intent_training.jsonl`: 기존 100/30/50 평가셋, seed/generated 발화, AI Hub 추출 발화를 합쳐 만든 의도 분류 학습셋

## 평가 목적

- 지역 해석, 동명이 시군구 선택 질문, 근처 확장 정책이 의도대로 동작하는지 확인한다.
- 휠체어, 유모차, 보조견, 장애인 화장실, 장애인 주차 같은 조건이 카드 근거와 연결되는지 본다.
- 관계 호칭만으로 나이를 추정하지 않는지 확인한다.
- 근거가 부족한 지역이나 잘못된 전제에서 임의로 카드를 지어내지 않는지 본다.
- `lookup_mode`, `warnings`, `suggested_messages` 같은 진단 필드가 QA에 충분한지 확인한다.
- 복합 상황 질문을 추론 보조 OFF 기본 모드에서 처리했을 때 지역 해석, 조건 반영, 경계 안내가 무너지지 않는지 확인한다.
- 기존 회귀 방어보다 새로 문제가 될 만한 질문을 먼저 찾고, 발견한 실패를 보강한 뒤 전체 회귀를 통과시키는 순서로 운용한다.

## 검증 품질 기준

평가 결과를 볼 때는 단순 통과율이나 accuracy만 보지 않는다. 특히 precision/recall/F1 또는 특정 label accuracy가 `1.0000`이면 우선 성능 개선이 아니라 검증셋 약화 가능성으로 의심한다.

항상 확인할 기준:

1. 같은 문항 반복으로 오른 점수인지 확인한다.
2. train/validation/test가 같은 template family, 생성 batch, 문장 패턴을 공유하지 않는지 확인한다.
3. locked test와 별도 independent validation을 함께 본다.
4. focused/contract/stress 셋의 `1.0000`은 품질 점수에서 제외하고, 깨지면 안 되는 최소 경계 방어선으로만 본다.
5. `1.0000`이 나온 label은 그 label을 직접 흔드는 adversarial holdout을 새로 만든다.
6. 새 holdout은 긍정 예시뿐 아니라 부정 예시, 선택 조건, 조건 교체, 조건 제외, 문맥 없는 후속 질문을 함께 넣는다.
7. per-label precision/recall/F1, exact match, micro-F1, special errors를 같이 본다.
8. sample mismatches를 읽고 코드 오류와 라벨 정의 오류를 분리한다.
9. 사람이 보기에 라벨이 틀린 row는 모델 점수보다 평가셋 라벨을 먼저 고친다.
10. 보강 뒤에는 새 adversarial set만 보지 않고 전체 locked test와 independent validation을 다시 돌린다.
11. latency가 늘어난 모델은 점수가 같으면 채택하지 않는다.
12. `/tourism/chat` 실제 응답 평가에서는 intent/context label 점수와 별개로 카드 근거, 지역 유지, 더보기, 경고 문구가 함께 맞는지 본다.
13. 고정 blind holdout을 오류 분석이나 학습 데이터 생성에 사용한 뒤에는 같은 파일 점수를 최종 품질 점수로 쓰지 않고, 새 rotating blind를 만들어 다시 본다.

새 문항을 추가해야 하는 신호:

- 어떤 부분 셋이 연속으로 `1.0000`을 보인다.
- sample mismatch가 문장 패턴 몇 개에 몰린다.
- 모델이 특정 단어 하나만 보고 label을 붙인다.
- “A 말고 B”, “A는 참고만”, “A 또는 B”, “A와 B 둘 다”, “A라는 단어가 있어도 요청은 아님” 같은 경계 표현이 부족하다.
- 실사용 질문에서는 틀릴 것 같은데 현재 eval에는 반례가 없다.

이 기준은 `docs/tourism/ml_evaluation_governance.md`와 함께 적용한다. 이 문서는 실행 대상 목록을 관리하고, `ml_evaluation_governance.md`는 ML/DL 실험 채택 기준을 관리한다.

## 2026-05-17 문맥 해석 blind 평가 결과

현재 작성된 independent validation이나 focused adversarial set에서 1.0000 또는 그에 가까운 점수가 반복되므로, 문맥 해석 평가는 고정 회귀셋과 fresh blind를 분리해서 본다.

| 평가셋 | rows | 최신 결과 | 해석 |
|---|---:|---|---|
| `tourism_context_independent_validation.jsonl` | 1,200 | 과거 exact/micro-F1 1.0000 | 당시 경계 회귀셋 통과. 품질 점수 아님 |
| `tourism_context_independent_validation.jsonl` | 1,200 | 최신 exact 0.9242 / micro-F1 0.9741 | v2 경계 보강 뒤 현실화된 독립 validation |
| locked context test | 4,800 | 최신 exact 0.9548 / micro-F1 0.9803 | 넓은 회귀 기준선 |
| `tourism_context_specific_facility_adversarial_holdout.jsonl` | 980 | 최신 exact 0.9918 / micro-F1 0.9946 | 시설 조건 focused 방어선 |
| `tourism_context_blind_holdout.jsonl` | 80 | 보강 후 exact 0.6250 / micro-F1 0.8340 | fixed diagnostic. 보강에 사용했으므로 최종 점수 아님 |
| `tourism_context_rotating_blind_holdout_20260517.jsonl` | 80 | 최초 exact 0.5750 / micro-F1 0.8163 | fresh blind 기준. 약점 확인 |
| `tourism_context_rotating_blind_holdout_20260517.jsonl` | 80 | 보강 후 exact 0.9750 / micro-F1 0.9919 | 같은 파일 대응 결과. 최종 품질 점수 아님 |
| `tourism_context_rotating_blind_holdout_20260517_v2.jsonl` | 80 | 최초 exact 0.6000 / micro-F1 0.8245 | v1 보강 뒤 새 blind에서 다시 약점 확인 |
| `tourism_context_rotating_blind_holdout_20260517_v2.jsonl` | 80 | 보강 후 exact 0.9250 / micro-F1 0.9719 | 같은 v2 파일 대응 결과. 최종 품질 점수 아님 |
| `tourism_context_rotating_blind_holdout_20260517_v3.jsonl` | 80 | 최초 exact 0.6625 / micro-F1 0.8560 | v2 보강 뒤 새 blind에서 `보조 조건`, `유모차 대여`, 시설명 near-miss 약점 확인 |
| `tourism_context_rotating_blind_holdout_20260517_v3.jsonl` | 80 | 보강 후 hybrid LinearSVC exact 0.9875 / micro-F1 0.9960, rule-only 1.0000 | 같은 v3 파일 대응 결과. 최종 품질 점수 아님 |
| `tourism_context_rotating_blind_holdout_20260517_v4.jsonl` | 80 | fresh v4 rule-only exact 0.7375 / micro-F1 0.9091, hybrid LinearSVC exact 0.7250 / micro-F1 0.9012, hybrid LogisticRegression exact 0.7125 / micro-F1 0.8968 | v3 보강 뒤 새 blind. 하이브리드 로지스틱 회귀는 계속 비교하지만 v4 최고는 아니며, 런타임 모델 교체 근거로 보지 않음 |
| `tourism_context_blind_chat_eval.jsonl` | 10 | 10/10 통과 | 실제 카드 반환 기준 blind smoke |
| `tourism_context_blind_chat_eval_v2.jsonl` | 15 | 15/15 통과 | 실제 `/tourism/chat` 카드 적합성 확장 smoke. context label failure와 실제 카드 품질을 분리해 보기 위한 셋 |

blind chat eval에서 최초 실패한 `전주 시장 제외+조용한 곳` 케이스는 시장 제외 표현이 세부 근거 필수 조건처럼 남고, `조용한` 선호가 hard filter로 작동한 문제였다. 시장 제외 파싱, `취소` 표현, preference ranking을 보정한 뒤 통과했다.

다음 문맥 해석 개선은 v4 failure bucket을 바로 룰 보강으로 흡수하기보다 실제 카드 적합성에 영향을 주는지 먼저 본다. 이번 보강으로 v1/v2/v3 rotating file의 오류는 줄었지만, 세 파일 모두 오류 분석과 룰 보강에 쓰였으므로 일반화 성능으로 주장하지 않는다. v4는 fresh blind이고, chat v2 15/15는 실제 응답 품질이 아직 깨지지 않았다는 별도 신호다. v3 작성 과정에서 `촉지도나 점자`는 OR, `카페 말고`, `공연장은 빼고`는 exclude로 라벨을 고쳤다. 사람이 보기에 라벨이 틀린 row는 모델 점수보다 평가셋 라벨을 먼저 고친다는 원칙을 적용한 사례다.

v4 rotating blind 생성과 평가는 아래처럼 실행했다.

```bash
.venv/bin/python scripts/generate_tourism_context_rotating_blind_holdout.py --variant v4
.venv/bin/python scripts/eval_tourism_context_classifier.py \
  --input data/eval/tourism_context_rotating_blind_holdout_20260517_v4.jsonl \
  --output data/generated/tour_api/context_classifier_eval_rotating_v4_20260517.json
```

chat blind v2 생성과 평가는 아래처럼 실행했다.

```bash
.venv/bin/python scripts/generate_tourism_context_blind_chat_eval.py --variant v2
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct \
  --input data/eval/tourism_context_blind_chat_eval_v2.jsonl \
  --output data/generated/tour_api/eval_runs/tourism_context_blind_chat_eval_v2_latest.jsonl
```

## 실행 방법

서버는 사용자가 볼 수 있는 에디터 터미널에서 직접 띄운다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

다른 터미널에서 평가 스크립트를 실행한다.

```bash
.venv/bin/python scripts/eval_tourism_chat.py
```

서버를 띄우지 않고 현재 코드 상태를 빠르게 확인할 때는 in-process 실행을 쓴다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct
```

확장 100문항 평가셋은 아래처럼 실행한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_100_questions.jsonl
```

챌린지 평가셋은 기존 정답지 반복 학습을 피하기 위해 별도로 실행한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_challenge_questions.jsonl
```

대화 흐름 챌린지는 같은 `session_id`로 여러 turn을 순차 호출해 확인한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_conversation_challenge.jsonl
```

신규 문제 탐색용 확장셋은 아래처럼 실행한다.

```bash
.venv/bin/python scripts/generate_tourism_chat_expanded_eval.py
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_expanded_questions.jsonl
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_expanded_conversation_challenge.jsonl
```

의도 분류 학습셋과 모델은 아래 순서로 재생성한다.

```bash
.venv/bin/python scripts/generate_tourism_intent_utterances.py
.venv/bin/python scripts/extract_aihub_tourism_intent_utterances.py
.venv/bin/python scripts/build_tourism_intent_training_set.py
.venv/bin/python scripts/train_tourism_intent_classifier.py
```

현재 모델은 `data/processed/tourism_intent_classifier.json`에 저장된다. 런타임에서는 규칙 기반 파싱을 대체하지 않고, `show_more`, `live_topup`, `ask_source`, `add_condition`, `replace_condition`, `exclude_preference`, `narrow_region`, `change_region`, `unsupported_request` 같은 후속 의도를 session context 사용 판단에 보조 신호로만 쓴다.

평가 스크립트는 시작 시 `TOUR_API_USAGE_LOG_PATH`의 오늘 엔드포인트별 사용량을 읽고 출력한다. live 조회까지 포함해 확인할 때는 `--strict-budget`을 붙여 보수적 최악 추정치가 오늘 한도 안에 들어오는지 먼저 확인한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=true .venv/bin/python scripts/eval_tourism_chat.py --direct --strict-budget --input data/eval/tourism_100_questions.jsonl
```

당일 로그 도입 전에 이미 생성된 TourAPI 산출물이 있으면 아래 명령으로 오늘 수정된 raw/live 산출물 기준 최소 사용량을 usage log에 반영한다.

```bash
.venv/bin/python scripts/bootstrap_tour_api_usage.py
```

공공데이터포털 호출량을 아껴야 하는 날에는 fallback-only로 실행한다.

결과는 기본적으로 `data/generated/tour_api/eval_runs/` 아래 JSONL로 저장된다. 이 디렉터리는 생성 산출물이므로 커밋하지 않는다.

## 2026-05-16 확장 평가 규모와 최종 실행 결과

기존 자동 평가 규모는 100문항 + 30문항 + 50시나리오 = 180건이었다. 신규 문제 탐색용으로 단발 274문항과 대화 97시나리오를 추가해 총 551건으로 늘렸다.

최종 실행 결과:

| 평가셋 | 건수 | fallback-only 실패 | live-enabled 실패 |
|---|---:|---:|---:|
| `tourism_100_questions.jsonl` | 100 | 0 | 0 |
| `tourism_challenge_questions.jsonl` | 30 | 0 | 0 |
| `tourism_conversation_challenge.jsonl` | 50 | 0 | 0 |
| `tourism_expanded_questions.jsonl` | 274 | 0 | 0 |
| `tourism_expanded_conversation_challenge.jsonl` | 97 | 0 | 0 |
| 합계 | 551 | 0 | 0 |

이번 확장 평가에서 확인하고 고친 품질 문제:

- `응급실은 말고 관광지만 계속`처럼 미지원 주제를 부정한 후속 질문은 의료 요청으로 거절하지 않고 관광 추천을 계속한다.
- `지하철역 바로 연결된 곳만`처럼 현재 카드 근거로 확인하기 어려운 핵심 조건은 일반 거절이 아니라 조건 제거 여부를 묻는 확인 질문으로 보낸다.
- 저장된 카드가 요청 선호를 덮지 못하면 cache/index 결과에서 멈추지 않고 sample 후보까지 확인한다.
- 남제주군처럼 통합된 과거 지명은 현재 행정구역 안내를 유지하면서 서귀포시 기준 카드를 찾는다.

TourAPI 사용량:

- 서귀포시 부족 카드 보강 전: `areaBasedList2=77`, `detailCommon2=190`, `detailWithTour2=190`
- 서귀포시 100건 보강 후: `areaBasedList2=80`, `detailCommon2=287`, `detailWithTour2=287`
- live-enabled 551건 전체 실행 후: `areaBasedList2=93`, `detailCommon2=287`, `detailWithTour2=287`
- live eval은 `TOURISM_LIVE_MAX_DETAIL_CALLS=1`로 실행했고, 캐시/색인 우선 경로 덕분에 상세 조회 추가 호출은 발생하지 않았다.

## 2026-05-16 100문항 fallback-only 실행 결과

실행 명령:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_100_questions.jsonl
```

호출량 가드:

- 부트스트랩 추정 사용량: `areaBasedList2=73`, `detailCommon2=170`, `detailWithTour2=170`
- fallback-only eval 추정 추가 호출량: 0
- live-enabled 100문항 실행은 실제 호출 전 현재 사용량을 확인하고, 각 TourAPI 요청 직전에 엔드포인트별 한도를 다시 확인했다.
- live-enabled 100문항 실행 후 사용량은 `areaBasedList2=76`, `detailCommon2=185`, `detailWithTour2=185`였다.

요약:

| 항목 | 결과 |
|---|---:|
| 총 문항 | 100 |
| 자동 채점 실패 | 0 |
| HTTP/API 실패 | 0 |
| live-enabled 자동 채점 실패 | 0 |

## 2026-05-16 챌린지 30문항 fallback-only 실행 결과

실행 명령:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_challenge_questions.jsonl
```

호출량 가드:

- 실행 시점 사용량: `areaBasedList2=77`, `detailCommon2=190`, `detailWithTour2=190`
- fallback-only eval 추정 추가 호출량: 0

요약:

| 항목 | 결과 |
|---|---:|
| 총 문항 | 30 |
| 자동 채점 실패 | 0 |
| HTTP/API 실패 | 0 |

확인된 개선:

- 점자블록, 오디오가이드, 보조견, 수어/자막 같은 감각 접근성 조건을 별도 조건으로 인식한다.
- 실내/박물관, 시장/먹거리, 공원/산책, 조용한 곳 같은 선호 조건을 카드 랭킹에 반영한다.
- 식당/카페/숙박/시장처럼 사용자가 빼 달라고 한 부정 조건은 대체 후보가 있으면 제외한다.
- live Markdown 캐시에 지역 카드가 있어도 세부 조건 근거가 부족하면 indexed/sample 후보까지 계속 확인한다.
- `광주`처럼 애매한 입력은 확인 질문으로 보내고, `광주광역시`처럼 명시된 입력은 바로 추천으로 처리한다.
- 복합 조건은 사용자가 `둘 다`, `모두`, `동시에`, `반드시`처럼 명시한 경우만 strict AND로 본다. 그 외에는 전체 충족 후보를 우선하고, 없으면 부분 근거 후보를 반환한다. 다만 점자블록, 보조견, 수어/자막, 장애인 주차/화장실, 기저귀 교환대처럼 직접 말한 세부 시설은 필수 근거로 유지한다.
- 유모차 조건은 직접 가족 편의 근거와 이동 가능성 근거를 분리한다. 직접 가족 편의 근거를 우선하고, 직접 근거가 없을 때만 턱 없음/경사로/출입통로 같은 이동성 근거를 보조로 인정한다.

평가기 보강:

- `must_include_any_card_terms`: 카드 제목, 주소, 태그, raw 편의정보 중 지정 근거가 하나 이상 있는지 확인한다.
- `first_card_must_include_any_terms`: 첫 번째 카드가 선호 조건에 맞는지 확인한다.
- `must_not_include_card_terms`: 제외 조건이 카드에 남아 있는지 확인한다.
- `must_include_answer_any_terms`, `min_suggestions`: 답변 문장과 후속 질문 품질을 함께 본다.

## 2026-05-16 대화 흐름 챌린지 50시나리오 fallback-only 실행 결과

실행 명령:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_conversation_challenge.jsonl
```

호출량 가드:

- 실행 시점 사용량: `areaBasedList2=77`, `detailCommon2=190`, `detailWithTour2=190`
- fallback-only eval 추정 추가 호출량: 0

요약:

| 항목 | 결과 |
|---|---:|
| 총 시나리오 | 50 |
| 자동 채점 실패 | 0 |
| HTTP/API 실패 | 0 |

확인된 개선:

- 같은 `session_id` 안에서 마지막 성공 응답의 지역, 조건, 선호/제외 조건을 얇게 기억한다.
- `더 보기`, `최신 정보 더 찾기`, `그중 시장 말고`, `숙박이나 호텔은 빼고` 같은 후속 질문은 이전 지역과 조건을 유지한다.
- `유모차 말고 휠체어`처럼 명시적으로 부정한 조건은 이전 조건에서 제거하고 새 조건으로 바꾼다.
- `부산 중구 말고 서울 중구`처럼 새 지역을 명시하면 이전 지역을 덮어쓴다.
- `서울` 대화 뒤 `중구로 좁혀줘`처럼 상위 지역 맥락이 있으면 전국 중복 지명을 해당 광역시 안에서 해석한다.
- `서울 강남구` 뒤 `바닷가나 해수욕장`처럼 잘못된 장소 특성을 후속으로 말해도 후보를 억지로 채우지 않는다.
- 50개 확장 중 최초 9건 실패를 확인했고, 후속 표현 인식과 `A 말고 B` 지역 전환을 보강한 뒤 실패 0건으로 정리했다.

평가기 보강:

- JSONL item에 `turns` 배열을 넣으면 같은 `session_id`로 순차 호출한다.
- 각 turn에 기존 단발 채점 필드(`min_cards`, `must_include_any_card_terms`, `must_not_include_card_terms`, `expect_no_cards` 등)를 그대로 적용한다.

## 2026-05-16 의도 분류 학습셋/모델 결과

학습 데이터:

| 항목 | 값 |
|---|---:|
| seed 발화 | 163 |
| 생성 발화 | 13,200 |
| AI Hub 학습 발화 | 2,700 |
| AI Hub 독립 holdout | 497 |
| 최종 학습 rows | 16,254 |
| intent label | 11 |

주요 label:

- `recommend_places`
- `show_more`
- `live_topup`
- `ask_source`
- `add_condition`
- `replace_condition`
- `exclude_preference`
- `change_region`
- `narrow_region`
- `clarify_region`
- `unsupported_request`

훈련 결과:

| 항목 | 값 |
|---|---:|
| train rows | 12,999 |
| test rows | 3,255 |
| 내부 holdout accuracy | 0.9164 |
| AI Hub holdout accuracy | 0.9115 |
| adversarial holdout accuracy | 0.8438 |
| AI Hub + adversarial combined accuracy | 0.8553 |

현재 분류기는 외부 대형 ML 런타임 없이 동작하는 rule override + 문자 n-gram Multinomial Naive Bayes다. 목적은 사용자의 자연스러운 후속 발화를 완전히 해결하는 것이 아니라, 규칙셋이 놓치는 짧은 표현을 감지해 대화 맥락 유지 여부를 더 안정적으로 판단하는 것이다.

ablation 결과:

| 조건 | 학습 rows | 전체 accuracy | AI Hub holdout | adversarial holdout |
|---|---:|---:|---:|---:|
| rule-only | 0 | 0.5605 | 0.3742 | 0.5988 |
| project seed/generated | 13,554 | 0.7854 | 0.4245 | 0.8595 |
| project + AI Hub | 16,254 | 0.8745 | 0.9034 | 0.8686 |
| project + AI Hub + HF external | 25,362 | 0.8632 | 0.8793 | 0.8599 |

AI Hub 발화는 독립 holdout과 전체 accuracy를 크게 올렸으므로 의미가 있었다. 반대로 Hugging Face external 발화는 현재 taxonomy에 맞춰 재라벨링하지 않고 그대로 섞으면 accuracy가 떨어져 기본 학습셋에서 제외한다.

latency 측정 결과:

| 항목 | 값 |
|---|---:|
| classifier load | 19.1482ms |
| classifier predict p50 | 0.0044ms |
| classifier predict p95 | 0.0055ms |
| direct fallback chat p50 | 3.4295ms |
| direct fallback chat p95 | 95.6137ms |
| direct fallback chat max | 1165.8930ms |

의도 분류기는 프로세스당 1회 로드되고 예측 비용이 p95 0.0055ms 수준이라 답변 시간에 실질적인 부담을 주지 않는다. 답변 지연은 검색 초기화, 카드 구성, 지역별 후보 수, live 조회에서 주로 발생한다.

재현 명령:

```bash
.venv/bin/python scripts/benchmark_tourism_intent_ablation.py
.venv/bin/python scripts/benchmark_tourism_latency.py
```

AI Hub 원본 3종은 `data/external/aihub/raw/`에 보관하고 git에는 포함하지 않는다. `scripts/extract_aihub_tourism_intent_utterances.py`는 관광 목적대화/한국어 대화/웰니스 대화에서 현재 intent taxonomy에 맞는 고신뢰 발화만 추출하며, validation split은 `data/eval/tourism_intent_aihub_holdout.jsonl`로 분리한다.

Gemini independent holdout:

| 항목 | 값 |
|---|---:|
| raw 생성 rows | 770 |
| 2차 검수 통과 rows | 676 |
| 개선 전 classifier accuracy | 0.5488 |
| 1차 개선 후 classifier accuracy | 0.7308 |
| 2차 hard holdout 보강 후 classifier accuracy | 0.8536 |

Gemini verified holdout에서 드러난 약점을 바탕으로 일반화 가능한 rule override를 보강했다. 2026-05-16 현재 전체 accuracy는 0.8536이다. 이 평가셋은 기존 템플릿/AI Hub 기준으로는 드러나지 않은 후속 발화 취약점을 찾기 위한 별도 holdout이며, 학습셋에는 넣지 않는다.

Hard intent holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_intent_hard_holdout.jsonl` |
| rows | 990 |
| label별 rows | 90 |
| 2차 보강 전 accuracy | 0.8566 |
| 2차 보강 후 accuracy | 0.9939 |
| change/replace 보강 후 accuracy | 0.9747 |

Hard holdout은 `현재 카드 다음 5곳`, `다른 옵션`, `지금 가지고 있는 것 말고 새로 조회`, `버스 소요시간 확인되는 곳`, `중구 휠체어 관광지`처럼 기존 평가에서 쉽게 통과하던 표현을 일부러 헷갈리게 만든다.

Region clarify holdout:

| 항목 | 값 |
|---|---:|
| rule-boundary stress rows | 960 |
| rule-boundary stress accuracy | 1.0000 |
| rule-boundary stress 품질 점수 포함 | 제외 |
| natural holdout rows | 600 |
| natural holdout 전체 accuracy | 0.9800 |
| natural holdout `clarify_region` rows | 300 |
| natural holdout `clarify_region` accuracy | 1.0000 |

`data/eval/tourism_intent_region_clarify_stress.jsonl`은 `중구`처럼 광역이 없는 중복 지명, `서울 중구`처럼 광역이 붙은 명시 지역, `아까 지역 중 부산 중구 위주로` 같은 지역 축소 표현을 분리해서 확인하는 rule-boundary contract/regression 테스트다. 1.0000을 실사용 일반화 성능으로 해석하지 않고 품질 점수에서 제외한다. 1.0000이 유지되는 동안에는 "충분히 좋은 판단셋"이 아니라 "아직 깨뜨릴 반례가 부족한 경계 테스트"로 본다.

`data/eval/tourism_intent_region_clarify_natural_holdout.jsonl`은 `중구라면 어디 중구 말하는 거야`, `강서구는 서울인지 부산인지`, `중구 중에서도 서울 중구만` 같은 자연형 표현을 섞은 주 추적 지표다. Gemini verified holdout의 `clarify_region` 35건은 유지하되, 표본 부족 판단은 이 natural holdout으로 보완한다.

`clarify_region` 부분 집합 300/300 통과는 보조 정보다. 1.0000이므로 단독 품질 지표로 쓰지 않고, natural holdout 전체 0.9800과 실제 대화 평가를 함께 본다. 부분 셋이 계속 1.0000이면 신규 반례를 더 만들어 판단셋 자체를 강화한다.

Change/replace focused holdout:

| 항목 | 값 |
|---|---:|
| rows | 600 |
| accuracy | 1.0000 |
| 품질 점수 포함 | 제외 |

`data/eval/tourism_intent_change_replace_natural_holdout.jsonl`은 지역 변경, 조건 교체, 단순 제외, 조건 추가 반례를 섞은 focused regression holdout이다. 생성형 템플릿의 영향을 받으므로 실사용 일반화 점수로 단독 사용하지 않고, `change_region`/`replace_condition` 경계가 깨졌는지 확인하는 보조 지표로 둔다. 이 셋의 1.0000도 품질 홍보용 수치가 아니라, 다음 반례 설계의 출발점이다.

Change/replace chat judgment holdout:

| 항목 | 값 |
|---|---:|
| rows | 201 |
| result | 201/201 통과 |
| 평가 방식 | `/tourism/chat` direct 멀티턴 응답 채점 |

`data/eval/tourism_change_replace_chat_holdout.jsonl`은 실제 API 응답에서 지역 전환, 조건 교체, 단순 제외, 더 보기 유지, 맥락 없는 조건 요청을 카드/답변 기준으로 검사한다. focused intent holdout보다 실사용 판단에 가깝지만 같은 생성기에서 만든 focused 멀티턴 셋이므로 표본 수와 생성 방식도 함께 적는다.

2026-05-16 기준 rows는 201건이고 201/201 통과했다. 확장 중 `말고` 뒤 새 선호 분리, 지역 교체 파싱, `replace_condition`의 이전 조건/선호 누적, 과거 지명 negation, 광역 전환 시 이전 sigungu 누수, 조사형 제외 표현 문제를 발견해 수정했다.

Adversarial chat holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_adversarial_chat_holdout.jsonl` |
| rows | 42 |
| result | 42/42 통과 |
| 평가 방식 | `/tourism/chat` direct 멀티턴 응답 채점 |

`data/eval/tourism_adversarial_chat_holdout.jsonl`은 일반 회귀 통과용이 아니라 실패 탐색용이다. 조사형 제외 표현, 과거 지명 뒤 지역 전환, 한 문장 안의 이중 `말고`, 맥락 없는 후속 발화, 중복 지명 clarification을 별도 추적한다.

Context specific-facility adversarial holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl` |
| rows | 980 |
| 생성 스크립트 | `scripts/generate_tourism_context_specific_facility_adversarial_holdout.py` |
| 최초 adversarial 평가 | exact 0.7102 / micro-F1 0.8809 |
| 최신 경계 보강 후 평가 | exact 0.9929 / micro-F1 0.9950 |
| 품질 점수 포함 | 제외 |

이 holdout은 locked test에서 `specific_facility_required` precision/recall/F1이 모두 1.0000으로 나온 결과를 그대로 믿지 않기 위해 추가했다. 최초 실행에서는 `추측 말고 확인된 근거`, `시설 조건은 묻지 않아`, `둘 중 하나만 되는 곳은 제외` 같은 문장에서 오류가 드러났다. 보강 후 최신 exact/micro-F1은 0.9929/0.9950까지 올랐지만, 이것도 실사용 일반화 증명이 아니라 현재 작성한 시설 조건 경계 반례를 대부분 통과했다는 뜻으로만 본다. 다음 갱신 때는 같은 유형 반복이 아니라 새로운 부정/선택/필수 경계 문장을 추가해야 한다.

이 셋을 갱신할 때 반드시 포함할 문항 유형:

- 시설명을 명시적으로 요구하는 문장
- 시설명이 나오지만 요청이 아니라고 부정하는 문장
- 시설은 참고/선택 조건이라고 말하는 문장
- `둘 다`, `둘 중 하나만 제외`, `또는`, `없으면 B라도` 같은 AND/OR 경계 문장
- 이전 조건을 버리고 새 시설 조건으로 바꾸는 문장
- 장소 유형 제외와 시설 조건 부정이 한 문장에 섞인 문장
- 가족/이동성 맥락과 시설 조건이 겹치는 문장

평가 명령:

```bash
.venv/bin/python scripts/generate_tourism_context_specific_facility_adversarial_holdout.py
.venv/bin/python scripts/eval_tourism_context_classifier.py --train data/processed/context_finetune/train.jsonl --model data/processed/tourism_context_classifier_independent_split.json --input data/eval/tourism_context_specific_facility_adversarial_holdout.jsonl --output data/generated/tour_api/context_classifier_eval_specific_facility_adversarial_latest.json
```

Context blind holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_context_blind_holdout.jsonl` |
| rows | 80 |
| 생성 스크립트 | `scripts/generate_tourism_context_blind_holdout.py` |
| 기존 generator 재사용 | 안 함 |
| rule-only | exact 0.4750 / micro-F1 0.7304 |
| LogisticRegression 단독 | exact 0.5125 / micro-F1 0.7512 |
| Hybrid LogisticRegression | exact 0.4500 / micro-F1 0.7296 |
| 보강 후 Hybrid LinearSVC | exact 0.6250 / micro-F1 0.8340 |
| 품질 점수 포함 | 별도 blind 지표로만 사용 |

이 holdout은 “경계/계약 테스트 1.0000”이 실제 일반화가 아니라는 가설을 검증하기 위해 만들었다. 사람이 쓴 문장을 지금 확보할 수 없으므로 Codex가 별도 LLM 역할로 작성하되, 기존 `generate_tourism_context_interpretation_data.py`, `generate_tourism_context_independent_validation.py`, `generate_tourism_context_specific_facility_adversarial_holdout.py`의 템플릿 family를 재사용하지 않는다.

최초 실행에서 1.0000이 바로 깨졌고, 이후 실패 bucket을 train-only extra data 생성에 사용했다. 따라서 이 파일은 이제 untouched blind가 아니라 tuned diagnostic이다. 최종 품질 판단은 매 cycle 새로 만드는 rotating blind에서 한다. 주요 실패 유형은 다음이다.

- `둘 중 하나라도 빠지면`, `패스할게` 같은 strict AND 표현 누락
- `엘베`, `유아 의자`, `애기` 같은 실제 발화형 동의어 누락
- `없으면 ...라도`, `베스트지만 없으면` 같은 OR 표현의 add/strict 오인
- `후보 적을 때만 가산점`, `필수까진 아니야` 같은 soft 조건의 시설 필수 오인
- `주차 말고 주제`, `수어라는 단어가 들어간 이름` 같은 부정/near-miss 처리

평가 명령:

```bash
.venv/bin/python scripts/generate_tourism_context_blind_holdout.py
.venv/bin/python scripts/eval_tourism_context_classifier.py --train data/processed/context_finetune/train.jsonl --model data/processed/tourism_context_classifier_independent_split.json --input data/eval/tourism_context_blind_holdout.jsonl --output data/generated/tour_api/context_classifier_eval_blind_holdout_latest.json
```

Context blind chat eval:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_context_blind_chat_eval.jsonl` |
| rows | 10 |
| 생성 스크립트 | `scripts/generate_tourism_context_blind_chat_eval.py` |
| 평가 방식 | `/tourism/chat` fallback-only direct |
| 최초 결과 | 9/10 통과 |
| 최신 결과 | 10/10 통과 |
| 최초 실패 | `TCBLIND005` `card_count_low` |

이 평가는 context label만 보지 않고 실제 카드 반환과 답변 문구를 본다. 2026-05-17 최초 실패는 `전주에서 시장 골목 말고 조용한 곳만 보고 싶어`에서 후보가 0장으로 나온 케이스다. 시장 제외 파싱, `취소` 표현, preference hard filter를 보정한 뒤 최신 실행은 10/10 통과한다. 이는 문맥 라벨 문제가 아니라 실제 후보 검색/랭킹/부족 안내 품질까지 같이 봐야 하는 사례다.

Context rotating blind holdout:

| 항목 | 값 |
|---|---:|
| 파일 | `data/eval/tourism_context_rotating_blind_holdout_20260517.jsonl` |
| rows | 80 |
| 생성 스크립트 | `scripts/generate_tourism_context_rotating_blind_holdout.py` |
| 기존 train/fixed blind text overlap | 0 |
| 최초 Hybrid LinearSVC | exact 0.5750 / micro-F1 0.8163 |
| 보강 후 Hybrid LinearSVC | exact 0.9750 / micro-F1 0.9919 |
| 품질 점수 포함 | 최신 fresh blind 지표로 사용 |

rotating blind는 고정 blind를 보강에 사용한 뒤 새로 만드는 검증셋이다. 이번 파일은 오류 분석에 사용했으므로 이제 tuned diagnostic이다. 같은 파일을 반복해서 1.0000으로 만드는 대신, 매 cycle 새 문장을 만들어 약점이 실제로 줄었는지 본다.

평가 명령:

```bash
.venv/bin/python scripts/generate_tourism_context_blind_chat_eval.py
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_context_blind_chat_eval.jsonl --output data/generated/tour_api/eval_runs/tourism_context_blind_chat_eval_latest.jsonl
```

```bash
GEMINI_API_KEY=... .venv/bin/python scripts/generate_tourism_intent_gemini_holdout.py --target 770
GEMINI_API_KEY=... .venv/bin/python scripts/verify_tourism_intent_gemini_holdout.py --batch-size 25 --timeout 90 --max-retries 4
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_gemini_holdout_verified.jsonl
.venv/bin/python scripts/generate_tourism_intent_hard_holdout.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_hard_holdout.jsonl
.venv/bin/python scripts/generate_tourism_intent_region_clarify_stress.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_region_clarify_stress.jsonl
.venv/bin/python scripts/generate_tourism_intent_region_clarify_natural_holdout.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_region_clarify_natural_holdout.jsonl
.venv/bin/python scripts/generate_tourism_intent_change_replace_natural_holdout.py
.venv/bin/python scripts/eval_tourism_intent_classifier.py --input data/eval/tourism_intent_change_replace_natural_holdout.jsonl
.venv/bin/python scripts/generate_tourism_change_replace_chat_holdout.py
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_change_replace_chat_holdout.jsonl --output data/generated/tour_api/eval_runs/tourism_change_replace_chat_holdout_latest.jsonl
.venv/bin/python scripts/generate_tourism_adversarial_chat_holdout.py
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_adversarial_chat_holdout.jsonl --output data/generated/tour_api/eval_runs/tourism_adversarial_chat_holdout_latest.jsonl
```

Hugging Face에서 확인한 참고 데이터셋:

- `neuralfoundry-coder/clinc150-ko`: 한국어 번역 CLINC150 intent/out-of-scope 데이터셋, <https://hf.co/datasets/neuralfoundry-coder/clinc150-ko>
- `AIWORKX/KoSGD`: 한국어 Schema-Guided Dialogue 데이터셋, NLU/DST/Intent 참고용, <https://hf.co/datasets/AIWORKX/KoSGD>
- `wicho/kor_3i4k`: 한국어 짧은 발화 의도 분류 데이터셋, <https://hf.co/datasets/wicho/kor_3i4k>
- `bitext/Bitext-travel-llm-chatbot-training-dataset`: 영어 travel chatbot tagged 데이터셋, 관광 도메인 intent 설계 참고용, <https://hf.co/datasets/bitext/Bitext-travel-llm-chatbot-training-dataset>

## 2026-05-15 fallback-only 실행 결과

실행 명령:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct
```

결과 파일: `data/generated/tour_api/eval_runs/tourism_eval_20260515-191900.jsonl`

요약:

| 항목 | 결과 |
|---|---:|
| 총 문항 | 20 |
| HTTP/API 실패 | 0 |
| `indexed` | 14 |
| `cache` | 1 |
| `sample` | 1 |
| `clarification` | 2 |
| `unsupported` | 1 |
| `unknown` | 2 |
| `reasoning_assist_used=true` | 4 |

확인된 개선:

- `이동하기 좋은`의 `이동`을 행정동으로 오인해 clarification을 띄우던 문제를 수정했다.
- `남구`처럼 여러 시도에 있는 구 이름은 특정 지역으로 추정하지 않고 후보 선택 질문을 반환한다.
- `서울 강남구에 바닷가...`처럼 지역 전제와 장소 특성이 맞지 않으면 강남구 일반 카드를 반환하지 않는다.
- `휠체어 대여 가격이 제일 싼 곳`처럼 MVP 범위를 벗어난 가격 비교 질문은 `unsupported`로 답하고 카드를 만들지 않는다.
- 복합 상황 질문 4개에서 LLM 추론 보조가 켜졌을 때 지연 시간은 대략 6~12초였다. 같은 eval을 `TOURISM_REASONING_ASSIST_ENABLED=false`로 실행하면 해당 문항은 80ms 안팎으로 끝났고 실패는 없었다. 따라서 MVP 기본값은 추론 보조 OFF로 둔다.

남은 문제와 해결책:

| 문항 | 현재 상태 | 해결책 |
|---|---|---|
| TQ004 부산 중구 휠체어 | 2장 반환 | 부산 중구 fallback/live 캐시 후보를 3장 이상 확보한다. |
| TQ005 부산 중구 유모차 | 1장 반환 | 유모차/가족 태그가 있는 부산 중구 후보를 보강하거나 live 조회 결과를 캐시한다. |
| TQ014 울릉군 휠체어 | 근거 없음 안내 | 울릉군은 fallback 부족 지역으로 남긴다. live-on-miss 실행 시 TourAPI 결과가 있는지 별도 확인한다. |
| TQ018 강남구 바닷가 | 근거 없음 안내 | 올바른 동작이다. 향후에는 “강남구에는 바닷가 후보가 없어 한강/실내/근처 해안 지역 중 선택” 같은 대체 질문을 제안할 수 있다. |
| TQ006/TQ007/TQ008/TQ020 복합 질문 | 추론 보조 ON 시 6~12초, OFF 시 약 80ms | 기본 시연은 OFF로 둔다. ON/OFF eval 결과의 카드 ID 순서, 카드 수, `lookup_mode`, `warnings`, `suggested_messages`를 비교해 질문 의도 파악 차이를 잡는다. |

다음 eval 단계:

1. 같은 20문항을 live-on-miss 모드로 실행해 fallback-only와 비교한다.
2. 카드가 3장 미만인 부산 중구, 울릉군을 보강 대상 목록에 넣는다.
3. 수동 채점표에 지역 해석, 조건 반영, 근거 준수, 상담 톤 점수를 기록한다.
4. 추론 보조 OFF 기본 모드에서 복합 질문 의도 파악이 약해지는지 ON/OFF eval 비교표로 확인한다.

## 채점 기준

각 문항은 1~5점으로 수동 채점한다.

| 항목 | 1점 | 5점 |
|---|---|---|
| 지역 해석 | 엉뚱한 지역을 추천 | 질문 지역 또는 선택 질문을 정확히 처리 |
| 조건 반영 | 휠체어/유모차 등 조건 무시 | 카드 근거와 조건이 연결됨 |
| 근거 준수 | 없는 정보를 단정 | 출처/카드 범위 안에서 답변 |
| 부족/모름 처리 | 결과를 지어냄 | 부족, 확인 필요, 선택 필요를 명확히 말함 |
| 상담 톤 | 기계적이거나 장황 | 짧고 한국어 상담형으로 자연스러움 |
| 진단 가능성 | QA가 경로를 알 수 없음 | `lookup_mode`, `warnings`, 카드 수, `reasoning_assist_used`로 확인 가능 |

## 문항 목록

| ID | 분류 | 질문 | 핵심 기대 |
|---|---|---|---|
| TQ001 | 시군구 고정 | 서울 강남구에서 휠체어 관광지 추천해줘 | 강남구만 우선, 부족 안내 |
| TQ002 | 근처 표현 | 서울 강남구 근처에서 휠체어 타고 갈 수 있는 관광지 추천해줘 | 강남구 기준 우선, 서울 전체 자동 확장 금지 |
| TQ003 | 모호 지역 | 중구에서 휠체어 타시는 어머니를 모시고 다닐 수 있는 관광지를 추천해줘 | 중구 선택 후보 반환 |
| TQ004 | 지역 확정 | 부산 중구에서 휠체어 타고 갈 수 있는 관광지 추천해줘 | 부산 중구로 확정 |
| TQ005 | 축약 주소 | 부산 중구 유모차로 갈만한 곳 알려줘 | 풀네임 없이 부산 중구 인식 |
| TQ006 | 관계 호칭 | 젊은 아빠가 휠체어를 타는데 아이랑 같이 갈만한 서울 관광지 추천해줘 | 아빠를 고령자로 추정하지 않음 |
| TQ007 | 고령자 명시 | 서울에서 고령자 부모님과 휠체어로 이동하기 좋은 실내 관광지 추천해줘 | 명시된 고령자/휠체어 맥락 반영 |
| TQ008 | 가족/유모차 | 유모차 끌고 부산에서 아이랑 가기 좋은 무장애 관광지 찾아줘 | 가족/유모차 조건 반영 |
| TQ009 | 보조견 | 시각장애인 보조견과 같이 갈 수 있는 인천 관광지 추천해줘 | 보조견/시각장애 편의 우선 |
| TQ010 | 장애인 화장실 | 대전에서 장애인 화장실 정보가 있는 관광지 알려줘 | 화장실 근거 연결 |
| TQ011 | 장애인 주차 | 제주에서 장애인 주차장 있는 관광지 추천해줘 | 주차 정보 확인 또는 확인 필요 |
| TQ012 | 강릉 | 강릉에서 휠체어로 갈만한 관광지 5곳 추천해줘 | 강릉 관련 카드 3~5개 |
| TQ013 | 대구 | 대구에서 부모님 모시고 천천히 둘러볼 수 있는 무장애 관광지 추천해줘 | 부모님만으로 고령자 단정 금지 |
| TQ014 | 저커버리지 | 울릉군에서 휠체어 접근 가능한 관광지 추천해줘 | 근거 부족 시 섞지 않고 안내 |
| TQ015 | 모호 지역 | 남구에서 유모차로 갈 수 있는 곳 추천해줘 | 남구 선택 후보 반환 |
| TQ016 | 지역 확정 | 울산 남구에서 유모차로 이동하기 좋은 관광지 추천해줘 | 울산 남구로 확정 |
| TQ017 | 출처 요청 | 서울에서 휠체어 가능한 관광지를 추천하고 출처도 같이 알려줘 | 출처 유지 |
| TQ018 | 잘못된 전제 | 서울 강남구에 바닷가 휠체어 관광지 추천해줘 | 바닷가 후보를 지어내지 않음 |
| TQ019 | 범위 밖 | 휠체어 대여 가격이 제일 싼 곳 알려줘 | 가격 비교 추측 금지 |
| TQ020 | 경로 진단 | 충북에서 휠체어 접근 가능하고 가족이 같이 가기 좋은 관광지 추천해줘 | `lookup_mode`와 warnings 확인 |

## 2026-05-16 80문항 fallback-only 실행 결과

실행 명령:

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct --input data/eval/tourism_80_questions.jsonl
```

결과 파일: `data/generated/tour_api/eval_runs/tourism_eval_20260516-031323.jsonl`

요약:

| 항목 | 결과 |
|---|---:|
| 총 문항 | 80 |
| HTTP/API 실패 | 0 |
| `indexed` | 56 |
| `cache` | 6 |
| `sample` | 4 |
| `clarification` | 10 |
| `unsupported` | 1 |
| `unknown` | 3 |
| `reasoning_assist_used=true` | 0 |

확인된 개선:

- 지역이 없는 질문은 임의 전국 후보를 반환하지 않고 지역 확인 질문으로 보낸다.
- 광역 지역의 잘못된 바닷가/해수욕장 전제도 후보를 지어내지 않고 `unknown`으로 처리한다.
- 의료기관, 차량 예약, 가격순, 이동시간 계산처럼 범위 밖 요청이 부가 조건으로 섞이면 경고를 남기고 관광 접근성 카드 근거 안에서만 답한다.
- 지하철역 바로 연결, 실시간 혼잡도처럼 범위 밖 조건이 핵심 필터인 질문은 카드 추천 전에 조건 완화 여부를 재확인한다.
- 2026-05-16 추가 시군구 fallback 수집 후 `TQ014` 울릉군, `TQ071` 영양군, `TQ072` 신안군 같은 저커버리지 문항이 카드 반환으로 개선됐다.

남은 확인 포인트:

- `TQ038`의 `광주`처럼 지명이 광역시와 시군구 alias 사이에서 clarification으로 흐르는 문항은 의도한 UX인지 확인한다.
