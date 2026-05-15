# 관광 챗봇 로컬 모델 추론 벤치마크

마지막 갱신: 2026-05-15

## 목적

복합 관광 질문에서 LLM은 장소를 새로 찾는 주체가 아니라, 이미 확보한 `TourismPlaceCard` 후보를 사용자 상황에 맞게 재랭킹하고 상담형 문장으로 정리하는 보조 계층이다.

이 문서는 어떤 로컬 모델을 `/tourism/chat`의 추론 보조 모델로 쓸지 비교하기 위한 실행 기준과 결과 기록이다.

## 비교 후보

| 모델 | 역할 | 선택 이유 |
|---|---|---|
| `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` | 현재 기준선 | 현재 `.env.example` 기본 답변 모델이며 한국어 상담 품질 확인 대상 |
| `gemma3:4b-it-q4_K_M` | 빠른 기준선 | 기존 비교 모델, native thinking 없이 속도와 안정성 기준 제공 |
| `gemma4:e4b` | 공식 Gemma 4 후보 | Ollama 페이지 기준 Gemma 4 E4B는 thinking capability를 제공하며 한국어 맥락 후보로 유지 |
| `qwen3:4b` | thinking 후보 | Ollama 로컬 확인 기준 `Capabilities: thinking` 노출, 작은 크기로 지연 시간 비교 가능 |
| `huihui_ai/gemma-4-abliterated:e4b` | 사용자 제안 후보 | Gemma 4 기반 abliterated 모델. 단, 안전 필터 약화 경고가 있어 공개 서비스 기본값 후보로는 신중해야 함 |

`deepseek-r1` 계열은 reasoning 후보지만, 이번 MVP Mac mini 기준에서는 다운로드 크기와 지연 시간이 커질 수 있어 후순위 후보로 둔다.

## 실험 방식

실험 스크립트:

```bash
.venv/bin/python scripts/benchmark_tourism_reasoning_models.py
```

주요 옵션:

```bash
.venv/bin/python scripts/benchmark_tourism_reasoning_models.py \
  --models gemma4:e4b qwen3:4b huihui_ai/gemma-4-abliterated:e4b \
  --runs 1
```

출력 파일:

```text
data/generated/tour_api/model_benchmarks/tourism_model_benchmark_YYYYMMDD-HHMMSS.jsonl
```

이 파일은 생성 산출물이므로 커밋하지 않는다. 결과 요약만 이 문서에 남긴다.

## 측정 항목

| 항목 | 의미 |
|---|---|
| `elapsed_ms` | Ollama API 호출 전체 시간 |
| `think=false` | 일반 응답 모드 |
| `think=true` | Ollama native thinking 요청 |
| `supports_native_thinking_observed` | 응답에 `thinking` 필드가 실제로 존재했는지 |
| `json_parse_ok` | 재랭킹 프롬프트가 JSON-only 계약을 지켰는지 |
| `ranked_ids` | 후보 카드 ID만 반환했는지 |
| `response_excerpt` | 최종 답변 품질 수동 확인용 일부 |

## 프롬프트 범위

벤치마크는 두 가지 최소 시나리오만 본다.

1. 복합 조건 후보 재랭킹: 비 오는 날, 휠체어 동행, 초등학생 동행 조건에서 카드 순서를 JSON으로 반환.
2. 한국어 상담 답변: 같은 카드 근거로 짧은 한국어 추천문 작성.

이 실험은 TourAPI나 Chroma 검색 품질을 측정하지 않는다. 이미 확보된 카드 후보를 LLM이 얼마나 잘 다루는지만 본다.

`think=true`는 reasoning 토큰을 별도로 소모하므로 일반 응답보다 더 큰 `num_predict` 예산으로 측정한다. 짧은 예산에서는 thinking 필드만 생성되고 최종 `response`가 비는 경우가 있다. 실서비스 추론 보조는 긴 사고 로그가 아니라 짧은 재랭킹이 목적이므로, 벤치마크 프롬프트도 “판단은 짧게, 최종 출력만”을 명시한다.

## 현재 판정 기준

MVP 기본 모델은 아래 조건을 만족해야 한다.

- 한국어 답변이 자연스럽다.
- 후보 카드에 없는 접근성 정보를 만들지 않는다.
- JSON-only 재랭킹 계약을 안정적으로 지킨다.
- 복합 질문에서만 추가 지연을 감수할 수 있다.
- 공개 테스트용 기본 모델은 안전 필터가 과도하게 제거된 모델을 피한다.

따라서 abliterated 모델은 실험 후보로는 포함하되, 공개 사용자에게 열리는 기본값은 수동 검토 후 결정한다.

## 2026-05-15 실행 기록

실행 전 확인:

- `qwen3:4b`: Ollama `Capabilities`에 `thinking` 포함.
- `gemma4:e4b`: Ollama `Capabilities`에 `thinking` 포함.
- `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M`: 이전 로컬 확인 기준 `think=true` 미지원.
- `gemma3:4b-it-q4_K_M`: 이전 로컬 확인 기준 `think=true` 미지원.

실행 명령:

```bash
.venv/bin/python scripts/benchmark_tourism_reasoning_models.py \
  --models hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M gemma3:4b-it-q4_K_M gemma4:e4b qwen3:4b huihui_ai/gemma-4-abliterated:e4b \
  --runs 1 \
  --timeout 600
```

결과 파일:

```text
data/generated/tour_api/model_benchmarks/tourism_model_benchmark_20260515-193912.jsonl
```

| 모델 | 모드 | 재랭킹 JSON | native thinking 관측 | 속도 메모 | 1차 판단 |
|---|---|---|---|---|---|
| `gemma3:4b-it-q4_K_M` | `think=false` | 성공, `C1,C4,C2,C3` | 없음 | JSON 5.2초, 답변 2.8초 | 가장 빠른 기준선. 답변은 짧고 보수적이나 상담 품질은 약함 |
| `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` | `think=false` | 성공, `C4,C1,C2` | 없음 | JSON 7.0초, 답변 6.6초 | 현재 기본값 유지 가능. native thinking은 미지원 |
| `gemma4:e4b` | `think=false` | 성공, `C4,C2,C1` | 없음 | JSON 9.4초, 답변 6.4초 | 공식 Gemma 4 후보 중 가장 균형적 |
| `gemma4:e4b` | `think=true` | 성공, `C4,C2` | 있음 | JSON 29.8초, 답변 34.3초 | 품질은 좋지만 MVP 실시간 기본값으로는 느림. 필요 시 제한적 사용 |
| `qwen3:4b` | `think=false` | 실패 | 없음 | JSON 7.9초, 답변 7.6초 | 영어 사고문이 섞여 JSON 계약과 한국어 답변 계약을 못 지킴 |
| `qwen3:4b` | `think=true` | 실패 | 있음 | JSON 48.9초, 답변 67.4초 | native thinking은 되지만 너무 느리고 최종 응답이 불완전함 |
| `huihui_ai/gemma-4-abliterated:e4b` | `think=false` | 성공, `C4,C1,C2` | 없음 | JSON 9.2초, 답변 8.6초 | 성능은 괜찮지만 안전 필터 약화 때문에 공개 기본값은 보류 |
| `huihui_ai/gemma-4-abliterated:e4b` | `think=true` | 성공, `C4,C2` | 있음 | JSON 33.0초, 답변 40.8초 | thinking은 동작하나 지연과 안전성 리스크가 큼 |

현재 결론:

- MVP 기본 추론 보조는 `think=false`로 유지한다.
- 기본 모델 후보는 `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` 유지 또는 공식 `gemma4:e4b` 전환을 20문항 eval 수동 채점 뒤 결정한다.
- native thinking은 복합 질문 전체에 켜기에는 지연 시간이 크다. 데모 전에는 끄고, Post-MVP에서 특정 고난도 질문에만 opt-in하는 방향이 맞다.
- `qwen3:4b`는 thinking capability가 있지만 현재 프롬프트 계약을 지키지 못해 이 프로젝트의 1차 후보에서는 제외한다.
- `huihui_ai/gemma-4-abliterated:e4b`는 사용자가 제안한 모델로 실험 가치는 있지만, safety filtering 약화 경고 때문에 공개 사용자 기본값으로는 보류한다.

## 운영 반영 원칙

- `OLLAMA_CHAT_MODEL` 기본값 변경은 20문항 eval과 이 벤치마크 결과를 같이 본 뒤 한다.
- native thinking이 가능해도 모든 질문에 켜지 않는다. 복합 조건 질문에서만 제한적으로 사용한다.
- thinking 출력은 사용자에게 그대로 노출하지 않는다. 응답에는 `reasoning_assist_used`, `reasoning_assist_notes` 같은 진단만 남긴다.
- 응답 시간이 길면 UI에는 로딩 상태를 명확히 보여준다.
