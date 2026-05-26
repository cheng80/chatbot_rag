# AutoRAG 검색 최적화 실험 계획

마지막 갱신: 2026-05-27

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

AutoRAG 의존성은 Python 3.12 계열의 별도 venv에 설치한다. 메인 `.venv`에도 dry-run 기준 resolver 충돌은 없지만, AutoRAG는 provider 의존성이 넓고 운영 런타임이 아니므로 프로젝트 기본 환경에 섞지 않는다. Python 3.13에서는 AutoRAG 0.3.x의 `numpy==1.26.4`와 `voyageai` 의존성 조건이 충돌할 수 있다.

```bash
pyenv local 3.12.10
python -m venv data/generated/tour_api/autorag_venv
data/generated/tour_api/autorag_venv/bin/python -m pip install --upgrade pip
data/generated/tour_api/autorag_venv/bin/python -m pip install -r requirements-autorag.txt

data/generated/tour_api/autorag_venv/bin/python scripts/build_autorag_tourism_dataset.py
```

검증과 평가:

```bash
data/generated/tour_api/autorag_venv/bin/autorag validate \
  --config configs/autorag/tourism_bm25_smoke.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet

data/generated/tour_api/autorag_venv/bin/autorag validate \
  --config configs/autorag/tourism_retrieval.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet

data/generated/tour_api/autorag_venv/bin/autorag evaluate \
  --config configs/autorag/tourism_retrieval.yaml \
  --qa_data_path data/processed/autorag_tourism/qa.parquet \
  --corpus_data_path data/processed/autorag_tourism/corpus.parquet \
  --project_dir data/processed/autorag_tourism/trials
```

`semantic_retrieval`과 `hybrid_retrieval`은 이 프로젝트의 기본 임베딩 정책에 맞춰 Ollama `bge-m3` 임베딩을 사용한다. 따라서 OpenAI API 토큰 없이 진행할 수 있지만, full config 검증과 평가는 로컬 Ollama 서버와 `bge-m3` 모델이 준비된 상태에서 실행해야 한다.

`configs/autorag/tourism_bm25_smoke.yaml`은 키 없이 데이터셋과 AutoRAG 실행 가능 여부를 확인하는 스모크 테스트용이다. 최종 비교와 채택 판단에는 `configs/autorag/tourism_retrieval.yaml`을 사용한다.

2026-05-27 재검토:

- AutoRAG 파일은 되살린다. 되살린 파일은 `requirements-autorag.txt`, `configs/autorag/*`, `scripts/build_autorag_tourism_dataset.py`, 이 문서다.
- `pip install --dry-run 'AutoRAG>=0.3.17' 'pandas>=2.2.0' 'pyarrow>=15.0.0' 'kiwipiepy>=0.20.0'` 기준 메인 Python 3.12.10 환경에서 resolver 충돌은 없었다.
- 한국어 BM25 토크나이저 비교를 위해 `requirements-autorag.txt`에 `konlpy`, `JPype1`을 추가한다. `ko_okt`, `ko_kkma`는 JDK가 필요하다.
- 그래도 운영 의존성에는 넣지 않는다. AutoRAG는 retrieval-only 오프라인 실험 도구이며 `/tourism/chat` runtime runner로 붙이지 않는다.

2026-05-25 1차 실행에서는 Ollama `bge-m3` 모델을 내려받은 뒤 retrieval-only validate/evaluate를 완료했다. QA 80건 기준 `VectorDB + top_k=40`이 `retrieval_recall=0.9250`, `retrieval_ndcg=0.441883`, `retrieval_mrr=0.436346`으로 BM25와 Hybrid RRF보다 높았다.

이후 기본 `--max-eval-rows 80` 샘플 한계를 확인하고, raw 904건과 live markdown 96건을 합친 corpus 1,000건, QA 683건으로 재산출했다. 전체 BM25/RRF 포함 evaluate는 summary 생성 전 장시간 소요되어 중단했고, `configs/autorag/tourism_semantic_topk.yaml`로 semantic vector-only top-k 비교를 분리해 완료했다. 전체 683 QA 기준 결과는 다음과 같다.

| top_k | retrieval_recall | retrieval_ndcg | retrieval_mrr | retrieval_f1 | retrieval_precision | execution_time |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.631040 | 0.307923 | 0.436408 | 0.385635 | 0.303953 | 0.025287 |
| 10 | 0.714495 | 0.307728 | 0.447743 | 0.349462 | 0.247877 | 0.025850 |
| 20 | 0.836018 | 0.395639 | 0.456461 | 0.302117 | 0.192753 | 0.026287 |
| 40 | 0.915081 | 0.464107 | 0.459182 | 0.222108 | 0.129209 | 0.028321 |

AutoRAG는 `top_k=40`을 best로 선택했다. 다만 이 결과는 휴리스틱 `retrieval_gt` 기반 retrieval screening이므로 운영 이식은 BM25/RRF 추가가 아니라 기존 vector-only 후보 검색의 기본 `TOP_K`를 40으로 넓히고, `/tourism/chat` hard/noisy eval로 최종 카드 품질을 별도 검증하는 방식으로 한다.

2026-05-27 한국어 BM25 토크나이저 재실험:

블로그에서 언급한 `space`, `ko_kiwi`, `ko_okt`, `ko_kkma`를 우리 관광 corpus와 QA mapping으로 직접 비교했다. 실행 스크립트는 `scripts/benchmark_tourism_bm25_tokenizers.py`이고, 산출물은 `data/generated/tour_api/autorag_bm25_tokenizers/summary.md`다.

같은 corpus 1,010개, QA 192개, top-k 기준에서 `bge-m3` vector-only도 함께 재측정했다.

| top_k | method | hit_rate | recall | precision | mrr | ndcg |
|---:|---|---:|---:|---:|---:|---:|
| 5 | `vector_bge-m3` | 0.5938 | 0.1745 | 0.2792 | 0.3819 | 0.2773 |
| 5 | `ko_okt` | 0.4792 | 0.1120 | 0.1792 | 0.3049 | 0.1903 |
| 5 | `ko_kkma` | 0.4635 | 0.1042 | 0.1667 | 0.2612 | 0.1674 |
| 5 | `ko_kiwi` | 0.3906 | 0.0964 | 0.1542 | 0.2606 | 0.1645 |
| 5 | `space` | 0.0677 | 0.0163 | 0.0260 | 0.0353 | 0.0248 |
| 40 | `vector_bge-m3` | 0.8906 | 0.6276 | 0.1255 | 0.4052 | 0.4388 |
| 40 | `ko_kkma` | 0.8177 | 0.5072 | 0.1014 | 0.2937 | 0.3313 |
| 40 | `ko_okt` | 0.7865 | 0.3971 | 0.0794 | 0.3332 | 0.2906 |
| 40 | `ko_kiwi` | 0.7604 | 0.3743 | 0.0749 | 0.2834 | 0.2581 |
| 40 | `space` | 0.2031 | 0.1217 | 0.0243 | 0.0471 | 0.0714 |

해석:

- 현재 관광 corpus에서는 블로그와 동일하게 `space`는 한국어 BM25에 부적합하다.
- `ko_okt`는 top5/MRR에서 BM25 후보 중 가장 안정적이다. 사용자가 실제로 보는 상위 카드 품질을 보려면 `ko_okt`가 1순위 비교 대상이다.
- `ko_kkma`는 top20/top40 recall이 가장 높지만 corpus 토큰화가 약 44.6초로 `ko_okt` 약 4.5초보다 훨씬 느리다. runtime 후보가 아니라 offline recall 비교 후보로만 둔다.
- `ko_kiwi`는 가장 빠른 형태소 후보지만 이번 corpus에서는 `ko_okt`, `ko_kkma`보다 낮다.
- `bge-m3` vector-only가 모든 top-k에서 BM25보다 높다. 따라서 운영 검색은 계속 Chroma vector-only `top_k=40`을 유지한다.

적용 방침:

1. AutoRAG/BM25 오프라인 실험 후보에는 `space`, `ko_kiwi`, `ko_okt`, `ko_kkma`를 모두 둔다.
2. 운영 `/tourism/chat` 검색 엔진은 바꾸지 않는다.
3. BM25를 붙인다면 1차 후보는 `ko_okt`다. 단, vector-only보다 실제 chat 카드 품질이 높다는 증거가 나오기 전에는 이식하지 않는다.
4. `ko_kkma`는 느려서 기본 smoke나 CI 성격의 반복 실험에는 부적합하다.

## 비교 설정

`configs/autorag/tourism_retrieval.yaml`은 retrieval-only 실험으로 시작한다. `configs/autorag/tourism_semantic_topk.yaml`은 전체 QA 기준으로 vector-only `top_k`만 빠르게 재검증할 때 사용한다.

| 후보 | 설정 |
|---|---|
| BM25 | `bm25_tokenizer`: `space`, `ko_kiwi`, `ko_okt`, `ko_kkma` |
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
