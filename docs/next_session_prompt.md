# Next Session Prompt

이 문서는 다음 Codex/Agent 세션에서 바로 이어서 작업하기 위한 시작 프롬프트다. 새 세션을 시작하면 이 문서를 먼저 읽고, 아래 순서대로 현재 상태를 확인한 뒤 작업을 계속한다.

## 시작 프롬프트

```text
이 저장소는 /Users/cheng80/Desktop/chatbot_rag 의 로컬 RAG 챗봇 프로젝트다.

먼저 AGENTS.md 와 docs/next_session_prompt.md 를 읽고, 아래 작업 순서를 기준으로 현재 상태를 확인해라. conda/Anaconda는 사용하지 않는다. Python은 프로젝트 루트의 .venv 를 사용한다.

작업을 시작하기 전에:
1. git status --short 로 변경 사항을 확인한다.
2. .venv/bin/python --version 으로 로컬 Python을 확인한다.
3. 필요한 경우 .venv/bin/python -m pytest 를 실행해 현재 테스트 상태를 본다.
4. README.md 와 docs/rag_chatbot_design.md 의 실행 순서를 기준으로 RAG 챗봇 작업을 이어간다.

로컬 VS Code 설정(.vscode/settings.json)은 git ignore 대상이다. 여기에 있는 python.defaultInterpreterPath 설정은 커밋 대상이 아니다.
```

## 프로젝트 요약

- 목표: ChatGPT/Gemini API 없이 FastAPI + ChromaDB + Ollama 기반 로컬 RAG 챗봇을 만든다.
- 답변 모델: `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M`
- 비교 모델: `gemma3:4b-it-q4_K_M`
- 임베딩 모델: `bge-m3`
- Vector DB: ChromaDB
- API: FastAPI
- 클라이언트 후보: Flutter, Jupyter Notebook requests 테스트

## 기본 작업 순서

1. 저장소 상태 확인

```bash
cd /Users/cheng80/Desktop/chatbot_rag
git status --short
```

2. Python 환경 확인

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
```

3. 의존성 확인 또는 설치

```bash
.venv/bin/python -m pip install -r requirements.txt
```

4. 테스트 실행

```bash
.venv/bin/python -m pytest
```

5. Ollama 모델 준비 확인

```bash
ollama list
```

필요 시:

```bash
ollama pull bge-m3
ollama pull gemma3:4b-it-q4_K_M
ollama run hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M
```

6. 문서 색인

```bash
.venv/bin/python scripts/ingest_all.py
```

임베딩 모델 변경 후에는 기존 벡터를 재사용하지 말고 재색인한다.

```bash
.venv/bin/python scripts/rebuild_index.py
```

7. 서버 실행

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

8. API 확인

```bash
curl http://localhost:8000/health
curl http://localhost:8000/documents/stats
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"환불은 언제까지 가능한가요?"}'
```

## 현재 로컬 환경 메모

- conda/Anaconda는 이 프로젝트에서 사용하지 않는다.
- `.venv`가 이미 존재하며, 확인 시점의 Python은 `3.13.7`이다.
- VS Code 오류 `Environment manager 'ms-python.python:conda' is not registered`는 `.vscode/settings.json`의 conda 환경 관리자 설정이 원인이었다.
- 현재 `.vscode/settings.json`은 다음처럼 `.venv`를 직접 보도록 정리했다.

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python-envs.pythonProjects": []
}
```

- `.vscode/`는 `.gitignore`에 포함되어 있으므로 위 설정은 로컬 전용이며 커밋에 포함되지 않는다.

## 주요 문서

- `README.md`: 실행 방법과 프로젝트 개요
- `docs/rag_chatbot_design.md`: RAG 구조, 폴더 역할, MVP 실행 순서
- `docs/remove_anaconda_mac_guide.md`: 다른 Mac에서 conda/Anaconda 정리할 때 참고
- `docs/관광 정보 탐색·상담형 챗봇 정리.md`: 도메인/기획 참고 문서

## 작업 원칙

- 기존 코드 구조를 먼저 읽고, 현재 패턴에 맞춰 작게 수정한다.
- `.env`와 로컬 설정은 커밋하지 않는다.
- `.vscode/settings.json`은 로컬 설정이므로 작업 히스토리 설명에는 포함할 수 있지만 커밋 대상처럼 다루지 않는다.
- 사용자가 구현을 요청하면 제안에서 멈추지 말고 가능한 범위에서 구현, 테스트, 결과 요약까지 진행한다.
