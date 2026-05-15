# 문서 인덱스

마지막 갱신: 2026-05-15

## 폴더 구조

```text
docs/
├─ project/      프로젝트 목표, 진행도, 교수님 검토 브리프, 다음 세션 handoff
├─ tourism/      관광 챗봇 기획, RAG/TourAPI 응답 전략, 데이터 수집 계획, eval
├─ rag/          일반 RAG 챗봇 설계
├─ setup/        로컬 개발 환경 정리
├─ tools/        gstack-codex 등 개발 도구 기록
└─ references/   공고문, 한국관광공사 OpenAPI 원자료

notebooks/
└─ 이벤트 로그 분석, 초기 API 탐색, 모델 비교 보조 노트북
```

## 먼저 볼 문서

- `project/next_session_prompt.md`: 새 세션 시작 문서
- `project/professor_review_brief.md`: 교수님/외부 검토자에게 보여줄 단일 검토 브리프. RAG, LLM, OpenAPI, 캐시, 폴백, eval 용어를 함께 설명한다.
- `project/GOAL.md`: 현재 MVP 목표와 API 판정 기준
- `project/progress_overview.md`: 전체 진행도 요약
- `project/mvp_quality_work_log.md`: 발표용 MVP 품질 개선 및 개발 작업 목록
- `project/demo_capture_scenarios.md`: 발표용 캡처와 시연 질문 시나리오
- `tourism/accessible_tourism_mvp_plan.md`: 무장애·가족 친화 관광 챗봇 구현 플랜
- `tourism/tourism_response_strategy_decision.md`: cache/RAG-first + TourAPI live-on-miss와 offline-index 방식 비교 및 되돌림 기준
- `tourism/tourism_data_collection_plan.md`: 폴백 데이터 수집 계획과 OpenAPI 호출량 기록
- `tourism/tourism_sigungu_fallback_scale.md`: 전국 시군구 폴백 예상 규모
- `tourism/admin_region_aliases.md`: 행정동/법정동 지역명 매칭 데이터 생성 기록
- `tourism/tourism_eval_questions.md`: `/tourism/chat` 20문항 평가셋 설명
- `tourism/tourism_model_reasoning_benchmark.md`: 로컬 LLM 추론 보조와 native thinking 비교 기준
- `tourism/tourism_sample_quality.md`: 폴백 Markdown 샘플 품질 감사 방법
- `../notebooks/tourism_event_log_analysis.ipynb`: `/tourism/chat` JSONL 이벤트 로그와 matplotlib 차트 분석

## 원자료

- `references/(공고문)『2026_생성형_AI_활용_관광_프롬프톤_부문』_공고문.pdf`
- `references/개방데이터_활용매뉴얼(국문)/`
- `references/개방데이터_활용매뉴얼(무장애여행)/`
