# 앱 디자인·기획 컨텍스트 묶음

마지막 갱신: 2026-05-18

이 문서는 Codex의 `huashu-design` 글로벌 스킬이나 다른 HTML 디자인 도구에 무장애 관광 챗봇 앱 화면을 의뢰할 때 함께 참고할 문서를 모아 둔 작업용 컨텍스트다. 원문 전체를 반복하지 않고, 디자인 작업에 필요한 판단 기준과 최신 기획 흐름을 빠르게 전달하는 것을 목표로 한다.

## 사용 대상

기본 사용 대상은 `huashu-design` 스킬이다.

- 설치 문서: `docs/design/huashu_design_usage.md`
- 글로벌 스킬 위치: `$CODEX_HOME/skills/huashu-design`
- 용도: HTML 기반 고충실도 프로토타입, 디자인 방향 탐색, 발표 deck, 카드 UI 비교안

이 문서는 디자인 시안 생성을 위한 컨텍스트이며, 생성된 HTML을 곧바로 production 코드로 복사하라는 뜻이 아니다. 실제 구현은 기존 `/tourism-ui/`의 API 계약, 카드 렌더링, 테스트 절차를 유지한 채 별도 작업으로 선별 반영한다.

## 핵심 방향

- 현재 제품은 무장애 관광 추천 챗봇이다.
- 기본 화면은 메신저형 상담 UI이며, 관광지 추천 카드를 중심으로 보여준다.
- Flutter 이전 가능성을 고려해 기본 디자인 방향은 Material 3 Expressive 계열로 잡는다.
- 부드러운 녹색/민트 tonal palette, 큰 터치 타깃, 명확한 containment, 둥근 shape, 가벼운 모션을 우선한다.
- 대화 경험은 카카오톡의 친숙한 말풍선 상담감과 인스타그램 DM의 빠른 메시지 흐름을 참고한다. 단, 특정 서비스의 로고·브랜드 자산·고유 UI를 복제하지 않고 상호작용 패턴만 참고한다.
- 카드 정보는 인스타그램 피드처럼 이미지, 장소명, 짧은 설명, 저장/공유/지도 액션, 근거 칩이 이어지는 구조를 참고한다.
- 사용자는 지역, 접근성 조건, 제외 조건, 후속 질문을 자연어로 입력할 수 있다.
- 최근 보강 방향은 자연어 해석만 강화하는 것이 아니라, 사용자가 조건을 명확히 고를 수 있게 돕는 UI를 추가하는 것이다.
- 디자인은 발표용 랜딩 페이지가 아니라 실제 조작 가능한 앱 화면이어야 한다.

## 현재 앱 UI 기준

참조 문서:

- `docs/design/tourism_chatbot_DESIGN.md`
- `frontend/web/README.md`
- `docs/project/tourism_ui_midcheck_20260517.md`

핵심 UI 기준:

- Material 3 Expressive 기반의 부드러운 녹색 모바일 메신저형 앱 프레임
- 방문 전 확인 안내 말풍선
- 지역 quick reply
- 사용자 질문 말풍선
- 챗봇 답변 말풍선
- 인스타그램 피드형 추천 관광지 카드
- 카드별 접근성 태그와 근거 칩
- 저장, 공유, 지도, 상세 정보 같은 카드 액션
- 상세 정보 펼침
- 지도 검색
- 출처 표시
- 개발 모드와 릴리즈 모드 분리

피해야 할 방향:

- 마케팅 랜딩 페이지처럼 hero가 먼저 나오는 구조
- 장식적인 카드만 많고 실제 질문/추천 흐름이 약한 화면
- 카카오톡 또는 인스타그램의 로고, 아이콘, 고유 레이아웃을 그대로 복제하는 화면
- 접근성 정보를 추측해 확정적으로 표현하는 카드
- 내부 진단 정보가 릴리즈 화면에 그대로 노출되는 구조
- 과한 투명도나 유리 장식 때문에 카드 본문 가독성이 떨어지는 화면

## 최근 적용된 서비스 보강안

참조 문서:

- `docs/tourism/tourism_service_enhancement_ideas.md`

최근 1차 반영된 항목:

1. 조건 확인형 질문 UI
   - 사용자의 접근성 표현이 애매할 때 바로 추천하지 않고 선택 버튼을 보여준다.
   - 예: 휠체어 접근, 입구/동선 접근로, 어르신 이동 부담 적은 곳, 장애인 화장실, 대중교통 접근.

2. 추천 카드별 근거 강조
   - 카드 본문에 짧은 근거 칩을 표시한다.
   - 예: 휠체어, 동선, 화장실, 주차, 승강, 수어/자막, 점자/촉지, 유아 편의.

3. 데이터 부족 안내와 조건 완화
   - 카드가 없을 때 실패 문장만 보여주지 않는다.
   - 같은 시·도까지 넓히기, 조건 완화하기, 같은 조건으로 다시 찾기 같은 회복 액션을 버튼으로 제공한다.

4. 지역 확장 컨트롤
   - `근처`, `주변`, `가까운`만으로 자동 광역 확장을 하지 않는다.
   - 시군구 안의 후보가 부족하면 `같은 시·도까지 넓혀 보기` 버튼을 제안한다.
   - 사용자가 명시적으로 확장한 경우에만 더 넓은 지역 후보를 섞는다.

아직 큰 별도 작업으로 남겨둔 항목:

- 옵션형 추천 모드

## 옵션형 추천 앱 기획

참조 문서:

- `docs/tourism/option_flow_app_concept.md`

핵심 아이디어:

- 사용자가 문장을 쓰지 않고 선택지를 따라가며 관광 조건을 만든다.
- 지역, 관광 유형, 동반 상황, 접근성 조건, 필수/선호 조건, 제외 조건을 순서대로 받는다.
- 선택값은 내부 검색 조건으로 바로 변환한다.
- 자연어 입력은 기본 경로가 아니라 `자연어로 조건 추가` 같은 보조 모드로 둔다.

추천 화면 흐름:

1. 지역 선택
2. 관광 유형 선택
3. 동반 상황 선택
4. 접근성 조건 선택
5. 필수 조건과 선호 조건 분리
6. 제외 조건 선택
7. 추천 카드 확인
8. 조건 완화 또는 지역 확장

자연어 보조 모드:

- 복잡한 문장을 구조화 조건으로 변환한다.
- 변환 결과를 바로 적용하지 않고 사용자에게 확인시킨다.
- 예: “엄마가 오래 못 걸어서 많이 안 움직이는 곳이면 좋겠어”
  - 동반 상황: 어르신/보행 약자
  - 선호 조건: 짧은 동선, 앉아 쉴 곳
  - 필수 조건: 없음

## 품질·검증 관련 최근 문서

참조 문서:

- `docs/project/progress_overview.md`
- `docs/project/mvp_quality_work_log.md`
- `docs/tourism/tourism_medium_chat_model_comparison.md`
- `docs/tourism/tourism_hard_chat_eval_v2_findings.md`
- `docs/tourism/tourism_hard_nlu_condition_transformer.md`
- `docs/tourism/tourism_keyword_variant_followup.md`
- `docs/tourism/ml_evaluation_governance.md`

디자인에 반영해야 하는 품질 판단:

- 모델이 모든 문맥을 단정하게 만들지 않는다.
- 의미가 애매하면 추가 질문으로 보내는 정책이 필요하다.
- 카드가 없을 때는 실패가 아니라 회복 가능한 상태로 보여준다.
- 수어/자막, 점자/촉지, 보조견, 고령자 조건은 데이터 커버리지 부족이 자주 나타날 수 있다.
- 추천 결과는 방문 전 공식 안내, 전화, 현장 정보로 다시 확인해야 한다.

## 데이터와 서비스 범위 관련 문서

참조 문서:

- `docs/tourism/tourism_dataset_inventory.md`
- `docs/tourism/tourism_data_operations.md`
- `docs/tourism/admin_region_aliases.md`
- `docs/tourism/tourism_response_strategy_decision.md`
- `docs/tourism/tourism_intent_classifier.md`

디자인에 반영할 범위:

- 현재 서비스는 일반 관광 전체가 아니라 무장애 관광 연관 장소 제공이 중심이다.
- 일반 관광지 질문이 들어오면 무장애 관광 중심 서비스임을 안내해야 한다.
- 행정구역명은 현재 행정구역 기준으로 처리한다.
- 과거 지명이나 통폐합 지역은 사용자에게 과도하게 기술적으로 노출하지 않는다.

## UI QA 스크린샷

최근 기능 보강 대표 캡처:

- `data/generated/tour_api/ui_qa/enhancement_ideas_20260518/condition_clarification_ui.png`
- `data/generated/tour_api/ui_qa/enhancement_ideas_20260518/card_evidence_highlights.png`
- `data/generated/tour_api/ui_qa/enhancement_ideas_20260518/no_card_recovery_actions.png`
- `data/generated/tour_api/ui_qa/enhancement_ideas_20260518/region_expansion_control.png`

이전 앱형 UI QA 대표 캡처:

- `data/generated/tour_api/ui_qa/regression_20260517_fixed/debug_initial.png`
- `data/generated/tour_api/ui_qa/regression_20260517_fixed/debug_final.png`
- `data/generated/tour_api/ui_qa/regression_20260517_fixed/release_initial.png`
- `data/generated/tour_api/ui_qa/regression_20260517_fixed/release_final.png`
- `data/generated/tour_api/ui_qa/regression_20260517_fixed/mobile_cards_viewport.png`

## Huashu Design에 줄 수 있는 프롬프트

```text
huashu-design 스킬을 사용해서 무장애 관광 추천 챗봇 앱 화면을 디자인해줘.

현재 제품은 메신저형 상담 UI이며, 사용자가 지역과 접근성 조건을 입력하면 무장애 관광지 카드를 추천한다.
디자인은 마케팅 랜딩 페이지가 아니라 실제 조작 가능한 앱 화면이어야 한다.

작업 방식:
- 먼저 2~3개의 디자인 방향을 간단히 제안한다.
- 선택한 방향 기준으로 모바일 우선 HTML 프로토타입을 만든다.
- 화면은 실제 클릭 흐름이 있는 4~6개 화면으로 구성한다.
- 더미 데이터는 명확히 예시로만 표시한다.
- production 코드 반영은 별도 단계로 남긴다.

반드시 포함할 것:
- Material 3 Expressive 기반의 부드러운 녹색 tonal 채팅 헤더
- 방문 전 확인 안내
- 지역 quick reply
- 사용자 질문 말풍선
- 챗봇 답변 말풍선
- 추천 관광지 카드
- 카드별 접근성 근거 칩
- 상세 정보 펼침 버튼
- 출처 표시
- 카드가 없을 때 조건 완화/지역 확장 버튼
- 조건이 애매할 때 선택형 확인 버튼

새로 검토할 화면:
- 옵션형 추천 모드
- 지역 선택, 관광 유형 선택, 동반 상황 선택, 접근성 조건 선택, 필수/선호 조건 분리, 제외 조건 선택, 추천 결과 확인 흐름
- 자연어 조건 추가는 기본 입력이 아니라 보조 모드로 둔다.
- 자연어 보조 모드는 해석 결과를 바로 적용하지 말고 사용자 확인 화면을 거친다.

톤:
- 따뜻하지만 실무적인 관광 상담 앱
- 대시보드가 아니라 모바일 메신저 기반 서비스
- Flutter 이전을 고려해 Material 3 Expressive에 가까운 색상 토큰, 큰 버튼, 둥근 카드, 명확한 상태 표현을 사용한다.
- 카드와 버튼은 과하게 장식하지 않고 빠르게 읽히게 한다.
- 접근성 정보는 추측하지 않고 확인 필요 문구를 유지한다.
```

## 디자인 결과를 Codex에 구현 요청할 때

Huashu Design으로 디자인 산출물을 만든 뒤 Codex에는 다음처럼 요청한다.

```text
huashu-design으로 만든 HTML 프로토타입과
docs/project/app_design_planning_context.md의 기준을 비교해서
우리 frontend/web UI에 적용 가능한 범위만 구현해줘.
기존 /tourism-ui/의 API 계약과 카드 렌더링 로직은 유지하고,
옵션형 추천 모드는 별도 진입점 또는 섹션으로 분리해줘.
```

구현 요청 시 지켜야 할 기준:

- 디자인 HTML을 그대로 복사하지 않는다.
- 기존 `frontend/web/index.html`, `frontend/web/styles.css`, `frontend/web/app.js` 구조와 API 호출 흐름을 유지한다.
- `/tourism/chat` 요청/응답 계약을 바꾸지 않는다.
- 카드 렌더링, 출처 표시, 방문 전 확인 안내, 빈 결과 회복 버튼을 유지한다.
- 구현 뒤 `node --check frontend/web/app.js`, `git diff --check`, 관련 pytest, 브라우저 시각 QA를 수행한다.

## Huashu Design 작업 요청 예시

옵션형 추천 모드:

```text
huashu-design 스킬을 사용해서 옵션형 무장애 관광 추천 모드의 모바일 우선 HTML 프로토타입을 만들어줘.
지역 선택, 관광 유형, 동반 상황, 접근성 조건, 필수/선호 조건, 제외 조건, 추천 결과, 빈 결과 회복 액션을 포함해줘.
기존 챗봇은 메신저형 상담 UI이고, 새 시안은 Material 3 Expressive 기반의 부드러운 녹색 tonal UI를 기준으로 한다. 랜딩 페이지식 hero는 피해야 한다.
```

현재 UI 개선안:

```text
huashu-design 스킬로 현재 무장애 관광 챗봇 UI 개선 시안을 만들어줘.
조건 확인 버튼, 카드별 근거 칩, 출처 표시, 조건 완화/지역 확장 버튼이 더 잘 읽히도록 3개 방향을 비교해줘.
대화 흐름은 카카오톡과 인스타그램 DM의 친숙한 메신저 경험을 참고하고,
추천 카드는 인스타그램 피드처럼 이미지 중심 카드, 저장/공유/지도 액션, 근거 칩이 보이게 구성해줘.
단, 특정 서비스 로고나 고유 브랜드 자산은 복제하지 마.
생산 코드는 수정하지 말고 HTML 프로토타입만 만들어줘.
```

발표용 deck:

```text
huashu-design 스킬로 교수님 설명용 HTML 발표 deck을 만들어줘.
주제는 무장애 관광 챗봇의 데이터 검색, 자연어 처리, 조건 정규화, RAG/카드 추천, 추가 질문, 옵션형 추천 모드다.
6~8장 정도로 짧고 읽기 쉽게 구성해줘.
```
