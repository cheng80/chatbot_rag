# 무장애 관광 챗봇 진행도

마지막 갱신: 2026-05-15

이 문서는 `docs/project/GOAL.md`, `docs/tourism/accessible_tourism_mvp_plan.md`, `README.md`, `TODOS.md` 기준으로 현재 MVP 진행 상태를 빠르게 보기 위한 요약이다.
응답 전략 변경 이력은 `docs/tourism/tourism_response_strategy_decision.md`에 별도로 기록한다.

## 전체 진행도

```text
MVP 전체              [████████░░] 75%
Backend contract     [█████████░] 90%
Live API coverage    [███████░░░] 70%
Data/sample coverage [████████░░] 80%
Web demo UI          [███████░░░] 70%
Quality/eval         [███░░░░░░░] 30%
Production readiness [██░░░░░░░░] 20%
```

현재 상태는 **live 캐시/색인/fallback 우선 + live TourAPI on miss + 웹 확인 UI** 단계다.
공개 데모 품질로 올리려면 데이터 커버리지, 20문항 eval, UI QA가 남아 있다.

## 영역별 상태

| 영역 | 진행도 | 상태 | 근거 |
|---|---:|---|---|
| TourAPI 연결 | 85% | 동작 | `KorWithService2` live 후보 조회, 지역 코드 캐시, 호출 상한 확인 |
| live 후보 조회 | 70% | 동작 | 캐시/색인/fallback miss 때 TourAPI 후보와 접근성 상세를 카드화, 프로세스 캐시 사용 |
| 샘플 데이터 | 80% | fallback | 광역권별 약 20장 수준 Markdown fallback + curated fallback |
| RAG 색인 | 75% | fallback | live API 호출 전 Markdown 샘플을 Chroma에서 검색 |
| `/tourism/chat` API | 92% | 안정화 | cache/fallback 우선, 안전한 오류, degraded fallback, 모호 지역 선택, 시군구 확장 정책 반영 |
| 카드 응답 schema | 85% | 동작 | `TourismPlaceCard[]`, `sources`, `warnings`, `suggested_messages` 반환 |
| 웹 확인 UI | 70% | 시연 가능 | `/tourism-ui/`, 지역 버튼, 자유 입력, Help, Swagger 링크, 터널 확인 |
| 테스트 | 75% | 주요 회귀 커버 | `pytest` 33개 통과, backend 정책 중심 |
| 모델 품질 평가 | 30% | 미완 | 20문항 eval/model comparison TODO |
| 운영/배포 | 20% | 임시 확인 | Cloudflare Quick Tunnel로 외부 임시 확인 가능, 정식 배포 아님 |

## 완료된 핵심 항목

- 한국관광공사 무장애 여행 정보 OpenAPI 호출 확인
- cache/fallback miss 때 live TourAPI 후보 조회를 사용하는 경로 추가
- 같은 지역 반복 요청을 줄이는 프로세스 메모리 캐시 추가
- mvp/fallback-1/fallback-2/fallback-3 분할 수집 완료
- `data/raw/tourism_accessible` 기준 366개 Markdown fallback 확보
- 지역 코드 캐시 생성 및 누락/손상 진단
- `/tourism/chat` endpoint 추가
- 관광 카드 Markdown codec 공유화
- Retriever 실패 시 local sample fallback과 `degraded/warnings` 노출
- 시군구 자동 확장 금지 정책 반영
- `근처/주변/가까운/인근` 명시 시 상위 지역 확장
- `중구` 같은 동명이 시군구는 지역 선택 후보 반환
- 관계 호칭만으로 나이 추정하지 않음
- 정적 웹 UI `/tourism-ui/` 추가
- Cloudflare Quick Tunnel 외부 확인 흐름 문서화
- Swagger/ReDoc/OpenAPI JSON 링크를 UI에 노출

## 남은 큰 작업

| 우선순위 | 작업 | 이유 | 현재 위치 |
|---|---|---|---|
| P1 | live 조회 QA | 실제 질문별 호출량, 쿼터, 응답 속도 확인 필요 | `/tourism/chat` |
| P1 | fallback 데이터 QA | 지역별 최소 샘플은 확보됐고 실제 질문 품질 확인 필요 | `data/raw/tourism_accessible/` |
| P1 | 웹 UI QA | 모바일/외부 사용자 관점에서 카드 가독성, Help, 오류 상태 확인 필요 | `frontend/web/` |
| P1 | 20문항 eval 작성 | 답변 품질을 감이 아니라 반복 측정으로 봐야 함 | `TODOS.md` |
| P2 | `supergemma4` vs `gemma3` 비교 | 기본 로컬 모델 선택 근거 확보 | `README.md` 모델 비교 섹션 |
| P2 | persistent TourAPI cache 검토 | 프로세스 재시작 후에도 반복 호출을 줄이기 위함 | `TODOS.md` |
| P3 | Flutter 전환 여부 결정 | 웹 UI로 충분한지, 모바일 앱이 필요한지 판단 | `frontend/flutter_client/README.md` |

## 다음 체크포인트

1. `/tourism-ui/`를 외부 터널 URL로 열어 사용자 흐름을 직접 테스트한다.
2. 서울/부산/강릉 외 지역 질문에서 live 조회 결과와 fallback 메시지를 수집한다.
3. fallback Markdown 카드 품질을 지역별로 샘플링한다.
4. 최소 20개 질문 eval set을 만든다.
5. 2026-06-10 전까지 기본 서비스 고정, 문서, 데모 스크립트, 최종 회귀 테스트를 끝낸다.

앱/Flutter 구현은 기본 서비스 완료 뒤로 미룬다.

## 빠른 확인 명령

장시간 실행 서버는 Codex 백그라운드 세션으로 조용히 띄우지 않는다. 에디터의 새 터미널에서 실행해 로그와 종료 상태를 직접 확인한다.

FastAPI와 Cloudflare는 같은 명령이 아니다. 외부 확인이 필요하면 터미널을 2개 연다.

터미널 1: FastAPI 서버

오늘처럼 TourAPI 호출을 더 쓰지 않을 때는 fallback-only로 실행한다.

```bash
cd /Users/cheng80/Desktop/chatbot_rag
.venv/bin/python -m pytest -q
TOURISM_LIVE_LOOKUP_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

외부 확인 URL 형식:

```text
https://...trycloudflare.com/tourism-ui/
```

터미널 2: Cloudflare Quick Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```
