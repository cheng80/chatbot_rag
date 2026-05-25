# AutoRAG 검색 최적화 실험 계획

마지막 갱신: 2026-05-25

## 목적

현재 `/tourism/chat`의 지역, 조건, 후속질문, 제외 조건, 범위 밖 질문 처리 로직은 유지한다. AutoRAG는 운영 엔진으로 붙이지 않고, 관광 Markdown 후보 검색 방식만 비교하는 오프라인 실험 도구로 사용한다.

AutoRAG 공식 흐름은 parsing, chunking, QA creation, retrieval, reranker, prompt maker, generator까지 포함해 전체 RAG 파이프라인을 최적화할 수 있다. 이 프로젝트에서는 그 전체 절차를 운영 파이프라인으로 채택하지 않는다. 이미 `/tourism/chat` 안에 정책 기반 응답 로직과 live TourAPI fallback이 있으므로, AutoRAG는 `retrieval-only` 후보 검색 실험에 한정한다.

비교하려는 질문은 하나다.

```text
관광 fallback/live Markdown 후보를 찾을 때
Chroma vector only, BM25, BM25+Vector RRF 중 무엇이 더 안정적인가?
```

## 입력 데이터

`scripts/build_autorag_tourism_dataset.py`는 다음 입력을 AutoRAG 형식으로 변환한다.

| 입력 | 역할 |
|---|---|
| `data/raw/tourism_accessible/*.md` | 기본 관광 카드 corpus |
| `data/generated/tour_api/live_markdown/*.md` | 로컬에 있을 때만 추가되는 live cache corpus |
| `data/eval/tourism_20_questions.jsonl` | 1차 QA seed |
| `data/eval/tourism_noisy_realistic_chat_eval_v1_200.jsonl` | noisy/hard 일부 QA seed |

출력은 기본적으로 `data/processed/autorag_tourism/` 아래에 만든다.

| 출력 | AutoRAG 요구 컬럼 |
|---|---|
| `corpus.parquet` | `doc_id`, `contents`, `metadata` |
| `qa.parquet` | `qid`, `query`, `retrieval_gt`, `generation_gt` |
| `summary.json` | 변환 행 수와 주의 메모 |

`retrieval_gt`는 현재 스크립트에서 지역명과 접근성 조건 키워드로 휴리스틱 매핑한다. 따라서 첫 결과는 최종 품질 점수가 아니라 검색 후보군을 좁히는 스크리닝 신호로만 본다. 중요한 질문군은 수동 검수한 `retrieval_gt`로 보강한 뒤 최종 비교한다.

## 실행 순서

AutoRAG 의존성은 Python 3.12 계열에서 설치한다. 2026-05-25 기준 이 프로젝트의 `.venv`는 Python 3.12.10으로 맞췄다. Python 3.13에서는 AutoRAG 0.3.x의 `numpy==1.26.4`와 `voyageai` 의존성 조건이 충돌할 수 있다.

```bash
pyenv local 3.12.10
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-autorag.txt

.venv/bin/python scripts/build_autorag_tourism_dataset.py
```

검증과 평가:

```bash
.venv/bin/autorag validate \
  --config configs/autorag/tourism_bm25_smoke.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet

.venv/bin/autorag validate \
  --config configs/autorag/tourism_retrieval.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet

.venv/bin/autorag evaluate \
  --config configs/autorag/tourism_retrieval.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet \
  --project_dir data/processed/autorag_tourism/trials
```

`semantic_retrieval`과 `hybrid_retrieval`은 이 프로젝트의 기본 임베딩 정책에 맞춰 Ollama `bge-m3` 임베딩을 사용한다. 따라서 OpenAI API 토큰 없이 진행할 수 있지만, full config 검증과 평가는 로컬 Ollama 서버와 `bge-m3` 모델이 준비된 상태에서 실행해야 한다.

`configs/autorag/tourism_bm25_smoke.yaml`은 키 없이 데이터셋과 AutoRAG 실행 가능 여부를 확인하는 스모크 테스트용이다. 최종 비교와 채택 판단에는 `configs/autorag/tourism_retrieval.yaml`을 사용한다.

2026-05-25 1차 실행에서는 Ollama `bge-m3` 모델을 내려받은 뒤 retrieval-only validate/evaluate를 완료했다. QA 80건 기준 `VectorDB + top_k=40`이 `retrieval_recall=0.9250`, `retrieval_ndcg=0.441883`, `retrieval_mrr=0.436346`으로 BM25와 Hybrid RRF보다 높았다.

이후 기본 `--max-eval-rows 80` 샘플 한계를 확인하고, raw 904건과 live markdown 96건을 합친 corpus 1,000건, QA 683건으로 재산출했다. 전체 BM25/RRF 포함 evaluate는 summary 생성 전 장시간 소요되어 중단했고, `configs/autorag/tourism_semantic_topk.yaml`로 semantic vector-only top-k 비교를 분리해 완료했다. 전체 683 QA 기준 결과는 다음과 같다.

| top_k | retrieval_recall | retrieval_ndcg | retrieval_mrr | retrieval_f1 | retrieval_precision | execution_time |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.631040 | 0.307923 | 0.436408 | 0.385635 | 0.303953 | 0.025287 |
| 10 | 0.714495 | 0.307728 | 0.447743 | 0.349462 | 0.247877 | 0.025850 |
| 20 | 0.836018 | 0.395639 | 0.456461 | 0.302117 | 0.192753 | 0.026287 |
| 40 | 0.915081 | 0.464107 | 0.459182 | 0.222108 | 0.129209 | 0.028321 |

AutoRAG는 `top_k=40`을 best로 선택했다. 다만 이 결과는 휴리스틱 `retrieval_gt` 기반 retrieval screening이므로 운영 이식은 BM25/RRF 추가가 아니라 기존 vector-only 후보 검색의 기본 `TOP_K`를 40으로 넓히고, `/tourism/chat` hard/noisy eval로 최종 카드 품질을 별도 검증하는 방식으로 한다.

## 비교 설정

`configs/autorag/tourism_retrieval.yaml`은 retrieval-only 실험으로 시작한다. `configs/autorag/tourism_semantic_topk.yaml`은 전체 QA 기준으로 vector-only `top_k`만 빠르게 재검증할 때 사용한다.

| 후보 | 설정 |
|---|---|
| BM25 | `bm25_tokenizer`: `space`, `ko_kiwi` |
| VectorDB | AutoRAG Chroma vector retrieval + Ollama `bge-m3` |
| Hybrid RRF | BM25와 vector 후보의 Reciprocal Rank Fusion |
| top-k | 5, 10, 20, 40 |

reranker는 1차 retrieval 결과에서 유의미한 차이가 보인 뒤 별도 실험으로 분리한다. 로컬 MVP에서는 지연시간과 모델 의존성 부담이 크므로 기본 실험에 섞지 않는다.

## 채택 기준

AutoRAG `summary.csv`만으로 런타임을 바꾸지 않는다. 다음 조건을 모두 만족해야 `/tourism/chat` 검색 단계에 이식한다.

1. `retrieval_recall` 또는 `retrieval_mrr`이 현재 vector-only 기준보다 명확히 좋다.
2. 평균 속도가 `/tourism/chat` 사용자 응답을 악화시키지 않는다.
3. `tests/test_tourism_chat_service.py`, `tests/test_tourism_query_service.py`에서 회귀가 없다.
4. hard/noisy chat eval에서 카드 품질이 떨어지지 않는다.
5. 지역/조건/후속질문/unsupported 처리 로직을 AutoRAG runner로 대체하지 않는다.
