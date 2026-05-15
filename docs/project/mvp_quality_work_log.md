# MVP 품질 개선 및 개발 작업 목록

마지막 갱신: 2026-05-15

이 문서는 프로젝트 발표에서 “단순 챗봇 구현”이 아니라, MVP 품질을 올리기 위해 어떤 검증, 데이터, 안정화, 운영 준비를 했는지 설명하기 위한 작업 목록이다.

## 한 줄 요약

로컬 RAG 챗봇에서 출발해, 한국관광공사 무장애 여행 정보 OpenAPI, Chroma fallback, 지역명 매칭, 데이터 감사, 웹 확인 UI, 이벤트 로그, 평가셋을 갖춘 **검증 가능한 무장애·가족 친화 관광 상담 MVP**로 확장했다.

## 핵심 개발 흐름

| 단계 | 작업 | 발표 포인트 |
|---|---|---|
| 1 | FastAPI + ChromaDB + Ollama 기반 로컬 RAG MVP 구현 | 외부 LLM API 없이 로컬 임베딩/생성 모델로 답변 생성 |
| 2 | 관광 챗봇 도메인 전환 | 일반 문서 QA에서 무장애·가족 친화 관광 상담으로 문제 범위 구체화 |
| 3 | TourAPI 연동 | 한국관광공사 국문 관광정보/무장애 여행 정보 API를 검증하고 코드화 |
| 4 | 관광 카드 schema 설계 | 답변을 자유 텍스트가 아니라 `TourismPlaceCard[]` 구조로 반환 |
| 5 | cache/fallback-first + live-on-miss 전략 확정 | 매 요청마다 API를 때리지 않고, 캐시/색인/fallback 후 live 조회 |
| 6 | 웹 확인 UI 추가 | API 결과를 비개발자도 카드 형태로 볼 수 있는 시연 화면 제공 |
| 7 | Cloudflare Quick Tunnel 확인 절차 문서화 | 로컬 Mac mini에서 외부 테스트 가능한 임시 공유 경로 확보 |

## 데이터 품질 작업

| 작업 | 결과 | 왜 중요한가 |
|---|---:|---|
| TourAPI 지역 코드 캐시 생성 | `data/processed/tour_area_codes.json` | 시군구 코드를 하드코딩하지 않고 공식 API 기준으로 관리 |
| fallback Markdown 분할 수집 | `data/raw/tourism_accessible` 460개 | API 장애/쿼터/네트워크 문제에도 시연 가능한 최소 안전망 |
| Chroma 재색인 | 461문서 / 463청크 | Markdown fallback을 RAG 검색 대상으로 사용 |
| 샘플 감사 스크립트 추가 | `scripts/audit_tourism_samples.py` | 파싱 실패, 필수 필드 누락, 중복 콘텐츠ID를 자동 점검 |
| 중복 콘텐츠ID 정리 | 중복 16개 제거 후 0개 | 강릉/강원 중복 수집 같은 품질 문제를 재발 방지 |
| 시군구 fallback 1차 수집 | 234개 TourAPI 지역 중 90개가 3장 이상 | 전국 단위 서비스로 확장하기 위한 중간 커버리지 확보 |
| 행정동/법정동 매칭 데이터 생성 | alias 662개, dong alias 11467개 | 사용자가 실제로 쓰는 지역명 입력을 시군구 코드로 연결 |

## 질문 이해 및 지역 정책

| 작업 | 예시 | 발표 포인트 |
|---|---|---|
| 동명이 지역 선택 질문 | `중구에서 휠체어 타시는 아버지와...` -> 어느 지역 중구인지 추가 질문 | 모호한 지역을 추측하지 않음 |
| 광역+시군구 확정 | `부산 중구에서...` -> 부산 중구 | 짧은 실제 사용자 표현을 처리 |
| 법정동/행정동 해석 | `해운대 좌동...` -> 부산 해운대구 | TourAPI가 직접 받지 않는 생활권 표현 보정 |
| 일반구/하위구 처리 | `창원 마산합포구...` -> 경남 창원시 TourAPI 코드 | 행정 체계와 TourAPI 체계 차이를 흡수 |
| 좁은 지역 자동 확장 금지 | `서울 강남구...` -> 강남구 결과만 제공 | 사용자의 명시 지역을 임의로 넓히지 않음 |
| 근처/주변 확장 허용 | `서울 강남구 근처...` -> 서울 범위 포함 | 사용자가 확장을 요청할 때만 상위 지역 포함 |
| 관계 호칭 나이 추정 금지 | `아빠`, `어머니`만으로 고령자 조건 부여 안 함 | 사용자 가족 상황을 임의로 추정하지 않음 |

## API 안정화 및 안전장치

| 작업 | 내용 |
|---|---|
| 안전한 오류 응답 | 내부 예외 문자열을 API 응답에 그대로 노출하지 않음 |
| degraded/fallback 표시 | Retriever, Chroma, Ollama, TourAPI 문제 시 fallback 사용 여부를 응답/로그에서 확인 |
| live Markdown 캐시 | live 조회 결과를 `data/generated/tour_api/live_markdown`에 저장해 반복 호출 절감 |
| 프로세스 메모리 캐시 | 같은 지역 반복 요청의 API 호출과 디스크 파싱 비용 감소 |
| 이벤트 로그 | `/tourism/chat` 응답을 JSONL로 기록하고, 기본값은 원문 질문 대신 hash 저장 |
| 로그 분석 노트북 | `notebooks/tourism_event_log_analysis.ipynb`로 lookup mode, 지역, 카드 분포 차트 확인 |

## 테스트와 평가 준비

| 작업 | 현재 상태 |
|---|---|
| pytest 회귀 테스트 | 57개 통과 |
| API route 테스트 | `/tourism/chat` 성공/오류/blank message/fallback 검증 |
| 관광 카드 codec 테스트 | Markdown 카드 round-trip 검증 |
| 지역 정책 테스트 | 동명이 지역, 시군구 확장 금지, 근처 확장, 행정동/법정동 입력 검증 |
| 수집 스크립트 테스트 | 중복 콘텐츠ID, 시군구 커버리지 계산, alias 생성 검증 |
| 20문항 평가셋 작성 | `data/eval/tourism_20_questions.jsonl` |
| 평가 실행 스크립트 | `scripts/eval_tourism_chat.py` |
| 모델 비교 준비 | `supergemma4` vs `gemma3` 비교는 다음 품질 작업 |

## 문서화 및 운영 준비

| 문서 | 역할 |
|---|---|
| `README.md` | 설치, 실행, API, UI, 터널 사용법 |
| `docs/project/GOAL.md` | MVP 완성 기준과 정책 결정 기록 |
| `docs/project/progress_overview.md` | 전체 진행도 차트와 다음 체크포인트 |
| `docs/tourism/tourism_response_strategy_decision.md` | offline-index 우선 vs cache/fallback-first + live-on-miss 비교 |
| `docs/tourism/tourism_data_collection_plan.md` | 수집 배치, 호출량, 안전치 500건/day 기록 |
| `docs/tourism/tourism_sample_quality.md` | 샘플 감사 결과와 중복 원인/재발 방지 |
| `docs/tourism/tourism_sigungu_fallback_scale.md` | 전국 fallback 수집 규모와 250개 실사용 지역 목표 |
| `docs/tourism/admin_region_aliases.md` | 행정동/법정동 매칭 데이터 생성 및 사용 원칙 |
| `.env.example` | 팀원이 민감정보 없이 환경 변수를 재현 가능 |

## 발표에서 강조할 차별점

1. **환각 억제**: 접근성 정보가 없으면 추측하지 않고 `확인 필요`로 남긴다.
2. **출처 기반 카드**: 추천 이유, 접근성 태그, 가족 태그, 주소, 출처 URL을 구조화한다.
3. **데모 안정성**: live API가 실패해도 Chroma/Markdown fallback으로 응답 가능하다.
4. **쿼터 절약**: live 캐시, 프로세스 캐시, fallback-first 전략으로 공공 API 호출을 줄인다.
5. **지역명 현실성**: `부산 중구`, `좌동`, `마산합포구` 같은 실제 사용자 표현을 처리한다.
6. **검증 가능성**: 테스트, 샘플 감사, 이벤트 로그, 20문항 eval로 품질을 반복 측정할 수 있다.
7. **확장 계획 명확성**: 전국 250개 실사용 지역, 주기적 갱신, SQLite 로그 전환, 모델 비교가 TODO로 분리돼 있다.

## 남은 발표 전 보강

- 20문항 eval을 실제 실행하고 실패 질문을 정리한다.
- `/tourism-ui/`를 모바일 폭과 외부 터널 환경에서 QA한다.
- `lookup_mode=cache/indexed/sample/live`별 대표 화면을 캡처한다.
- 전국 250개 실사용 지역 목록을 확정하고 시군구 fallback 부족분을 우선순위화한다.
- 모델 비교 결과를 한 장짜리 표로 정리한다.
