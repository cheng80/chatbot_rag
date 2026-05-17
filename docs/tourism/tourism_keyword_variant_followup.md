# 핵심어 변형 보강 후속 작업

마지막 갱신: 2026-05-18

이 문서는 오타, 띄어쓰기 붕괴, 동의어, 우회 표현을 계속 보강하기 위한 작업 지침이다.
`data/processed/tourism_keyword_variants_20260518_5000.valid.jsonl`과 그 후속 리포트를 기준으로 한다.

## 현재 결론

핵심어 5,000건은 단순 성능 홍보용 데이터가 아니다.
사용자가 실제로 틀릴 수 있는 표현을 넓게 만들어 현재 파서가 어디서 실패하는지 찾는 진단/학습 후보 데이터다.

현재까지의 개선은 다음과 같다.

| 단계 | 현재 파서 exact | mismatch | promote candidate mismatch |
|---|---:|---:|---:|
| 최초 5,000건 | 2,607 | 2,393 | 1,645 |
| 1차 안전 후보 반영 | 3,563 | 1,437 | 726 |
| bucket 보강 후 | 4,298 | 702 | 159 |

중요한 해석:

- 1,645건은 모두 추가해야 할 후보가 아니었다.
- 726건에는 `missing`과 `extra`가 섞여 있었다.
- `extra`의 대부분은 `장애인 주차/화장실/보조견`에서 `장애인` 단어 하나 때문에 `휠체어`가 추가되는 과해석이었다.
- 따라서 보강은 “더 많이 넣기”가 아니라 “필요한 것은 넣고, 과해석은 제거”하는 방향이어야 한다.

## 이미 적용한 보강

정규화기에 반영:

- `휠쳐`, `휠 체어`, `휠체 어` -> `휠체어`
- `보조갼`, `보조 견`, `안내 견`
- `앨리베이터`, `엘리배이터`, `엘리 베이터`, `승 강기`
- `출입 통로`, `접근 로`, `경 사로`, `무 단차`, `턱없음`
- `자 막`, `문자 안내`, `영상 안내`, `청각 장애`, `시각 장애`
- `유모 차`, `아가랑`, `무릅 불편`, `부모 님`, `어르 신`, `고령 자`

조건 키워드에 반영:

- `바퀴 의자`, `바퀴의자`
- `무단차`, `평탄한 길`, `출입통로`, `입구에 턱이 없는`, `유모차 바퀴가 걸리지`
- `부모님`, `무릎 불편`, `오래 걷기 힘든 분`, `무리 없는`, `쉬어 갈 곳`
- `층 이동이 편한`, `위아래 이동이 쉬운`, `계단 말고 올라갈`
- `영상안내`, `문자안내`, `영상에 글자 안내`, `소리 없이도 안내를 볼 수`
- `손으로 만져 확인할 안내`, `소리 안내`

과해석 제거:

- `장애인` 단독을 `휠체어` 조건 키워드에서 제거했다.
- `장애인 화장실`, `장애인 주차`, `장애인 보조견`은 각각 화장실/주차/보조견 조건으로 본다.
- 무장애, 접근성, 이동약자, 베리어프리, 휠체어, 바퀴 의자처럼 이동 접근성 의미가 명확할 때만 휠체어 조건으로 본다.

## 남은 159건 처리 원칙

남은 `data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_bucket_patch_review_queue.jsonl` 159건은 무조건 줄이는 대상이 아니다.
남은 후보는 아래 기준으로 처리한다.

### 1. 바로 적용 가능

다음 조건을 모두 만족하면 정규화기 또는 조건 키워드에 추가한다.

- 표현이 특정 조건으로 거의 고정된다.
- 장소 유형, 예약, 교통수단, 의료, 가격 의미와 충돌하지 않는다.
- 실제 `/tourism/chat` 카드 결과에서 과필터링을 만들지 않는다.
- negative/ambiguous row를 새로 만들어도 통과한다.

### 2. 조건부 반영 또는 보류

다음 표현은 단독으로는 바로 사전에 넣지 않고 주변 맥락을 본다.

- `리프트` 단독
  - 엘리베이터/승강 설비 의미도 있지만, 리프트 차량/예약/이동지원 서비스와 충돌한다.
  - `리프트 차량`, `예약`, `업체`와 같이 나오면 현재 미지원 영역이다.
  - `휠체어 리프트`, `장애인 리프트`, `승강 리프트`, `승강용 리프트`, `계단 리프트`, `지하철 리프트`, `시설 리프트`, `건물 리프트`, `관광시설 리프트`, `공공기관 리프트`처럼 시설 맥락이 분명하면 접근성 승강 설비로 본다.
  - 지하철, 공공기관, 공공시설만 대상으로 한정하지 않는다. 관광시설, 전시관, 공연장, 상업시설, 역사 같은 장소에도 휠체어 리프트가 접근성 설비로 존재할 수 있으므로 조건부 반영 대상이다.
- 너무 넓은 paraphrase
  - `편한 곳`, `무리 없는 곳`, `가기 쉬운 곳` 같은 표현은 단독 조건으로 승격하지 않는다.
  - 지역/장소/동반자/시설 힌트와 함께 있을 때만 문맥 분류기 후보로 본다.

### 3. 모델/문맥 학습으로 넘김

다음은 단어 사전보다 문맥 분류기 또는 Transformer 후보 학습으로 넘긴다.

- `소리 없이도 안내를 볼 수 있는`
- `손으로 만져 확인할 안내가 있는`
- `계단 말고 올라갈 수 있는`
- `바퀴 달린 의자로 이동 가능한`
- `부모님이 무리 없는`

이 표현들은 지금 일부 키워드에 반영했지만, 앞으로는 단순 substring보다 문맥 classifier가 더 적합하다.

## 다음 작업 순서

1. 남은 review queue를 bucket별로 다시 요약한다.

```bash
.venv/bin/python - <<'PY'
import json
from collections import Counter
from pathlib import Path
path = Path("data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_after_bucket_patch_review_queue.jsonl")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
print("rows", len(rows))
print("variant_type", Counter(row["variant_type"] for row in rows))
print("missing", Counter(item for row in rows for item in row["parser_missing_conditions"]).most_common())
print("extra", Counter(item for row in rows for item in row["parser_extra_conditions"]).most_common())
PY
```

2. 후보를 세 그룹으로 나눈다.

| 그룹 | 처리 |
|---|---|
| 명확한 typo/spacing | `KoreanQueryNormalizer.TYPO_REPLACEMENTS` 또는 `PHRASE_REPLACEMENTS`에 추가 |
| 명확한 동의어 | `CONDITION_KEYWORDS`에 추가 |
| paraphrase/충돌 후보 | 문맥 학습셋 또는 추가질의 후보로 이동 |

3. 보강 후 반드시 5,000건을 다시 검증한다.

```bash
.venv/bin/python scripts/validate_tourism_keyword_variant_dataset.py \
  --input data/generated/tour_api/keyword_variant_batches/keyword_variant_batch_20260518_gpt_style_5000.raw.jsonl \
  --output data/processed/tourism_keyword_variants_20260518_5000.next.valid.jsonl \
  --report data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_next_report.json \
  --review-queue data/generated/tour_api/keyword_variant_reports/keyword_variant_20260518_5000_next_review_queue.jsonl \
  --min-rows 5000
```

4. 실제 chat 평가도 같이 본다.

```bash
.venv/bin/python -m pytest tests/test_korean_query_normalizer.py tests/test_tourism_quality_regression.py tests/test_tourism_query_service.py -q
.venv/bin/python -m pytest -q
```

5. 성능 수치만 보고 끝내지 않는다.

- `parser_exact_rows`가 올라갔는지 본다.
- `parser_extra_conditions`가 늘지 않았는지 본다.
- 일반 관광 질문이 무장애 조건으로 과해석되지 않는지 본다.
- `/tourism/chat` 카드가 요청 조건과 맞는지 표본 확인한다.

## 외부 데이터 필요 여부

지금 단계에서 외부 데이터가 반드시 필요하지는 않다.
이미 5,000건 안에 충분한 실패 후보가 있다.

외부 데이터가 필요한 시점:

- 남은 159건 중 실제 사용자 로그와 겹치는 표현을 우선순위화할 때
- 단독 `리프트`, `이동지원`, `편한 곳`처럼 의미가 넓은 표현의 실제 사용 맥락을 확인할 때
- Transformer/robust NLU 후보를 학습할 때 일반화 검증용 별도 blind set이 필요할 때

외부 데이터를 가져오더라도 바로 학습에 넣지 않는다.
먼저 taxonomy 재라벨링, 중복 제거, negative/ambiguous 반례 생성, 실제 chat 카드 평가를 통과해야 한다.
