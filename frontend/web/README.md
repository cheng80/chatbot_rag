# Web Frontend

`/tourism/chat` 백엔드 응답을 눈으로 확인하기 위한 메신저형 정적 웹 UI다.
빌드 도구 없이 HTML/CSS/JS만 사용한다.

현재 화면은 발표 시연을 위해 카카오톡 같은 친숙한 채팅창 구조를 참고하되, 특정 서비스 로고나 브랜드 자산은 쓰지 않는다. 디자인 기준은 `docs/design/tourism_chatbot_DESIGN.md`에 둔다.

## 화면 구성

- 상단 노란 채팅 헤더와 API 문서 링크
- 방문 전 확인 필요 공지 말풍선
- 지역 선택 quick reply 버튼
- 자유 질문 입력창과 `추천 받기` 버튼
- 짧게 접힌 답변 말풍선과 `전체 보기`/`접기`
- 추천 관광지 카드, `더 보기`, 출처 표시
- 카드별 `상세 정보` 펼침과 `지도 검색`

한국관광공사 열린관광 사이트의 상세 URL은 현재 콘텐츠 ID만으로 안정적인 공개 상세 링크를 만들 수 없어, 잘못된 `access.visitkorea.or.kr/detail/...` 링크는 노출하지 않는다. 대신 카드 내부 상세 정보와 장소명/주소 기반 지도 검색을 제공한다.

## 실행

서버류 실행 원칙:

- `uvicorn`, `cloudflared`, `python3 -m http.server` 같은 장시간 실행 프로세스는 Codex 백그라운드 세션으로 조용히 띄우지 않는다.
- VS Code/Cursor 등 에디터의 새 터미널을 열고 사용자가 로그와 종료 상태를 볼 수 있게 실행한다.
- 터미널은 FastAPI용, 터널용처럼 역할별로 분리한다.

권장 실행:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

브라우저에서 `http://127.0.0.1:8000/tourism-ui/`를 연다.

FastAPI가 `frontend/web`을 `/tourism-ui/`로 같이 서빙하므로 외부 터널링도 8000번 포트 하나만 열면 된다.
화면 상단의 API 영역에는 Swagger 문서(`/docs`), ReDoc(`/redoc`), OpenAPI JSON(`/openapi.json`) 바로가기가 있다.

정적 파일 서버로 따로 확인하고 싶을 때:

```bash
cd frontend/web
python3 -m http.server 5173
```

브라우저에서 `http://127.0.0.1:5173`을 연다.

로컬 정적 서버에서 열면 기본 API 주소는 `http://127.0.0.1:8000`이다. `/tourism-ui/`나 터널 URL에서 열면 현재 origin을 API 주소로 자동 사용한다. 서버 포트를 바꿨다면 화면 상단의 API 입력값만 수정한다.

## 외부 임시 확인

Mac mini에서 FastAPI를 먼저 실행한다.

FastAPI와 Cloudflare는 같은 명령이 아니다. 터미널을 2개 열어 각각 실행한다.

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

출력되는 `https://...trycloudflare.com` 주소 뒤에 `/tourism-ui/`를 붙여 외부에서 연다.

```text
https://...trycloudflare.com/tourism-ui/
```

Quick Tunnel은 임시 확인용이다. 시연이 끝나면 `cloudflared`와 `uvicorn`을 종료한다.

## 확인할 것

- 강남구 휠체어 추천이 카드로 보이는지 확인한다.
- 추천 카드 위 답변이 짧게 접히고, 길 때만 `전체 보기`가 보이는지 확인한다.
- 각 카드에서 `상세 정보`를 눌렀을 때 주차, 화장실, 휠체어, 유아차 등 원 편의정보가 펼쳐지는지 확인한다.
- `지도 검색`이 장소명과 주소 기반 검색으로 열리는지 확인한다.
- 깨진 `access.visitkorea.or.kr/detail/...` 원문 링크가 카드에 노출되지 않는지 확인한다.
- 상태 표시가 `Live 캐시 응답`, `Live API 응답`, `색인 응답`, `샘플 fallback`, `지역 선택 필요`를 구분하는지 확인한다.
- "근처" 질문에서 상위 지역 확장 결과가 보이는지 확인한다.
- 화면이 대시보드가 아니라 메신저형 채팅 흐름으로 보이는지 확인한다.
- Help 버튼이 사용법, 테스트 범위, 유의점을 모달로 보여주는지 확인한다.
- `중구`처럼 여러 시도에 있는 지명은 추천 카드 대신 지역 선택 후속 버튼을 보여주는지 확인한다.
- `중구에서 휠체어 타시는 아버지와 갈 관광지 추천`은 “어느 지역인지” 추가 질문과 원래 질문 맥락을 유지한 서울/인천/대전/대구/부산/울산 중구 버튼을 보여주는지 확인한다.
- `부산 중구`처럼 광역 지역을 함께 선택하거나 입력하면 해당 시군구 카드만 보이는지 확인한다.
- `해운대 좌동`, `창원 마산합포구`처럼 법정동/행정동/일반구가 섞인 질문이 시군구 후보로 해석되는지 확인한다.
- `degraded=true`일 때 fallback 진단 문구가 보이는지 확인한다.
- 빈 입력, API 연결 실패, 백엔드 오류가 화면에서 구분되는지 확인한다.
