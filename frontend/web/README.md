# Web Frontend

`/tourism/chat` 백엔드 응답을 눈으로 확인하기 위한 정적 웹 UI다.
빌드 도구 없이 HTML/CSS/JS만 사용한다.

## 실행

권장 실행:

```bash
.venv/bin/uvicorn app.main:app --reload
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

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

다른 터미널에서 Cloudflare Quick Tunnel을 실행한다.

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
- "근처" 질문에서 상위 지역 확장 결과가 보이는지 확인한다.
- 현재 테스트 지역 안내가 서울/부산/강릉과 주요 시군구를 보여주는지 확인한다.
- Help 버튼이 사용법, 테스트 범위, 유의점을 모달로 보여주는지 확인한다.
- `중구`처럼 여러 시도에 있는 지명은 추천 카드 대신 지역 선택 후속 버튼을 보여주는지 확인한다.
- `부산 중구`처럼 광역 지역을 함께 선택하거나 입력하면 해당 시군구 카드만 보이는지 확인한다.
- `degraded=true`일 때 fallback 진단 문구가 보이는지 확인한다.
- 빈 입력, API 연결 실패, 백엔드 오류가 화면에서 구분되는지 확인한다.
