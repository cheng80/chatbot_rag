# 관광 챗봇 로컬 모델 추론 벤치마크

마지막 갱신: 2026-06-07

## 목적

복합 관광 질문에서 LLM은 장소를 새로 찾는 주체가 아니라, 이미 확보한 `TourismPlaceCard` 후보를 사용자 상황에 맞게 재랭킹하고 상담형 문장으로 정리하는 보조 계층이다.

이 문서는 어떤 로컬 AI provider와 모델을 `/tourism/chat`의 추론 보조 및 RAG embedding 경로에 쓸지 비교하기 위한 실행 기준과 결과 기록이다.

## 비교 후보

| 모델 | 역할 | 선택 이유 |
|---|---|---|
| `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` | 현재 기본값 | 현재 `.env.example` 기본 답변 모델이며 빠른 한국어 상담 답변 후보 |
| `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` | 이전 기준선 | 기존 기본 답변 모델이며 한국어 상담 품질 비교 대상 |
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
  --provider ollama \
  --models gemma4:e4b qwen3:4b huihui_ai/gemma-4-abliterated:e4b \
  --embedding-model bge-m3 \
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
| `provider` | 현재는 Ollama 기준 |
| `task` | `generation` 또는 `embedding` |
| `elapsed_ms` | provider API 호출 전체 시간 |
| `think=false` | 일반 응답 모드 |
| `think=true` | Ollama native thinking 요청 |
| `supports_native_thinking_observed` | 응답에 `thinking` 필드가 실제로 존재했는지 |
| `json_parse_ok` | 재랭킹 프롬프트가 JSON-only 계약을 지켰는지 |
| `ranked_ids` | 후보 카드 ID만 반환했는지 |
| `response_excerpt` | 최종 답변 품질 수동 확인용 일부 |
| `top1_ok` | embedding probe에서 기대 문서가 1순위로 검색됐는지 |
| `embedding_dimension` | embedding vector 차원. provider 전환 시 기존 Chroma collection과 섞이면 안 된다 |

## 프롬프트 범위

벤치마크는 두 가지 최소 시나리오만 본다.

1. 복합 조건 후보 재랭킹: 비 오는 날, 휠체어 동행, 초등학생 동행 조건에서 카드 순서를 JSON으로 반환.
2. 한국어 상담 답변: 같은 카드 근거로 짧은 한국어 추천문 작성.

generation 실험은 TourAPI나 Chroma 검색 품질을 측정하지 않는다. 이미 확보된 카드 후보를 LLM이 얼마나 잘 다루는지만 본다.

embedding 실험은 작은 관광 문서 probe로 top-1 검색 품질과 batch embedding 지연을 본다. 이 probe만으로 최종 검색 품질을 확정하지 않고, provider 전환 후보를 걸러내는 1차 관문으로 쓴다.

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
  --models hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M gemma3:4b-it-q4_K_M gemma4:e4b qwen3:4b huihui_ai/gemma-4-abliterated:e4b \
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
| `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` | `think=false` | 성공, `C4,C1,C2` | 없음 | JSON 7.0초, 답변 6.6초 | 당시 기본값 유지 가능. native thinking은 미지원 |
| `gemma4:e4b` | `think=false` | 성공, `C4,C2,C1` | 없음 | JSON 9.4초, 답변 6.4초 | 공식 Gemma 4 후보 중 가장 균형적 |
| `gemma4:e4b` | `think=true` | 성공, `C4,C2` | 있음 | JSON 29.8초, 답변 34.3초 | 품질은 좋지만 MVP 실시간 기본값으로는 느림. 필요 시 제한적 사용 |
| `qwen3:4b` | `think=false` | 실패 | 없음 | JSON 7.9초, 답변 7.6초 | 영어 사고문이 섞여 JSON 계약과 한국어 답변 계약을 못 지킴 |
| `qwen3:4b` | `think=true` | 실패 | 있음 | JSON 48.9초, 답변 67.4초 | native thinking은 되지만 너무 느리고 최종 응답이 불완전함 |
| `huihui_ai/gemma-4-abliterated:e4b` | `think=false` | 성공, `C4,C1,C2` | 없음 | JSON 9.2초, 답변 8.6초 | 성능은 괜찮지만 안전 필터 약화 때문에 공개 기본값은 보류 |
| `huihui_ai/gemma-4-abliterated:e4b` | `think=true` | 성공, `C4,C2` | 있음 | JSON 33.0초, 답변 40.8초 | thinking은 동작하나 지연과 안전성 리스크가 큼 |

현재 결론:

- MVP 기본 추론 보조는 `think=false`로 유지한다.
- 2026-05-15 당시 기본 모델 후보는 `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` 유지 또는 공식 `gemma4:e4b` 전환을 20문항 eval 수동 채점 뒤 결정하기로 했다.
- native thinking은 복합 질문 전체에 켜기에는 지연 시간이 크다. 데모 전에는 끄고, Post-MVP에서 특정 고난도 질문에만 opt-in하는 방향이 맞다.
- `qwen3:4b`는 thinking capability가 있지만 현재 프롬프트 계약을 지키지 못해 이 프로젝트의 1차 후보에서는 제외한다.
- `huihui_ai/gemma-4-abliterated:e4b`는 사용자가 제안한 모델로 실험 가치는 있지만, safety filtering 약화 경고 때문에 공개 사용자 기본값으로는 보류한다.

## 2026-05-27 provider 정리

Apple Silicon 전용 대안 provider는 실제 서비스 모델과 실제 관광 corpus 기준에서 채택하지 않기로 했다. 관련 실험 venv, 모델 cache, 산출물, 전용 비교 스크립트는 디스크 절약을 위해 삭제했다.

현재 결론:

- `/tourism/chat` generation은 Ollama를 유지한다.
- 서비스 모델은 `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL`를 유지한다.
- embedding은 Ollama `bge-m3`를 유지한다.
- Chroma collection은 기존 `manual_documents`와 `TOP_K=40` 운영을 유지한다.
- provider switching이나 dual-index 구조는 쓰지 않는다. 임베딩 모델이 바뀌면 벡터 공간이 달라져 재색인과 별도 collection이 필요하기 때문이다.

이후 provider 재검토 조건:

1. 현재 서비스 모델과 동등한 GGUF/Ollama 품질을 재현하는 후보가 있어야 한다.
2. JSON-only 재랭킹 계약과 한국어 답변 계약을 통과해야 한다.
3. 실제 관광 corpus retrieval에서 `bge-m3`보다 hit rate/MRR이 높아야 한다.
4. 별도 collection 재색인을 감수할 정도의 품질 이득이 있어야 한다.

## AutoRAG 재도입 가능성

AutoRAG는 운영 런타임으로 되살리지 않고, retrieval-only 오프라인 실험 도구로는 되살릴 수 있다.

2026-05-27 확인:

- `.venv` Python 3.12.10 기준 `pip install --dry-run 'AutoRAG>=0.3.17' 'pandas>=2.2.0' 'pyarrow>=15.0.0' 'kiwipiepy>=0.20.0'`는 resolver 충돌 없이 `AutoRAG-0.3.22`만 추가 설치 대상으로 계산됐다.
- 한국어 BM25 비교 후보로 `ko_okt`, `ko_kkma`를 추가하려면 `konlpy`, `JPype1`, JDK가 필요하다. 로컬 JDK 17 환경에서 `Okt`, `Kkma`, `Kiwi` 초기화는 확인했다.
- 기존 충돌 위험은 Python 3.13, `numpy`, `voyageai`, 대형 RAG provider 의존성이 섞일 때 커진다.
- 메인 서비스는 이미 Chroma, FastAPI, Ollama, 관광 정책 로직을 직접 들고 있으므로 AutoRAG runner를 `/tourism/chat`에 붙이면 복잡도와 장애면이 커진다.

권장 운용:

- `requirements-autorag.txt`, `configs/autorag/*`, `scripts/build_autorag_tourism_dataset.py`는 되살릴 수 있다.
- 설치는 메인 `.venv`보다 `data/generated/tour_api/autorag_venv/` 같은 별도 venv를 권장한다.
- 산출물은 `data/processed/autorag_tourism/` 아래에만 둔다.
- 비교 대상은 BM25, vector-only, hybrid RRF, top-k이며 운영 이식은 점수가 아니라 `/tourism/chat` hard/noisy eval 통과로 결정한다.
- 운영 기본 검색 엔진은 계속 직접 Chroma vector-only다. AutoRAG는 “검색 후보 실험실”로만 둔다.

2026-05-27 BM25 토크나이저 직접 재실험:

- corpus 1,010개, QA 192개에서 `scripts/benchmark_tourism_bm25_tokenizers.py --max-eval-rows 220 --include-ollama-vector`를 실행했다.
- `bge-m3` vector-only는 top40 recall 0.6276, MRR 0.4052, NDCG 0.4388이다.
- BM25 최고 recall은 `ko_kkma` top40 recall 0.5072이지만 MRR 0.2937이고 토큰화가 약 44.6초로 느리다.
- BM25 상위 카드 안정성은 `ko_okt`가 낫다. top5 hit_rate 0.4792, MRR 0.3049다.
- 결론은 운영 vector-only 유지다. BM25는 AutoRAG 오프라인 비교 후보로만 두고, runtime 이식은 보류한다.

## 통합 파이프라인 비교 기준

단일 LLM 호출 속도만으로 런타임 전환을 결정하지 않는다. 실제 `/tourism/chat`의 기본 경로는 아래처럼 단계가 분리돼 있다.

```text
사용자 발화
  -> 한국어 오타/띄어쓰기 보정
  -> 지역/조건/문맥 파싱
  -> 선택적 조건 Transformer
  -> cache/RAG/fallback/live 후보 조회
  -> 필요한 경우에만 LLM reasoning assist
  -> 카드/답변 생성
```

따라서 비교 variant는 최소 아래를 포함한다.

| variant | 맞춤법 보정 | 조건 Transformer | LLM reasoning assist | 모델 |
|---|---|---|---|---|
| `current_runtime` | ET5 local risky-only | off | off | 없음 |
| `et5_roberta_combined` | ET5 local risky-only | on | off | 없음 |
| `current_default_reasoning` | ET5 local risky-only | off | on | `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` |
| `et5_roberta_default_reasoning` | ET5 local risky-only | on | on | `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` |
| `current_gemma3_reasoning` | ET5 local risky-only | off | on | `gemma3:4b-it-q4_K_M` |
| `current_gemma4_reasoning` | ET5 local risky-only | off | on | `gemma4:e4b` |

비교 명령:

```bash
.venv/bin/python scripts/compare_tourism_medium_chat_models.py \
  --include-reasoning-assist \
  --output-dir data/generated/tour_api/medium_chat_model_compare_integrated_latest

.venv/bin/python scripts/compare_tourism_noisy_realistic_chat_models.py \
  --include-reasoning-assist \
  --output-dir data/generated/tour_api/noisy_realistic_chat_model_compare_integrated_latest
```

이 통합 비교에서 봐야 할 것은 단순 pass rate가 아니라 다음 항목이다.

- reasoning assist가 실제로 켜진 문항 수
- 평균/상위 지연 시간
- 카드 수 부족이나 필수 근거 누락이 줄었는지
- unsupported/범위 밖 질문이 다시 관광 카드로 오염되지 않는지
- 맞춤법 보정과 조건 Transformer가 LLM 보조보다 먼저 해결하는 케이스가 얼마나 되는지
- 현재 기본 Unsloth Gemma4가 카드 품질을 올리는지, 아니면 지연만 늘리는지

## 2026-05-27 통합 벤치마크 결과

Rapid/MLX 관련 설정, 스크립트, 의존성은 제거했다. AutoRAG는 retrieval-only 오프라인 실험 도구로 되살렸지만 운영 런타임에는 붙이지 않는다. 기존 검색 운영은 Chroma vector-only `top_k=40` 경로를 유지한다.

중형 120문항 통합 비교:

| variant | pass | mean ms | reasoning assist |
|---|---:|---:|---:|
| `current_runtime` | 104/120 | 402.7 | 0 |
| `current_supergemma4_reasoning` | 104/120 | 2141.0 | 0 |
| `et5_roberta_supergemma4_reasoning` | 104/120 | 2135.2 | 0 |
| `current_gemma3_reasoning` | 104/120 | 4184.1 | 0 |
| `current_gemma4_reasoning` | 104/120 | 6506.8 | 0 |
| `roberta_small_candidate` | 104/120 | 1982.3 | 0 |

노이즈 현실형 200문항 통합 비교:

| variant | pass | mean ms | reasoning assist |
|---|---:|---:|---:|
| `roberta_small_candidate` | 174/200 | 1027.1 | 0 |
| `et5_roberta_combined` | 172/200 | 563.1 | 0 |
| `et5_roberta_supergemma4_reasoning` | 172/200 | 1198.0 | 0 |
| `current_runtime` | 168/200 | 504.4 | 0 |
| `current_supergemma4_reasoning` | 168/200 | 793.4 | 0 |
| `current_gemma3_reasoning` | 165/200 | 1056.7 | 0 |
| `current_gemma4_reasoning` | 165/200 | 8816.2 | 0 |

통합 세트에서는 reasoning assist가 실제로 켜진 문항이 0건이었다. 따라서 위 수치는 LLM 품질 비교가 아니라 맞춤법 보정, 조건 Transformer, 카드 근거 채점, 모델 로드 부하가 포함된 파이프라인 비교로 해석한다.

LLM 보조가 실제 켜지는 20문항 eval 비교:

| mode | pass | mean ms | reasoning assist | assist mean ms | 메모 |
|---|---:|---:|---:|---:|---|
| OFF | 20/20 | 489.6 | 0 | - | 기본값 유지 기준 |
| SuperGemma4 | 20/20 | 2463.7 | 4 | 9853.2 | 필요한 확인 메모를 비교적 짧게 반환 |
| Gemma3 | 20/20 | 4213.5 | 5 | 15333.7 | Metal memory 부족 경고 발생 |
| Gemma4 | 20/20 | 4477.3 | 4 | 18937.0 | 가장 느림 |

판단:

- MVP 기본값은 계속 `TOURISM_REASONING_ASSIST_ENABLED=false`로 둔다.
- LLM 보조를 실험적으로 켜야 한다면 현재 기본 Unsloth Gemma4 `think=false`를 우선 사용한다. 이 태그와 SuperGemma4 태그 모두 Ollama native `think=true`는 지원하지 않는다.
- Gemma3/Gemma4는 20문항 통과만으로 기본 전환하지 않는다. Gemma3는 메모리 경고가 있고, Gemma4는 지연이 너무 크다.
- 노이즈 현실형 세트에서는 `roberta_small_candidate`가 pass rate는 가장 높지만 평균 지연이 1초를 넘는다. 균형안은 `et5_roberta_combined`이며, 즉시 런타임 기본값 변경보다는 잔여 실패 28건의 근거 부족 bucket을 먼저 보강한다.
- medium/noisy 실패 대부분은 `card_missing_required_terms`, `card_count_low`라서 LLM 모델 교체보다 데이터 근거 보강과 조건별 카드 근거 개선의 우선순위가 높다.

## 운영 반영 원칙

- `OLLAMA_CHAT_MODEL` 기본값 변경은 20문항 eval과 이 벤치마크 결과를 같이 본 뒤 한다. 2026-06-07에는 응답 속도와 상담형 답변 품질 비교를 근거로 Unsloth Gemma4 E4B QAT를 기본값으로 바꿨다.
- native thinking이 가능해도 모든 질문에 켜지 않는다. 복합 조건 질문에서만 제한적으로 사용한다.
- thinking 출력은 사용자에게 그대로 노출하지 않는다. 응답에는 `reasoning_assist_used`, `reasoning_assist_notes` 같은 진단만 남긴다.
- 응답 시간이 길면 UI에는 로딩 상태를 명확히 보여준다.
