# Noisy realistic 잔여 실패 분류

마지막 갱신: 2026-05-27

## 기준

입력 파일:

```text
data/eval/tourism_noisy_realistic_chat_eval_v1_200.jsonl
```

최신 실행 결과:

```text
data/generated/tour_api/eval_runs/noisy_realistic_v1_200_topk40_service_scope_copy_fix.jsonl
```

TOP_K=40과 unsupported 답변 문구 수정 후 200건 중 28건이 실패로 남았다.
`answer_missing_any_term` 14건은 해결됐고, 남은 실패는 서비스 범위 답변 문제가 아니라 카드/근거 데이터 부족이다.

## Bucket

| Bucket | 대표 조건 | 처리 원칙 |
|---|---|---|
| sensory_low_coverage | 수어, 수화, 자막, 영상에 글자 안내 | 카드에 실제 수어/자막/영상안내 근거가 없으면 추천하지 않는다. 문구로 해결하지 않는다. |
| tactile_low_coverage | 점자블록, 점자 안내, 촉지도 | 실제 편의정보에 점자/촉지도 근거가 없으면 추천하지 않는다. 테마/전시명 near-miss는 제외한다. |
| service_animal_low_coverage | 보조견 | 보조견 동반 가능 근거가 없으면 추천하지 않는다. 동물 테마/작품명 near-miss는 제외한다. |
| strict_combo_low_coverage | 장애인 화장실 + 점자, 엘리베이터 + 점자 등 | strict 조합은 둘 다 근거가 확인될 때만 카드로 반환한다. |
| multiturn_evidence_low_coverage | 첫 턴은 카드가 있으나 후속 조건 추가 뒤 0장 | 이전 카드가 새 조건 근거를 갖지 않으면 0장과 확장 제안을 유지한다. |

## 결정

- 남은 28건은 코드 과수정 대상이 아니다.
- 해결하려면 TourAPI/live Markdown/fallback Markdown에서 해당 편의정보가 실제로 있는 카드를 추가 수집해야 한다.
- 수집 전에는 실패 상태를 “희소 접근성 근거 부족”으로 유지한다.
- 자동 채점 실패를 없애기 위해 `수어`, `점자`, `보조견`을 넓은 무장애/휠체어 근거로 대체하지 않는다.

## 다음 데이터 보강 후보

1. 수어/자막/영상안내 근거가 있는 문화시설
2. 점자블록/점자 안내/촉지도 근거가 있는 시각장애 접근성 시설
3. 보조견 동반 가능이 명시된 공공 관광지
4. 위 조건이 시군구 단위로 부족할 때 광역 확장 안내를 유지할 수 있는 fallback 카드
