# chatbot_rag

FastAPI + ChromaDB + Ollama 기반의 로컬 RAG 챗봇 코드 뼈대입니다.

이 프로젝트는 ChatGPT/Gemini API 없이 다음 구조로 동작합니다.

```text
사용자 질문
  ↓
Ollama bge-m3 임베딩 모델로 질문 임베딩
  ↓
ChromaDB Vector DB에서 관련 문서 검색
  ↓
검색 결과를 프롬프트에 삽입
  ↓
Ollama supergemma4-e4b-abliterated Q4_K_M 로컬 LLM으로 답변 생성
  ↓
답변 + 출처 반환
```

## 1. 폴더 구조

```text
chatbot_rag/
├─ app/
│  ├─ main.py
│  ├─ core/
│  ├─ api/
│  │  └─ routes/
│  ├─ schemas/
│  ├─ services/
│  ├─ repositories/
│  └─ utils/
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ vector_store/
├─ docs/
├─ ingestion/
├─ prompts/
├─ scripts/
├─ tests/
├─ .env.example
├─ requirements.txt
└─ docker-compose.yml
```

## 2. 준비

다른 Mac에서 Anaconda/conda 설정을 걷어내고 Python 환경을 최소화해야 하면 [Mac Anaconda 제거 및 Python 환경 최소화 가이드](docs/remove_anaconda_mac_guide.md)를 먼저 참고한다.

### 프로젝트 진입

```bash
cd /Users/cheng80/Desktop/chatbot_rag
```

### Python 가상환경

현재 Mac 환경은 Anaconda를 사용하지 않는다. 프로젝트에 `.venv`가 없으면 새로 만들고, 있으면 활성화만 한다.

Mac:

```bash
cd /Users/cheng80/Desktop/chatbot_rag

# 최초 1회: 이 프로젝트에서 사용할 pyenv Python 지정
pyenv local 3.13.7

# 최초 1회 또는 .venv를 다시 만들 때
python -m venv .venv

# 매번 프로젝트 작업을 시작할 때
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

pyenv `3.13.7`이 없으면 Homebrew 또는 시스템 Python으로 만들 수 있다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Ollama 모델 준비

```bash
ollama run hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
ollama pull gemma3:4b-it-q4_K_M
ollama pull bge-m3
```

`supergemma4-e4b-abliterated`는 한국어 답변 품질 실험을 위한 1차 후보이고, `gemma3:4b-it-q4_K_M`는 비교 기준선으로 사용한다.
`bge-m3`가 로컬 환경에서 지원되지 않으면 `.env`의 `OLLAMA_EMBED_MODEL` 값을 다른 Ollama 임베딩 모델로 바꿔 사용할 수 있습니다.

## 3. 환경 변수

```bash
cp .env.example .env
```

주요 값:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
OLLAMA_EMBED_MODEL=bge-m3
CHROMA_PATH=./data/vector_store/chroma
CHROMA_COLLECTION=manual_documents
DATABASE_URL=sqlite:///./data/app.sqlite3
RAW_DATA_PATH=./data/raw
TOP_K=5
```

## 4. 문서 넣기

`data/raw/` 아래에 문서를 넣습니다.

지원 형식:

```text
.pdf
.txt
.md
```

예:

```text
data/raw/product_manual.pdf
data/raw/faq.md
data/raw/install_guide.txt
```

## 5. 문서 색인

```bash
source .venv/bin/activate
python scripts/ingest_all.py
```

기존 Vector DB를 비우고 다시 색인하려면:

```bash
source .venv/bin/activate
python scripts/rebuild_index.py
```

임베딩 모델을 바꾼 뒤에는 기존 벡터와 차원이 달라질 수 있으므로 `python scripts/rebuild_index.py`로 다시 색인한다.

## 6. API 서버 실행

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

## 7. 질문 테스트

기본 테스트는 Jupyter Notebook에서 Python `requests`로 `/chat`, `/health`, `/documents/stats` API를 호출해 확인한다. 빠른 확인이 필요하면 아래 `curl`도 사용할 수 있다.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"환불은 언제까지 가능한가요?"}'
```

응답 예:

```json
{
  "answer": "문서에 따르면 환불은 구매일로부터 7일 이내에 가능합니다.",
  "sources": [
    {
      "source": "example_faq.md",
      "page": null,
      "chunk_id": "...",
      "chunk_index": 0,
      "distance": 0.42
    }
  ]
}
```

## 8. 주요 API

| Method | Path | 설명 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| POST | `/chat` | RAG 질문 답변 |
| POST | `/documents/reindex` | `data/raw/` 문서 재색인 |
| GET | `/documents/stats` | Chroma collection 상태 |

## 9. 기준 스택

| 역할 | 선택 |
|---|---|
| LLM 실행 | Ollama + `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M` |
| 비교 기준선 | `gemma3:4b-it-q4_K_M` |
| 임베딩 | bge-m3 |
| RAG / Vector DB | ChromaDB |
| 일반 DB | SQLite |
| 외부 접속 | Cloudflare Tunnel 또는 ngrok |
| 프론트 테스트 | Flutter 앱 |
| API 테스트 | Jupyter Notebook의 Python requests |

## 10. 개발 순서

1. `data/raw/`에 문서 추가
2. `source .venv/bin/activate`로 프로젝트 가상환경 진입
3. `python scripts/ingest_all.py` 실행
4. `python -m uvicorn app.main:app --reload` 실행
5. Jupyter Notebook 또는 Flutter 앱에서 `/chat` API 호출
6. 검색 품질이 낮으면 `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K` 조정
7. 문서가 많아지면 reranker, hybrid search, 권한 필터링 추가

## 11. 모델 비교 실험 순서

비교 대상은 `supergemma4-e4b-abliterated Q4_K_M`와 `gemma3:4b-it-q4_K_M` 두 개로 제한한다. 임베딩은 `bge-m3`로 고정해 LLM 답변 품질만 비교한다.

1. 모델 준비

```bash
ollama run hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
ollama pull gemma3:4b-it-q4_K_M
ollama pull bge-m3
```

2. 같은 문서와 같은 ChromaDB 인덱스를 사용한다.

```bash
source .venv/bin/activate
python scripts/rebuild_index.py
```

3. `.env`의 `OLLAMA_CHAT_MODEL`만 바꿔가며 서버를 재시작한다.

```env
OLLAMA_CHAT_MODEL=hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
```

```env
OLLAMA_CHAT_MODEL=gemma3:4b-it-q4_K_M
```

4. `notebooks/model_comparison_template.ipynb`에서 같은 질문 세트를 실행한다. 단일 API 확인은 `notebooks/api_test.ipynb`를 사용한다.

5. 각 응답을 아래 기준으로 1~5점 평가한다.

| 평가 항목 | 기준 |
|---|---|
| 한국어 자연스러움 | 문장이 어색하지 않고 상담형 톤을 유지하는가 |
| 근거 준수 | 검색된 문서와 출처 범위 안에서 답하는가 |
| 모름 처리 | 근거가 없을 때 추측하지 않는가 |
| 관광 상담 적합성 | 여행 조건, 지역, 동행자 맥락을 잘 반영하는가 |
| 응답 속도 | `/chat` 전체 응답 시간이 실사용 가능한가 |

6. 채택 기준은 품질 우선이다. `supergemma4`가 한국어와 상담 품질에서 확실히 앞서고, 환각이 늘지 않으면 메인 모델로 유지한다. 환각이나 지시 불이행이 늘면 `gemma3:4b-it-q4_K_M` 또는 공식 `gemma4:4b-q4_K_M`를 기준선으로 되돌린다.

## 12. 참고 문서

- FastAPI Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Chroma Persistent Client: https://docs.trychroma.com/docs/run-chroma/clients
- Chroma Python Client: https://docs.trychroma.com/reference/python/client
- Ollama API: https://docs.ollama.com/api
- Ollama Generate API: https://docs.ollama.com/api/generate
- Ollama Embed API: https://docs.ollama.com/api/embed
