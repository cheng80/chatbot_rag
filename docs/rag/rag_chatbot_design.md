# RAG 챗봇 설계 문서

## 1. 목표

Gemini나 ChatGPT API 없이, 로컬 모델과 Vector DB를 사용해 문서 기반 RAG 챗봇을 만든다.

핵심 목표는 다음과 같다.

```text
- 사내 문서, 매뉴얼, FAQ, PDF를 기반으로 답변한다.
- 문서에 없는 내용은 추측하지 않는다.
- 답변과 함께 출처를 반환한다.
- FastAPI 서버로 구성해 Flutter 클라이언트와 Python 기반 Jupyter Notebook 테스트에서 호출할 수 있게 한다.
```

## 2. RAG 기본 구조

```text
사용자 질문
  ↓
질문 임베딩
  ↓
Vector DB에서 관련 문서 검색
  ↓
검색 결과를 프롬프트에 삽입
  ↓
로컬 LLM이 답변 생성
  ↓
답변 + 출처 반환
```

RAG는 모델을 새로 학습시키는 방식이 아니라, 질문이 들어올 때 관련 문서를 검색해서 답변 생성을 보강하는 방식이다.

## 3. 기술 스택

| 역할 | 선택 |
|---|---|
| API 서버 | FastAPI |
| Vector DB | ChromaDB |
| LLM 실행 | Ollama |
| 답변 생성 모델 | `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` |
| 비교 기준선 | `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M`, `gemma3:4b-it-q4_K_M` |
| 임베딩 모델 | bge-m3 |
| 일반 DB | SQLite |
| 외부 접속 | Cloudflare Tunnel 또는 ngrok |
| 문서 파싱 | pypdf, txt, markdown |
| 클라이언트 | Flutter 앱 |
| 테스트 | Jupyter Notebook의 Python requests |

## 4. 프로젝트 구조

```text
chatbot_rag/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ docker-compose.yml
│
├─ data/
│  ├─ raw/
│  │  ├─ example_faq.md
│  │  ├─ pdf/
│  │  ├─ txt/
│  │  └─ md/
│  ├─ processed/
│  └─ vector_store/
│
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  └─ logging.py
│  ├─ api/
│  │  ├─ deps.py
│  │  └─ routes/
│  │     ├─ chat.py
│  │     ├─ documents.py
│  │     └─ health.py
│  ├─ schemas/
│  │  ├─ chat.py
│  │  └─ document.py
│  ├─ services/
│  │  ├─ document_loader.py
│  │  ├─ text_splitter.py
│  │  ├─ embedding_service.py
│  │  ├─ vector_store.py
│  │  ├─ retriever.py
│  │  ├─ prompt_builder.py
│  │  ├─ llm_service.py
│  │  ├─ rag_service.py
│  │  ├─ citation_service.py
│  │  └─ ingestion_service.py
│  └─ utils/
│     ├─ file_utils.py
│     └─ text_utils.py
│
├─ ingestion/
├─ prompts/
├─ scripts/
├─ tests/
└─ frontend/
```

## 5. 폴더별 역할

### `data/raw/`

원본 문서를 넣는 위치다. PDF, TXT, Markdown 파일을 여기에 넣는다.

### `data/processed/`

전처리 결과나 chunk 결과를 저장할 때 사용한다. 현재 코드 뼈대에서는 필수는 아니지만, 디버깅을 위해 남겨두었다.

### `data/vector_store/`

Chroma가 로컬 Vector DB 파일을 저장하는 위치다.

### `ingestion/`

문서를 읽고, 정제하고, chunk로 나누고, 임베딩해서 Vector DB에 넣는 작업을 담당한다.

### `app/services/`

RAG 핵심 로직이 들어간다.

```text
DocumentLoader       원본 문서 로딩
TextSplitter         chunk 분할
EmbeddingService     Ollama 임베딩 호출
VectorStore          Chroma 저장/검색
Retriever            질문 기반 문서 검색
PromptBuilder        검색 결과를 프롬프트로 구성
LLMService           Ollama 답변 생성 호출
RAGService           전체 흐름 조립
CitationService      출처 구성
IngestionService     문서 색인 흐름 조립
```

### `app/api/routes/`

FastAPI endpoint가 들어간다.

```text
/chat                사용자 질문 처리
/documents/reindex   문서 재색인
/documents/stats     collection 상태 확인
/health              서버 상태 확인
```

## 6. 문서 색인 흐름

```text
data/raw 문서 읽기
  ↓
PDF/TXT/MD 파싱
  ↓
텍스트 정제
  ↓
chunk 분할
  ↓
Ollama 임베딩 생성
  ↓
Chroma에 upsert
```

## 7. 질문 답변 흐름

```text
POST /chat
  ↓
질문 임베딩
  ↓
Chroma top-k 검색
  ↓
검색된 chunk를 프롬프트에 삽입
  ↓
Ollama /api/generate 호출
  ↓
답변 + sources 반환
```

## 8. 프롬프트 규칙

`prompts/rag_answer_prompt.txt`에는 다음 원칙이 들어간다.

```text
1. 검색된 문서 내용만 근거로 답변한다.
2. 문서에 없는 내용은 추측하지 않는다.
3. 모르면 제공된 문서에서 확인되지 않는다고 말한다.
4. 답변은 한국어로 한다.
5. 출처를 유지한다.
```

## 9. MVP 실행 순서

```bash
cp .env.example .env

# 최초 1회 또는 .venv를 다시 만들 때
pyenv local 3.12.10
python -m venv .venv

# 매번 프로젝트 작업을 시작할 때
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

ollama run hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL
ollama run hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
ollama pull gemma3:4b-it-q4_K_M
ollama pull bge-m3

python scripts/ingest_all.py
python -m uvicorn app.main:app --reload
```

임베딩 모델을 `bge-m3`로 바꾼 뒤에는 기존 ChromaDB 벡터를 그대로 쓰지 않고 `python scripts/rebuild_index.py`로 재색인한다.

venv 활성화 없이 명확히 실행하려면 다음처럼 프로젝트의 `.venv` Python을 직접 사용한다.

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/ingest_all.py
.venv/bin/python -m uvicorn app.main:app --reload
```

Anaconda는 사용하지 않는다. Python 경로가 헷갈리면 다음으로 확인한다.

```bash
which python
python --version
```

정상적으로 가상환경에 진입했다면 `which python`은 프로젝트의 `.venv/bin/python`을 가리킨다.

질문 테스트:

기본 테스트는 Jupyter Notebook에서 Python `requests`로 실행한다. 빠른 확인이 필요하면 아래 `curl`을 사용한다.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"환불은 언제까지 가능한가요?"}'
```

상태 확인:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/documents/stats
```

## 10. 현재 검증 상태

2026-05-13 기준으로 다음 항목을 확인했다.

```text
1. docs/rag/rag_chatbot_design.md 존재
2. requirements.txt 존재 및 의존성 포함
3. .env.example 존재
4. app/ FastAPI 코드 존재
5. prompts/ 프롬프트 파일 존재
6. scripts/ 실행 스크립트 존재
7. data/raw/example_faq.md 테스트 문서 존재
8. pytest 통과: 3 passed
9. Ollama 모델 준비 완료: unsloth gemma-4-E4B-it-qat UD-Q4_K_XL, supergemma4-e4b-abliterated Q4_K_M, gemma3:4b-it-q4_K_M, bge-m3
10. scripts/ingest_all.py 실행 성공
    - document_count: 1
    - chunk_count: 1
    - collection_name: manual_documents
11. python -m uvicorn app.main:app --reload 실행 및 /health 응답 확인
    - 응답: {"status":"ok"}
```

서버와 스크립트 실행은 `.venv` 활성화 후 `python -m ...` 형식을 쓰거나, `.venv/bin/python -m ...` 형식을 쓰면 가장 명확하다.

응답 속도 기준으로는 ChromaDB 검색보다 Ollama 답변 생성 시간이 대부분을 차지한다. 현재 기본 `unsloth/gemma-4-E4B-it-qat UD-Q4_K_XL` 사용 시 `LLM_NUM_PREDICT`로 최대 생성 토큰을 제한한다.

```text
embedding: 약 0.3초
vector_search: 약 0.02초
llm_generate: 약 3초
POST /chat 전체 응답: 약 2~3초
```

## 11. 다음 확장 방향

```text
1. PDF 업로드 API 추가
2. 사용자별 문서 권한 필터링
3. BM25 + Vector Search 하이브리드 검색
4. Reranker 추가
5. SQLite 기반 대화 히스토리 저장
6. Flutter 클라이언트 연결
7. Cloudflare Tunnel 또는 ngrok 외부 접속 구성
8. 운영용 Docker 구성 강화
9. Jupyter Notebook 기반 답변 품질 평가 자동화
```

## 12. 모델 비교 실험 계획

목표는 한국어 관광 상담형 RAG 답변에 적합한 LLM을 고르는 것이다. 임베딩 모델은 `bge-m3`로 고정하고, ChromaDB 인덱스도 동일하게 유지한다. 비교는 LLM 답변 생성 품질과 속도만 본다.

비교 모델:

| 구분 | 모델 |
|---|---|
| 1차 후보 | `hf.co/unsloth/gemma-4-E4B-it-qat-GGUF:UD-Q4_K_XL` |
| 이전 기준선 | `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` |
| 기준선 | `gemma3:4b-it-q4_K_M` |
| 예비 기준선 | `gemma4:4b-q4_K_M` |

실험 순서:

```text
1. Ollama 모델 2개와 bge-m3를 준비한다.
2. data/raw/ 문서를 확정한다.
3. bge-m3 기준으로 ChromaDB를 rebuild_index.py로 재색인한다.
4. OLLAMA_CHAT_MODEL을 1차 후보로 설정한다.
5. 서버를 재시작한다.
6. Jupyter Notebook에서 같은 질문 세트를 실행하고 응답, 출처, 응답 시간을 기록한다.
7. OLLAMA_CHAT_MODEL을 기준선 모델로 바꾼다.
8. 서버를 재시작한다.
9. 동일 질문 세트를 다시 실행한다.
10. 점수표로 비교해 메인 모델을 결정한다.
```

평가 질문 세트는 최소 20개로 구성한다.

```text
1. 근거가 문서에 있는 관광지 추천 질문
2. 지역, 동행자, 계절 조건이 포함된 복합 질문
3. 문서에 없는 정보를 묻는 질문
4. 출처를 요구하는 질문
5. 잘못된 전제를 포함한 질문
```

평가 기준:

| 항목 | 점수 기준 |
|---|---|
| 한국어 자연스러움 | 1=어색함, 5=상담형으로 자연스러움 |
| 근거 준수 | 1=근거 밖 추측, 5=검색 근거 안에서 답변 |
| 모름 처리 | 1=없는 내용을 지어냄, 5=확인 불가를 명확히 말함 |
| 관광 상담 적합성 | 1=일반 답변, 5=조건을 반영한 관광 상담 |
| 출처 유지 | 1=출처 누락, 5=출처와 답변 연결이 명확함 |
| 응답 속도 | 1=느림, 5=실사용 가능 |

## 13. 참고 문서

- FastAPI Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Chroma Clients: https://docs.trychroma.com/docs/run-chroma/clients
- Chroma Python Client: https://docs.trychroma.com/reference/python/client
- Ollama API: https://docs.ollama.com/api
- Ollama Generate API: https://docs.ollama.com/api/generate
- Ollama Embed API: https://docs.ollama.com/api/embed
