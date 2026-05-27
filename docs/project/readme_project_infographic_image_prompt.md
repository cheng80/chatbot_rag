# README 프로젝트 인포그래픽 이미지 생성 프롬프트

아래 프롬프트는 `docs/project/readme_project_infographic.html`의 최신 내용을 바탕으로, ChatGPT 이미지 생성이나 다른 이미지 생성 도구에 넣어 README용 생성형 요약 이미지를 만들 때 사용한다.

목표는 정확한 운영 명세표가 아니라, 프로젝트 첫 화면에서 한눈에 이해되는 AI 생성형 기술 요약 포스터다. 텍스트 정확도가 중요하므로 작은 문장을 많이 넣지 말고 큰 라벨 중심으로 구성한다.

## 최종 프롬프트

세로형 README용 기술 인포그래픽 이미지를 새로 그려줘.

중요:

- 웹페이지 스크린샷처럼 만들지 마.
- HTML 원본의 사실, 제목, 흐름, 정책만 추출해서 새 포스터 이미지로 재해석해.
- 작은 글씨를 많이 넣지 말고, 큰 섹션명 + 아이콘 + 짧은 설명 중심으로 구성해.
- 한국어 텍스트를 또렷하고 정확하게 써. 자신 없으면 작은 문장은 생략해.
- 존재하지 않는 기술명, API명, 숫자를 만들지 마.

반드시 유지할 큰 내용:

- 제목: `무장애·가족 친화 관광 챗봇`
- 부제: `한국관광공사 데이터, 저장 문서 검색, 로컬 AI 모델을 묶어 접근성 근거가 있는 관광지 카드를 상담 흐름으로 추천하는 로컬 실행형 프로젝트`
- 핵심 메시지: `TourAPI를 먼저 확인하고, 늦거나 실패하면 저장 자료 안전망으로 응답한다. 근거 없는 접근성 정보는 만들지 않는다.`

큰 섹션:

1. 추천 카드 흐름
   - 자연어 질문
   - 질문 해석
   - 대화 기억
   - TourAPI 우선 확인
   - 저장 기록 재사용
   - 저장 문서 검색
   - 카드 형식 정리
   - 응답 반환

2. 시스템 레이어
   - 사용자 화면
   - FastAPI 서버
   - AI와 판단 규칙

3. 데이터 파이프라인
   - 관광공사 API
   - 904개 예비 관광 카드
   - Chroma + bge-m3 검색 색인
   - SQLite 응답 저장소

4. 품질 게이트
   - 주요 자동 질문셋 실패 0
   - 지역·조건 변경 대화 테스트 통과
   - 오타 질문 200개 중 남은 실패 28

5. 현재 운영 정책
   - 근거 없는 정보 생성 금지
   - Live 우선 + 저장 자료 안전망
   - 시군구 자동 확장 금지
   - LLM 보조는 선택 사항

표시해도 되는 핵심 기술명:

- FastAPI
- `/tourism/chat`
- Chroma
- bge-m3
- TourAPI
- SQLite
- SuperGemma4
- JSON

정확히 써야 하는 문구:

- `TourAPI 우선 확인`
- `저장 자료 안전망`
- `최신 정보 더 찾기`
- `근거 없는 정보 생성 금지`
- `자료 부족은 코드로 만들지 않음`
- `휠체어`

숫자 표현:

- `904개 예비 관광 카드`
- `top_k=40`
- `실패 0`
- `남은 실패 28`
- `5초 대기`

디자인 스타일:

- tall vertical README technical infographic poster
- off-white paper background
- subtle paper texture
- clean whiteboard explainer style
- 첨부한 기존 README 이미지처럼 가족·휠체어 사용자·관광지 풍경·서버·DB·문서·돋보기·체크리스트 아이콘을 중심으로 구성
- black ink sketch lines
- muted green, teal, red, yellow, blue, violet accents
- large numbered section badges
- simple technical icons
- roomy spacing and large readable Korean labels
- startup technical blog / AI thread style

피해야 할 것:

- 웹페이지 캡처처럼 보이는 결과
- 작은 글씨가 빽빽한 운영 명세표
- 랜덤한 영어/한글 더미 텍스트
- 존재하지 않는 기술명이나 수치
- `휄체어` 같은 오탈자
- 자료 부족을 코드가 해결한다는 표현
- 뇌, 뉴런, 해부학적 머리, 로봇 머리처럼 관광 서비스 맥락과 안 맞는 AI 아이콘
