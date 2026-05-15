---
version: draft
name: Tourism Chatbot Demo
source_references:
  - https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/intercom
  - https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/airbnb
  - https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/mintlify
---

# Tourism Chatbot Demo DESIGN.md

이 문서는 무장애·가족 친화 관광 챗봇 시연 UI를 만들 때 참고할 프로젝트 전용 디자인 기준이다.
원본 `awesome-design-md` 자료를 그대로 복제하지 않고, 챗봇·관광 카드·출처 확인 화면에 맞는 원칙만 선별했다.

## Current Direction

사용자가 원하는 최종 톤은 대시보드가 아니라 메신저형 관광 상담 챗봇이다.
카카오톡처럼 친숙한 채팅창 구조를 참고하되, 특정 서비스 로고·브랜드 자산은 사용하지 않는다.

## Design Goal

시연자는 질문을 입력하고, 관람자는 다음 다섯 가지를 첫 화면에서 바로 이해해야 한다.

- 어느 지역을 선택했는지
- 추천 관광지가 카드로 어떻게 제시되는지
- 더 많은 결과를 어떻게 요청하는지
- 추천 근거와 출처가 어디인지
- 실제 방문 전 확인해야 하는 경고 문구가 무엇인지

## Reference Fit

| Reference | 가져올 점 | 피할 점 |
|---|---|---|
| Intercom | 대화형 제품답게 부드러운 상담 화면, 흰 카드, 명확한 CTA | 브랜드 오렌지를 과하게 쓰는 것 |
| Airbnb | 관광지 카드, 장소 사진, 지역 선택, 따뜻한 consumer marketplace 감각 | 숙박 예약 서비스처럼 보이는 가격/평점 중심 UI |
| Mintlify | 출처·주의·API 상태를 읽기 쉽게 정리하는 문서형 패널 | 개발자 문서처럼 너무 건조한 3열 레이아웃 |

## Visual Theme

- 분위기: 모바일 메신저 안에서 관광 상담원이 답하는 느낌.
- 밀도: 한 화면에 채팅 헤더, 주의 문구, 지역 quick reply, 답변 말풍선, 추천 카드가 보여야 한다.
- 장식: 앱 프레임, 말풍선, 카드만 사용한다. 랜딩 페이지식 hero는 쓰지 않는다.
- 신뢰 신호: 출처, 확인 필요 문구, 응답 경로 상태를 봇 메시지 흐름 안에 노출한다.

## Color Palette

| Token | Hex | Role |
|---|---:|---|
| canvas | `#eef2f6` | 전체 배경. 모바일 메신저 바깥 영역 |
| surface | `#ffffff` | 입력 패널, 답변 패널, 카드 |
| chat-bg | `#b9cedc` | 채팅방 배경 |
| app-yellow | `#fee500` | 메신저 헤더와 주요 버튼 |
| surface-soft | `#f6f7f8` | quick reply, 보조 버튼 |
| ink | `#17201b` | 기본 텍스트 |
| muted | `#66746d` | 설명, 보조 정보 |
| line | `#ded8cf` | 카드/패널 경계 |
| brand | `#3a1d1d` | 헤더 텍스트, 주요 CTA 텍스트 |
| brand-dark | `#2f1717` | 강조 텍스트 |
| travel | `#ff7a45` | 더 보기, 추천 액션의 보조 강조 |
| warning | `#9a5b00` | 확인 필요/주의 문구 |
| danger | `#b3261e` | API 오류 |
| success | `#277246` | 정상 응답 상태 |

## Typography

- 기본 폰트: system UI, `Inter`, `Pretendard`, `Apple SD Gothic Neo`, sans-serif.
- H1: 20-24px, 700, line-height 1.2. 메신저 헤더 안에서 과하게 커지지 않아야 한다.
- H2: 14-18px, 700.
- 카드 제목: 16-18px, 700.
- 본문: 13-15px, line-height 1.45-1.65.
- 보조/출처/태그: 11-13px, 700 또는 800.
- letter-spacing은 0을 기본으로 둔다. 한국어 UI에서 음수 자간을 사용하지 않는다.

## Layout

- 전체 화면 가운데에 430-760px 폭의 채팅 앱 프레임을 둔다.
- 채팅 헤더에는 챗봇 이름, 상태, API 링크를 작게 둔다.
- 경고 문구는 시스템 공지 말풍선처럼 채팅방 최상단에 둔다.
- 지역 선택은 quick reply 칩으로 말풍선 아래에 둔다.
- 추천 카드는 봇 말풍선 안에서 1열 카드 또는 데스크톱 2열 카드로 둔다.
- 입력창은 채팅방 하단 composer처럼 보이게 한다.

## Components

### Region Selector

- pill 또는 8px radius 버튼.
- 선택된 지역은 `app-yellow` 배경과 진한 텍스트를 사용한다.
- 버튼 텍스트는 짧게 유지한다: `서울`, `서울 강남구`, `부산 중구`.
- 지역 선택만으로 질문 입력창이 자연어 질문으로 채워져야 한다.

### Chat Composer

- textarea와 CTA 버튼을 나란히 배치한다.
- CTA 문구는 `추천 받기`.
- 로딩 중에는 `조회 중`으로 바꾸고 버튼을 disabled 처리한다.

### Chat Bubble

- 봇 말풍선은 흰색, 사용자가 선택하는 입력 영역은 노란 CTA를 쓴다.
- 답변, 출처, 추천 카드는 모두 채팅 흐름의 일부로 보여야 한다.
- 빈 상태도 봇의 안내 메시지처럼 보여야 한다.

### Recommendation Card

카드는 다음 정보를 반드시 가진다.

- 관광지명
- 주소
- 추천 이유
- 접근성/가족 태그
- 주차, 화장실, 휠체어, 유아차 등 확인된 세부 정보
- 출처 이름
- 상세 정보 펼침 버튼
- 장소명/주소 기반 지도 검색 링크

카드 이미지는 있으면 크게 보여주고, 없으면 차분한 placeholder를 사용한다.
한국관광공사 열린관광 사이트의 상세 URL은 콘텐츠 ID만으로 안정적인 공개 상세 링크를 만들 수 없으므로, `access.visitkorea.or.kr/detail/...` 같은 추정 URL을 원문 링크로 만들지 않는다.

### More Button

- 추천 카드 아래에 `더 보기` 버튼을 둔다.
- API 응답의 `suggested_messages`에 `더 보기` 계열 문구가 있으면 해당 문구로 요청한다.
- 없을 때는 비활성화하거나 “현재 추가 후보 없음” 상태로 둔다.

### Source Panel

- 답변 말풍선 안 또는 바로 아래 봇 말풍선에 별도 `출처` 영역을 둔다.
- 전역 출처(`sources`)와 카드별 출처(`source_name`, `source_url`)를 구분한다.
- `source_url`이 없거나 깨진 열린관광 추정 URL이면 클릭 링크가 아니라 출처명만 보여준다.
- 출처가 없으면 “응답 후 출처가 표시됩니다” 같은 빈 상태를 보여준다.

### Warning

- 화면 상단에 상시 노출한다.
- 문구는 짧고 구체적이어야 한다.
- 예: “실제 방문 전 운영 시간, 휠체어 동선, 주차, 화장실 정보는 공식 안내·전화·현장 정보로 다시 확인하세요.”

## Do

- 카드와 출처를 함께 보여준다.
- 카드 안에서 상세 편의정보를 펼쳐 볼 수 있게 한다.
- 원문 링크가 불확실하면 지도 검색과 출처명으로 대체한다.
- fallback, live, indexed, cache 상태를 숨기지 않는다.
- 접근성 정보가 없으면 “확인 필요”로 표시한다.
- 데모 화면에서도 빈 상태를 실제 제품처럼 디자인한다.

## Do Not

- 관광지 접근성 정보를 추측해서 확정 표현으로 쓰지 않는다.
- 카드 안에 너무 많은 설명 문장을 넣지 않는다.
- 마케팅 landing page처럼 hero만 크고 실제 챗봇 조작이 아래로 밀리게 만들지 않는다.
- 브랜드 레퍼런스 색을 그대로 베껴 특정 회사 서비스처럼 보이게 하지 않는다.

## Agent Prompt

이 디자인을 적용할 때는 다음 기준을 따른다.

```text
무장애 관광 챗봇 시연 UI를 만든다.
따뜻한 상담 화면, 관광지 추천 카드, 명확한 지역 선택, 더 보기 CTA, 출처 패널, 방문 전 확인 경고를 첫 화면에서 보이게 한다.
Intercom의 대화형 친절함, Airbnb의 여행 카드 가독성, Mintlify의 출처/문서 패널 명료함만 참고하고 특정 브랜드처럼 보이지 않게 한다.
```
