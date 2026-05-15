# 무장애 관광 챗봇 진행도

마지막 갱신: 2026-05-15

이 문서는 `docs/project/GOAL.md`, `docs/tourism/accessible_tourism_mvp_plan.md`, `README.md`, `TODOS.md` 기준으로 현재 MVP 진행 상태를 빠르게 보기 위한 요약이다.
응답 전략 변경 이력은 `docs/tourism/tourism_response_strategy_decision.md`에 별도로 기록한다.

## 전체 진행도

```text
MVP 전체              [████████░░] 77%
Backend contract     [█████████░] 90%
Live API coverage    [███████░░░] 70%
Data/sample coverage [████████░░] 80%
MVP fallback collect [█████████░] 90%
Sigungu fallback     [████░░░░░░] 35%
Region alias data    [████████░░] 80%
Web demo UI          [███████░░░] 70%
Quality/eval         [██████░░░░] 60%
Production readiness [██░░░░░░░░] 20%
```

현재 상태는 **live 캐시/색인/fallback 우선 + live TourAPI on miss + 웹 확인 UI** 단계다.
공개 데모 품질로 올리려면 데이터 커버리지, 20문항 eval, UI QA가 남아 있다.

## 영역별 상태

| 영역 | 진행도 | 상태 | 근거 |
|---|---:|---|---|
| TourAPI 연결 | 85% | 동작 | `KorWithService2` live 후보 조회, 지역 코드 캐시, 호출 상한 확인 |
| live 후보 조회 | 70% | 동작 | 캐시/색인/fallback miss 때 TourAPI 후보와 접근성 상세를 카드화, 프로세스 캐시 사용 |
| 샘플 데이터 | 82% | fallback + QA 도구 | 광역권별 약 20장 수준 Markdown fallback + curated fallback, 샘플 감사 스크립트 추가 |
| MVP fallback 수집 | 90% | 최소 안전망 확보 | `mvp`, `fallback-1`, `fallback-2`, `fallback-3` 완료, 중복 정리 후 350개 Markdown 확보 |
| 시군구 fallback 확장 | 35% | 1차 부분 수집 | TourAPI 지역 코드 234개 중 90개 시군구가 3장 이상 확보, 전국 실사용 250개 기준 보강은 계속 필요 |
| 지역명 매칭 데이터 | 80% | 생성 및 파싱 연결 | 행안부 `jscode20260325` 기반 `admin_region_aliases.json` 생성, 예외 입력 테스트 추가 |
| RAG 색인 | 75% | fallback | live API 호출 전 Markdown 샘플을 Chroma에서 검색 |
| `/tourism/chat` API | 94% | 안정화 | cache/fallback 우선, 안전한 오류, degraded fallback, 모호 지역 선택, 시군구 확장, 추론 보조 정책 반영 |
| 카드 응답 schema | 88% | 동작 | `TourismPlaceCard[]`, `sources`, `warnings`, `suggested_messages`, `reasoning_assist_used` 반환 |
| 웹 확인 UI | 70% | 시연 가능 | `/tourism-ui/`, 지역 버튼, 자유 입력, Help, Swagger 링크, 터널 확인 |
| 테스트 | 84% | 주요 회귀 커버 | `pytest` 57개 통과, backend 정책과 수집/감사/eval/지역명 매칭 중심 |
| 모델 품질 평가 | 70% | 1차 벤치마크 완료 | 20문항 fallback-only eval 실행 완료, 모델 추론 보조/native thinking 1차 비교 완료 |
| 운영/배포 | 20% | 임시 확인 | Cloudflare Quick Tunnel로 외부 임시 확인 가능, 정식 배포 아님 |

## 완료된 핵심 항목

- 한국관광공사 무장애 여행 정보 OpenAPI 호출 확인
- cache/fallback miss 때 live TourAPI 후보 조회를 사용하는 경로 추가
- 같은 지역 반복 요청을 줄이는 프로세스 메모리 캐시 추가
- mvp/fallback-1/fallback-2/fallback-3 분할 수집 완료
- fallback Markdown 샘플 품질 감사 스크립트와 리포트 절차 추가
- 2026-05-15 샘플 감사 결과 460개 중 460개 파싱 성공, 필수 필드 누락 0개, 중복 콘텐츠ID 0개 확인
- 2026-05-15 fallback-only 20문항 eval 실행 완료, API 실패 0건과 추론 보조 4건 확인
- 2026-05-15 로컬 모델 추론 보조 벤치마크 실행 완료, `gemma4:e4b`와 `huihui_ai/gemma-4-abliterated:e4b`는 native thinking이 되지만 30초 이상 지연 확인
- `data/raw/tourism_accessible` 기준 460개 Markdown fallback 확보
- MVP fallback 수집은 지역별 최소 안전망 기준으로 90% 완료다. 남은 10%는 20문항 eval에서 드러나는 부족 지역만 보강하는 작업이다.
- 전국 시군구 fallback은 별도 확장 작업이다. 2026-05-15 1차 부분 수집으로 TourAPI 지역 코드 234개 중 90개 시군구가 3장 이상 확보됐고, 3장 목표까지 남은 부족분은 약 365장이다. 전국 실사용 지역 250개 기준 보강은 계속 필요하다.
- 행안부 주민등록주소코드 기반 행정동/법정동 매칭 데이터 생성
- 지역 코드 캐시 생성 및 누락/손상 진단
- `/tourism/chat` endpoint 추가
- 관광 카드 Markdown codec 공유화
- Retriever 실패 시 local sample fallback과 `degraded/warnings` 노출
- 시군구 자동 확장 금지 정책 반영
- `근처/주변/가까운/인근` 명시 시 상위 지역 확장
- `중구` 같은 동명이 시군구는 지역 선택 후보 반환
- 관계 호칭만으로 나이 추정하지 않음
- 복합 질문에서만 LLM 추론 보조를 호출해 후보 카드 재랭킹과 확인 필요 메모를 반환
- 정적 웹 UI `/tourism-ui/` 추가
- Cloudflare Quick Tunnel 외부 확인 흐름 문서화
- Swagger/ReDoc/OpenAPI JSON 링크를 UI에 노출

## 남은 큰 작업

| 우선순위 | 작업 | 이유 | 현재 위치 |
|---|---|---|---|
| P1 | live 조회 QA | 실제 질문별 호출량, 쿼터, 응답 속도 확인 필요 | `/tourism/chat` |
| P1 | fallback 데이터 QA 실행 | 지역별 최소 샘플은 확보됐고 샘플 감사 리포트와 실제 질문 품질 확인 필요 | `scripts/audit_tourism_samples.py` |
| P1 | 웹 UI QA | 모바일/외부 사용자 관점에서 카드 가독성, Help, 오류 상태 확인 필요 | `frontend/web/` |
| P1 | 20문항 eval 수동 채점 및 live-on-miss 비교 | fallback-only 실행은 완료했고, 품질 점수와 live 경로 비교가 필요 | `data/eval/tourism_20_questions.jsonl` |
| P1 | 복합 질문 추론 보조 QA | `reasoning_assist_used`가 필요한 질문에서만 켜지고 지연 시간이 허용 범위인지 확인 필요 | `/tourism/chat` |
| P2 | 로컬 모델 비교 실행/수동 채점 | 기본 로컬 모델과 native thinking 사용 여부 결정 | `scripts/benchmark_tourism_reasoning_models.py`, `docs/tourism/tourism_model_reasoning_benchmark.md` |
| P2 | persistent TourAPI cache 검토 | 프로세스 재시작 후에도 반복 호출을 줄이기 위함 | `TODOS.md` |
| P2 | 시군구 fallback 확장 | 1차 부분 수집은 완료했지만 전국 실사용 지역 250개 기준 대상 확장과 남은 부족분 수집이 필요 | `docs/tourism/tourism_sigungu_fallback_scale.md` |
| P2 | 지역명 매칭 QA 확장 | 행정동/법정동 매칭은 연결됐지만 전국 250개 제품 대상 목록과 UI 후보 표시 QA가 필요 | `docs/tourism/admin_region_aliases.md` |
| P3 | Flutter 전환 여부 결정 | 웹 UI로 충분한지, 모바일 앱이 필요한지 판단 | `frontend/flutter_client/README.md` |
| P3 | 의료 안전 정보 확장 검토 | 일반 관광/무장애 관광을 여행 안전 지원으로 확장할지 판단. MVP에는 포함하지 않음 | `docs/project/professor_review_brief.md` |

## 다음 체크포인트

1. `/tourism-ui/`를 외부 터널 URL로 열어 사용자 흐름을 직접 테스트한다.
2. 서울/부산/강릉 외 지역 질문에서 live 조회 결과와 fallback 메시지를 수집한다.
3. fallback Markdown 카드 품질을 지역별로 샘플링한다.
4. 20개 질문 eval set을 fallback-only와 live-on-miss 환경에서 실행한다.
5. eval에서 빈 지역이 반복되면 시군구 fallback 대상 목록을 전국 실사용 250개 기준으로 확장하고 남은 부족분을 엔드포인트별 500건 안전치 안에서 나눠 보강한다.
6. 2026-06-10 전까지 기본 서비스 고정, 문서, 데모 스크립트, 최종 회귀 테스트를 끝낸다.

앱/Flutter 구현은 기본 서비스 완료 뒤로 미룬다.

## 빠른 확인 명령

장시간 실행 서버는 Codex 백그라운드 세션으로 조용히 띄우지 않는다. 에디터의 새 터미널에서 실행해 로그와 종료 상태를 직접 확인한다.

FastAPI와 Cloudflare는 같은 명령이 아니다. 외부 확인이 필요하면 터미널을 2개 연다.

터미널 1: FastAPI 서버

오늘처럼 TourAPI 호출을 더 쓰지 않을 때는 fallback-only로 실행한다.

```bash
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
