# Next Session Prompt

이 문서는 다음 Codex/Agent 세션에서 바로 이어서 작업하기 위한 시작 프롬프트다. 새 세션을 시작하면 이 문서를 먼저 읽고, 아래 순서대로 현재 상태를 확인한 뒤 작업을 계속한다.

## 시작 프롬프트

```text
이 저장소는 로컬 RAG 챗봇 프로젝트다. 모든 명령은 별도 표기가 없으면 프로젝트 루트에서 실행한다.

먼저 AGENTS.md 와 docs/project/next_session_prompt.md 를 읽고, 아래 작업 순서를 기준으로 현재 상태를 확인해라. conda/Anaconda는 사용하지 않는다. Python은 프로젝트 루트의 .venv 를 사용한다.

작업을 시작하기 전에:
1. git status --short 로 변경 사항을 확인한다.
2. .venv/bin/python --version 으로 로컬 Python을 확인한다.
3. 필요한 경우 .venv/bin/python -m pytest 를 실행해 현재 테스트 상태를 본다.
4. README.md 와 docs/rag/rag_chatbot_design.md 의 실행 순서를 기준으로 RAG 챗봇 작업을 이어간다.
5. 관광 MVP 작업은 docs/project/GOAL.md 와 docs/tourism/accessible_tourism_mvp_plan.md 의 최신 API 메모를 먼저 확인한다.

로컬 VS Code 설정(.vscode/settings.json)은 git ignore 대상이다. 여기에 있는 python.defaultInterpreterPath 설정은 커밋 대상이 아니다.
```

## 프로젝트 요약

- 목표: ChatGPT/Gemini API 없이 FastAPI + ChromaDB + Ollama 기반 로컬 RAG 챗봇을 만든다.
- 답변 모델: `hf.co/mradermacher/supergemma4-e4b-abliterated-i1-GGUF:Q4_K_M`
- 비교 모델: `gemma3:4b-it-q4_K_M`, `gemma4:e4b`, `qwen3:4b`, `huihui_ai/gemma-4-abliterated:e4b`
- 임베딩 모델: `bge-m3`
- Vector DB: ChromaDB
- API: FastAPI
- 클라이언트 후보: 웹 확인 UI 우선, Flutter는 후순위
- 평가셋: `data/eval/tourism_20_questions.jsonl`은 `/tourism/chat` 20문항 품질 평가 원본이다.
- 노트북: `notebooks/tourism_event_log_analysis.ipynb`는 `/tourism/chat` 이벤트 로그 분석용, `model_comparison_template.ipynb`는 20문항 eval/model comparison 보조용
- 모델 벤치마크: `scripts/benchmark_tourism_reasoning_models.py`는 후보 카드 재랭킹과 Ollama native thinking 여부를 비교한다.

## 기본 작업 순서

1. 저장소 상태 확인

```bash
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
ollama pull gemma4:e4b
ollama pull qwen3:4b
# 선택: 사용자 제안 Gemma 4 abliterated 후보
ollama pull huihui_ai/gemma-4-abliterated:e4b
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

서버류 실행 원칙:

- `uvicorn`, `cloudflared`, `python3 -m http.server` 같은 장시간 실행 프로세스는 Codex 백그라운드 세션으로 조용히 띄우지 않는다.
- 에디터의 새 터미널을 열고 사용자가 로그와 종료 상태를 볼 수 있게 실행한다.
- FastAPI 서버와 Cloudflare 터널은 서로 다른 터미널에서 실행한다.

FastAPI와 Cloudflare는 같은 명령이 아니다. 외부 확인이 필요하면 터미널을 2개 연다.

터미널 1: FastAPI 서버

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

오늘처럼 TourAPI 호출을 더 쓰지 않을 때는 fallback-only로 실행한다.

```bash
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

터미널 2: Cloudflare Quick Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8000
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
- 관광 API는 `.env`의 `TOUR_API_BASE_URL=https://apis.data.go.kr/B551011/KorService2`를 기본 목록/검색/공통 상세 조회에 사용한다.
- `KorService2`를 코드에서 `KorWithService2`로 강제 치환하지 않는다.
- 무장애 상세 조회는 별도 `TOUR_API_ACCESSIBLE_BASE_URL=https://apis.data.go.kr/B551011/KorWithService2`를 사용한다.
- `.env`에는 `TOUR_API_SERVICE_KEY`와 `TOUR_API_ACCESSIBLE_SERVICE_KEY`가 있다. 현재는 같은 인증키지만 서비스별 분리를 위해 둘 다 유지한다.
- 2026-05-15 재테스트 결과 `areaCode2`, `searchKeyword2`, `areaBasedList2`는 200 OK였다. 단, `areaBasedList2`에 `listYN=Y`를 넣으면 `INVALID_REQUEST_PARAMETER_ERROR(listYN)`가 발생하므로 넣지 않는다.
- 공공데이터포털 화면에서 `한국관광공사_무장애 여행 정보` 개발계정 승인은 확인됐다.
- 승인 반영 후 `KorWithService2/areaCode2`, `KorWithService2/detailWithTour2`, `KorWithService2/areaBasedList2` 호출이 200 OK로 확인됐다.
- 전국 시군구 코드는 수동 하드코딩하지 않는다. `scripts/fetch_tour_area_codes.py`로 `data/processed/tour_area_codes.json` 캐시를 만들고 `TourismQueryService`가 이 캐시를 우선 사용한다. 중복되는 시군구 별칭은 캐시에 넣지 않는다.
- 지역 추천 정책은 다음과 같다. 사용자가 시군구를 명시하면 해당 시군구 결과만 먼저 제공한다. 결과가 3개 미만이어도 자동으로 다른 구/군을 섞지 않고 부족 안내를 한다. 사용자가 `근처`, `주변`, `가까운`, `인근` 같은 확장 의도를 말한 경우에만 상위 광역 지역 후보를 함께 포함하고 답변에 확장 사실을 명시한다. 기본 추천은 최대 5장이다. 후보가 5장보다 많으면 `suggested_messages`에 `더 보기` 후속 질문을 넣고, 사용자가 `더 보기`, `전체`, `전부`, `20곳` 같은 의도를 말하면 확인된 후보를 가능한 만큼 반환한다.
- 다음 세션에서 지역 코드가 이상하면 아래 캐시 재생성부터 실행한다.

```bash
.venv/bin/python scripts/fetch_tour_area_codes.py
```

- `/tourism/chat`은 지역이 확정되면 이전 live 조회 Markdown 캐시를 먼저 확인한다. live 캐시에 없으면 Chroma 색인과 로컬 Markdown fallback을 확인한다. 그래도 같은 지역 카드가 없고 API 키가 있으면 live TourAPI 후보 조회를 사용한다. 같은 지역 반복 요청은 프로세스 메모리 캐시와 `data/generated/tour_api/live_markdown/` Markdown 캐시를 사용한다. `data/raw/tourism_accessible/`는 계획 수집한 fallback/색인 후보로 유지한다.
- `/tourism-ui/`는 정적 HTML/CSS/JS 기반 메신저형 시연 UI다. 디자인 기준은 `docs/design/tourism_chatbot_DESIGN.md`에 있다. 카드 위 긴 답변은 기본 접힘 처리하고, 카드에는 `상세 정보` 펼침과 장소명/주소 기반 `지도 검색`을 제공한다.
- 한국관광공사 열린관광 사이트의 상세 URL은 콘텐츠 ID만으로 안정적인 공개 상세 링크를 만들 수 없어 `access.visitkorea.or.kr/detail/...` 추정 링크 생성을 중단했다. 기존 캐시/색인에 남아 있는 해당 링크도 UI에서 숨기고 출처명만 표시한다.
- `/tourism/chat` 응답 이벤트는 `data/generated/tour_api/query_card_events.jsonl`에 JSONL로 저장한다. 기본값은 원문 질문을 저장하지 않고 `message_hash`만 저장한다. 필요할 때만 `TOURISM_QUERY_EVENT_LOG_INCLUDE_MESSAGE=true`로 원문 저장을 켠다.
- `/tourism/chat`의 LLM 추론 보조는 기본값이 꺼져 있다. 복합 상황 질문 품질 비교나 실험이 필요할 때만 `TOURISM_REASONING_ASSIST_ENABLED=true`로 켠다. 응답과 이벤트 로그의 `reasoning_assist_used`, `reasoning_assist_notes`로 사용 여부와 확인 필요 메모를 확인한다.
- 추론 보조를 끈 기본 모드에서 질문 의도 파악이 달라지는지 확인하려면 같은 eval을 ON/OFF로 실행해 `lookup_mode`, 카드 수, 카드 ID 순서, `warnings`, `suggested_messages`를 비교한다.
- 2026-05-15 로컬 모델 추론 보조 벤치마크를 실행했다. 결과 요약은 `docs/tourism/tourism_model_reasoning_benchmark.md`에 있다. 현재 결론은 MVP 기본 추론 보조는 OFF이며, 켜더라도 native `think=false`로만 실험하는 것이다. `gemma4:e4b`와 `huihui_ai/gemma-4-abliterated:e4b`는 native thinking이 동작하지만 30초 이상 지연됐고, `qwen3:4b`는 현재 프롬프트에서 JSON/한국어 계약을 지키지 못했다.
- 생성된 모델 벤치마크 원본은 `data/generated/tour_api/model_benchmarks/` 아래에 있으며 git ignore 대상이다. 필요하면 `scripts/benchmark_tourism_reasoning_models.py`로 다시 만든다.
- 개발/QA 기본 모드는 `cache/fallback-first + live-on-miss`이다. 호출량 또는 시연장 네트워크가 불안하면 `TOURISM_LIVE_LOOKUP_ENABLED=false`로 끄고 fallback-only로 운영한다. 장기 신선도는 Post-MVP 주기적 갱신 배치로 해결한다.
- offline-index 우선 방식과 cache/fallback-first + live-on-miss 방식의 차이, 장단점, 되돌림 기준은 `docs/tourism/tourism_response_strategy_decision.md`를 먼저 확인한다.
- 2026-05-15 수집은 중단했다. 추가 수집 전에는 `docs/tourism/tourism_data_collection_plan.md`의 호출량 메모와 내일 이어갈 때 섹션을 먼저 확인한다.
- fallback 데이터는 `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 배치 수집과 시군구 fallback 확장 수집을 진행했다. 중복 콘텐츠ID 정리 후 `data/raw/tourism_accessible` 기준 808개 Markdown, Chroma 기준 809개 문서/816개 청크가 색인됐다.
- 시군구 fallback은 TourAPI 지역 코드 234개 중 228개 시군구가 3장 이상 확보됐다. 0장 지역은 청원군, 마산시, 진해시, 남제주군, 북제주군이고, 3장 미만 지역은 계룡시 1장이다. 0장 5개 지역은 폐지/통합 지명으로 보고 사용자 질문에서는 현재 행정구역명을 안내한다. 매핑은 청원군 -> 청주시, 마산시 -> 창원시, 진해시 -> 창원시 진해구 안내/TourAPI 창원시 기준, 남제주군 -> 서귀포시, 북제주군 -> 제주시다. 전국 실사용 지역 250개 기준 대상 목록 확장은 아직 남아 있다.
- 2026-05-15에는 사용자의 명시 승인으로 엔드포인트별 500건 평시 안전치를 일시적으로 풀고 1,000건 기준까지 수집을 확장했으나, `detailCommon2` 429 응답 후 즉시 중단했다. 같은 quota window에서는 추가 수집하지 않는다.
- 20문항 fallback-only eval은 2026-05-15에 1차 실행했다. 20문항은 smoke test 수준이므로 다음에는 `docs/project/demo_capture_scenarios.md`와 확장 eval을 함께 live-on-miss/fallback-only로 비교한다.
- 서버 없이 현재 코드 기준 eval을 빠르게 확인할 때는 `TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python scripts/eval_tourism_chat.py --direct`를 사용한다.
- 전국 시군구 단위 fallback을 늘릴 경우 예상 규모와 호출량은 `docs/tourism/tourism_sigungu_fallback_scale.md`를 참고한다.
- 행정동/법정동 지역명 매칭 데이터는 `scripts/build_admin_region_aliases.py`로 생성했다. 결과는 `data/processed/admin_region_aliases.json`이고, 설계 기록은 `docs/tourism/admin_region_aliases.md`에 있다. `TourismQueryService`는 이 파일을 읽어 `부산 중구`, `해운대 좌동`, `창원 마산합포구`, `성남 분당구` 같은 예외 입력을 시군구 후보로 해석한다.
- 2026-05-15 스모크 결과 `서울 강남구에서 휠체어 관광지 추천해줘`는 강남구 결과 2건과 부족 안내를 반환했고, `서울 강남구 근처에서 휠체어 관광지 추천해줘`는 서울 범위 확장 안내와 함께 5건을 반환했다.
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

- `docs/README.md`: 문서 폴더 구조와 먼저 볼 문서 인덱스
- `docs/project/professor_review_brief.md`: 교수님/외부 검토자에게 보여줄 단일 검토 브리프
- `README.md`: 실행 방법과 프로젝트 개요
- `docs/rag/rag_chatbot_design.md`: RAG 구조, 폴더 역할, MVP 실행 순서
- `docs/setup/remove_anaconda_mac_guide.md`: 다른 Mac에서 conda/Anaconda 정리할 때 참고
- `docs/tourism/관광 정보 탐색·상담형 챗봇 정리.md`: 도메인/기획 참고 문서
- `docs/project/GOAL.md`: 현재 관광 MVP 목표와 API 판정 기준
- `docs/project/demo_capture_scenarios.md`: 발표용 캡처와 시연 질문 시나리오
- `docs/tourism/accessible_tourism_mvp_plan.md`: 무장애·가족 친화 관광 챗봇 구현 플랜
- `docs/tourism/tourism_eval_questions.md`: 20문항 관광 챗봇 평가셋 설명
- `docs/tourism/tourism_model_reasoning_benchmark.md`: 로컬 모델 추론 보조와 native thinking 비교 결과
- `docs/tourism/tourism_sample_quality.md`: fallback Markdown 샘플 품질 감사 방법
- `docs/references/개방데이터_활용매뉴얼(국문)/`: 국문 관광정보 서비스_GW 매뉴얼
- `docs/references/개방데이터_활용매뉴얼(무장애여행)/`: 무장애 여행 정보 매뉴얼

## 작업 원칙

- 기존 코드 구조를 먼저 읽고, 현재 패턴에 맞춰 작게 수정한다.
- 코드, 문서, 예제 명령, 프롬프트에는 저장소 상대경로를 사용한다. `/Users/...`, `~/Desktop/...`, `/home/...`, 임시 로컬 경로처럼 특정 머신에 묶인 절대경로는 커밋하지 않는다.
- `.env`와 로컬 설정은 커밋하지 않는다.
- `.vscode/settings.json`은 로컬 설정이므로 작업 히스토리 설명에는 포함할 수 있지만 커밋 대상처럼 다루지 않는다.
- 커밋 메시지는 항상 한글로 작성하고, 변경 내용을 명확히 요약한다. 여러 영역을 함께 커밋할 때는 제목과 본문으로 API, 데이터, 테스트, 문서 변경을 구분해 적는다.
- 사용자가 구현을 요청하면 제안에서 멈추지 말고 가능한 범위에서 구현, 테스트, 결과 요약까지 진행한다.
