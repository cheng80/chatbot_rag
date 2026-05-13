# chatbot_rag

FastAPI + Chroma + Ollama 기반의 로컬 RAG 챗봇 코드 뼈대입니다.

이 프로젝트는 ChatGPT/Gemini API 없이 다음 구조로 동작합니다.

```text
사용자 질문
  ↓
Ollama 임베딩 모델로 질문 임베딩
  ↓
Chroma Vector DB에서 관련 문서 검색
  ↓
검색 결과를 프롬프트에 삽입
  ↓
Ollama 로컬 LLM으로 답변 생성
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

### Python 가상환경

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ollama 모델 준비

```bash
ollama pull qwen3:8b
ollama pull qwen3-embedding
```

`qwen3-embedding`이 로컬 환경에서 지원되지 않으면 `.env`의 `OLLAMA_EMBED_MODEL` 값을 `embeddinggemma` 또는 `nomic-embed-text`로 바꿔 사용할 수 있습니다.

## 3. 환경 변수

```bash
cp .env.example .env
```

주요 값:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen3:8b
OLLAMA_EMBED_MODEL=qwen3-embedding
CHROMA_PATH=./data/vector_store/chroma
CHROMA_COLLECTION=manual_documents
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
python scripts/ingest_all.py
```

기존 Vector DB를 비우고 다시 색인하려면:

```bash
python scripts/rebuild_index.py
```

## 6. API 서버 실행

```bash
uvicorn app.main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

## 7. 질문 테스트

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

## 9. 개발 순서

1. `data/raw/`에 문서 추가
2. `python scripts/ingest_all.py` 실행
3. `uvicorn app.main:app --reload` 실행
4. `/chat` API 호출
5. 검색 품질이 낮으면 `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K` 조정
6. 문서가 많아지면 reranker, hybrid search, 권한 필터링 추가

## 10. 참고 문서

- FastAPI Bigger Applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Chroma Persistent Client: https://docs.trychroma.com/docs/run-chroma/clients
- Chroma Python Client: https://docs.trychroma.com/reference/python/client
- Ollama API: https://docs.ollama.com/api
- Ollama Generate API: https://docs.ollama.com/api/generate
- Ollama Embed API: https://docs.ollama.com/api/embed
