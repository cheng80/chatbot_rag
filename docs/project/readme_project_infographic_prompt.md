# README 인포그래픽 재생성 프롬프트

이 문서는 `README.md`의 내용을 바탕으로 README 상단용 프로젝트 인포그래픽을 다시 만들 때 쓰는 독립 프롬프트다.

프롬프트는 두 단계로 나뉜다.

- 1단계: `README.md`를 읽고 정확한 HTML 인포그래픽 원본을 만든다.
- 2단계: 완성된 HTML을 참고 자료로 삼아 AI 이미지 생성 도구에서 bitmap 인포그래픽을 만든다.

공식 문서에 넣을 최종 산출물은 텍스트 정확도가 높은 HTML 렌더 PNG를 우선한다. AI 생성 이미지는 시각 스타일 탐색이나 보조 이미지로 쓴다.

## 1. HTML 생성용 프롬프트

아래 프롬프트는 코드 생성 도구에 넣어 `README.md` 기반 HTML 인포그래픽을 만들 때 쓴다.

```text
프로젝트의 `README.md`를 읽고, README 상단에 넣을 프로젝트 요약 인포그래픽 HTML을 만들어줘.

출력 파일:

- `docs/project/readme_project_infographic.html`

목표:

- README 내용을 한 장짜리 기술 인포그래픽으로 요약한다.
- 이 프로젝트가 무엇인지, 어떻게 동작하는지, 어떤 데이터와 모델을 쓰는지, 현재 검증 상태와 운영 정책이 무엇인지 한눈에 보여준다.
- README의 설치·실행 명령을 그대로 길게 옮기지 말고, 프로젝트 이해에 필요한 구조와 정책을 시각화한다.

소스 기준:

- 사실, 숫자, 모델명, 경로, 정책은 반드시 `README.md`에서 먼저 가져온다.
- README에서 최신 상태가 모호하면 `docs/project/progress_overview.md`를 보조로 확인한다.
- README와 보조 문서가 충돌하면 README 본문을 우선하고, 확신 없는 수치는 넣지 않는다.
- 존재하지 않는 수치, 모델명, API명, 관광지 이름을 만들지 않는다.

HTML 요구사항:

- self-contained HTML/CSS 하나로 만든다.
- 외부 폰트, 외부 이미지, CDN을 쓰지 않는다.
- 1600px 폭 포스터로 만든다.
- PNG 렌더링을 전제로 텍스트와 레이아웃이 고정적으로 보이게 한다.
- 모든 텍스트는 실제 HTML 텍스트로 넣는다.
- 한국어 줄바꿈이 자연스럽게 보이도록 `word-break: keep-all`과 `overflow-wrap: break-word`를 사용한다.
- 텍스트가 카드 밖으로 넘치거나 겹치지 않게 font-size, grid, min-height를 안정적으로 잡는다.
- machine-specific absolute path나 임시 로컬 경로를 넣지 않는다.

시각 스타일:

- 따뜻한 크림색 종이 배경
- 얇은 검은 선
- muted green, teal, blue, yellow, red, violet 포인트 색
- 정돈된 technical infographic poster
- 카드 radius는 8px 안팎
- 섹션은 명확하되 화면 UI mockup처럼 보이지 않게 한다.
- 장식용 blob, 진한 gradient, stock photo 느낌을 피한다.
- README에서 축소되어도 제목, 큰 숫자, 흐름이 읽혀야 한다.

필수 상단 구성:

- 배지: `README VISUAL BRIEF`
- 제목: `무장애·가족 친화 관광 챗봇`
- 한 줄 설명: README 첫 문단을 요약해, 한국관광공사 OpenAPI와 로컬 RAG 검색 자료를 함께 쓰는 로컬 실행형 관광 챗봇임을 보여준다.
- 오른쪽에는 현재 상태 요약 패널을 둔다.

현재 상태 요약 패널:

README 또는 `docs/project/progress_overview.md`의 최신 진행도 숫자를 사용한다.
현재 값이 유지된다면 아래 항목을 쓴다.

- 시제품 84%
- 서버 기능 92%
- 웹 화면 90%
- 자동 검증 90%
- 정식 운영 20%

필수 섹션 1: `사용자 질문이 추천 카드가 되는 흐름`

README의 관광 챗봇 흐름을 8단계 안팎의 가로 플로우로 요약한다.

권장 단계:

1. 자연어 질문
2. 질문 해석
3. 대화 기억
4. 저장 기록 확인
5. 저장 문서 검색
6. 부족할 때 TourAPI 조회
7. 카드 형식 정리
8. 응답 반환

각 단계는 다음 형식으로 만든다.

- 큰 단계명
- 한 줄 설명
- 작은 기술 라벨

예시 기술 라벨:

- `/tourism/chat`
- 규칙 + 보조 분류기
- 대화 ID
- 저장 캐시
- 벡터 검색 top_k=40
- TourAPI
- 추천 카드
- 근거 우선

필수 섹션 2: `시스템 레이어`

README의 주요 요청 경로와 기술 구성을 바탕으로 3개 레이어를 만든다.

- 사용자 화면
  - `/tourism-ui/`
  - Flutter 앱은 별도 repo
  - 추천 카드, 상세 정보, 지도 검색

- 백엔드 기능
  - FastAPI
  - `/tourism/chat`
  - `/chat`
  - `/documents/reindex`
  - 응답에는 카드, 출처, 경고, 조회 경로가 포함됨

- AI와 판단 규칙
  - Ollama SuperGemma4
  - bge-m3
  - ET5 + 정규화 규칙
  - 규칙 + n-gram 보조 분류기
  - LLM reasoning assist 기본 OFF

필수 섹션 3: `데이터 파이프라인`

README의 관광 시제품 데이터와 정책을 요약한다.

포함할 항목:

- 한국관광공사 OpenAPI
- 저장 캐시
- 예비 관광 Markdown
- Chroma 검색 색인
- SQLite raw response cache

README 기준 최신 수치가 유지된다면 아래 숫자를 쓴다.

- 904개 Markdown
- 905개 문서
- 914개 조각
- 228/234 시군구 3장 이상 fallback 확보

필수 섹션 4: `품질 게이트`

README의 자동 회귀·벤치마크 요약을 큰 숫자로 보여준다.

README 기준 최신 수치가 유지된다면 아래 내용을 쓴다.

- TOP_K=40 challenge 30건 실패 0
- TOP_K=40 residual hard chat 80건 실패 0
- noisy realistic 200건 direct 실행 후 남은 실패 28
- LLM reasoning assist 20문항 eval: OFF, SuperGemma4, Gemma3, Gemma4 모두 20/20 통과

표현은 짧게 줄여도 된다.

필수 섹션 5: `현재 운영 정책`

README의 관광 시제품 데이터와 정책에서 핵심 정책을 뽑아 카드로 만든다.

반드시 포함할 정책:

- 근거 없는 접근성 정보 생성 금지
- 캐시/RAG 우선, 부족할 때만 TourAPI live 조회
- 저장된 후보가 적으면 자동 조회보다 `최신 정보 더 찾기` 제안
- 운영 검색은 Chroma vector-only `TOP_K=40`
- AutoRAG는 retrieval-only 오프라인 실험 도구
- 시군구 자동 확장 금지
- 관계 호칭만으로 나이 추정 금지
- LLM reasoning assist 기본 OFF

필수 섹션 6: `핵심 폴더 지도`

README의 폴더 구조를 짧은 path chip으로 요약한다.

추천 path:

- `app/`
- `app/api/routes/`
- `app/services/`
- `app/repositories/`
- `app/schemas/`
- `frontend/web/`
- `data/raw/tourism_accessible/`
- `data/processed/`
- `data/eval/`
- `scripts/`
- `tests/`
- `docs/project/`
- `docs/tourism/`

필수 섹션 7: `실행·확인 입구`

README의 실행 방법을 긴 명령 대신 입구 중심으로 요약한다.

포함할 항목:

- 서버: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
- 웹 UI: `http://127.0.0.1:8000/tourism-ui/`
- API 문서: `/docs`, `/redoc`
- 관광 API: `POST /tourism/chat`
- 일반 RAG: `POST /chat`

footer:

- `근거 문서: README.md`
- `이 이미지는 README 이해를 돕는 시각 요약이다. 실행 절차와 최신 명령은 README 본문을 우선한다.`

텍스트 제한:

- 한 카드 안의 설명은 1-2줄을 넘기지 않는다.
- 긴 문장을 그대로 붙이지 않는다.
- 설치 명령 전체를 포스터 안에 많이 넣지 않는다.
- 세부 API명 `areaBasedList2`, `detailCommon2`, `detailWithTour2`는 넣지 않는다.
- 세부 latency 숫자는 넣지 않는다.

검증:

- 완성 뒤 `git diff --check`가 통과해야 한다.
- HTML 안에 machine-specific absolute path나 임시 로컬 경로가 없어야 한다.
- PNG 렌더링 시 텍스트가 겹치거나 잘리지 않아야 한다.
```

## 2. HTML 참조 이미지 생성용 프롬프트

아래 프롬프트는 완성된 `docs/project/readme_project_infographic.html`을 이미지 생성 도구에 참고 자료로 넣고, 별도의 bitmap 인포그래픽 이미지를 만들 때 쓴다.

```text
첨부한 README 인포그래픽 HTML을 참고해서 README용 프로젝트 인포그래픽 이미지를 새로 그려줘.

중요:

- HTML을 그대로 렌더링하거나 웹페이지 스크린샷처럼 만들지 마.
- HTML의 정보 구조, 색감, 섹션 구성, 핵심 문구만 참고해서 새 technical infographic poster로 재해석해.
- 이 이미지는 README 첫 화면용 프로젝트 요약 이미지다.
- 텍스트는 크고 짧게 유지해.
- 한국어 텍스트는 또렷하고 자연스러워야 한다.
- 랜덤 더미 텍스트, 존재하지 않는 기술명, 존재하지 않는 숫자는 넣지 마.

반드시 보이는 큰 요소:

- 제목: `무장애·가족 친화 관광 챗봇`
- 배지: `README VISUAL BRIEF`
- 핵심 흐름: `질문 → 해석 → 저장 자료 검색 → 부족할 때 TourAPI → 추천 카드`
- 핵심 정책: `근거 없는 접근성 정보 생성 금지`

스타일:

- 세로형 고해상도 technical infographic poster
- 따뜻한 크림색 종이 배경
- 얇은 검은 선
- muted green, teal, blue, yellow, red, violet 포인트 색
- 정리된 whiteboard explainer 느낌
- README 대표 이미지 느낌
- 카드와 섹션이 명확하지만, 웹페이지 스크린샷처럼 보이지 않게 해

내용 구성:

1. 상단:
   - 큰 제목
   - 짧은 설명
   - 진행도 mini panel

2. 중앙:
   - 사용자 질문이 추천 카드가 되는 흐름
   - 단계명은 짧게:
     - 자연어 질문
     - 질문 해석
     - 대화 기억
     - 저장 기록
     - 문서 검색
     - TourAPI 보강
     - 카드 생성
     - 응답 반환

3. 하단:
   - 시스템 레이어: UI, FastAPI, AI/규칙
   - 데이터: 904개 Markdown, Chroma, bge-m3, SQLite cache
   - 품질: 30건 실패 0, 80건 실패 0, noisy 잔여 28
   - 운영 정책: 근거 생성 금지, 부족할 때만 live 조회, reasoning assist OFF

표시해도 되는 대표 숫자:

- 84% 시제품
- 92% 서버 기능
- 90% 웹 화면
- 90% 자동 검증
- 20% 정식 운영
- 904개 Markdown
- 905개 문서
- 914개 조각
- 228/234
- top_k=40
- 30건 실패 0
- 80건 실패 0
- 20/20
- 28

표시해도 되는 기술명:

- FastAPI
- `/tourism/chat`
- Chroma
- bge-m3
- TourAPI
- SQLite
- Ollama SuperGemma4

피해야 할 것:

- 세부 API명 `areaBasedList2`, `detailCommon2`, `detailWithTour2`
- 세부 latency 숫자
- AutoRAG를 운영 엔진처럼 크게 표시하는 것
- LLM 보조가 기본 ON인 것처럼 보이는 구성
- 실제 관광지 이름을 임의로 만드는 것
- 웹 UI screenshot처럼 보이는 결과
- 작은 텍스트가 빽빽한 표
- 진한 gradient, 장식용 blob, stock image 느낌

정확성 규칙:

- 운영 검색은 `Chroma vector-only + top_k=40`으로 표현해.
- AutoRAG는 필요하면 오프라인 비교 도구로만 작게 표현해.
- LLM 보조는 `기본 OFF` 또는 `선택 사항`으로 표현해.
- TourAPI는 매번 호출이 아니라 `부족할 때 보강`으로 표현해.
- 접근성 정보는 근거가 있을 때만 쓴다는 정책을 강조해.

최종 느낌:

README 첫 화면용 대표 이미지.
기술자는 구조를 이해하고, 비개발자는 “근거 있는 관광 추천 카드 챗봇”이라는 목적을 이해해야 한다.
정보는 정확하지만 모든 문서를 한 장에 욱여넣지 말고, 큰 흐름과 대표 숫자만 보여줘.
```

## 3. 렌더링 명령

HTML 원본을 PNG로 렌더링할 때는 프로젝트 루트에서 실행한다.

```bash
HTML_URL="$(python - <<'PY'
from pathlib import Path
print(Path('docs/project/readme_project_infographic.html').resolve().as_uri())
PY
)"
npx -y playwright screenshot --full-page --viewport-size=1600,2400 "$HTML_URL" docs/project/readme_project_infographic.png
```

## 4. 점검 기준

- `README.md`의 내용이 원천이다.
- 제목과 핵심 흐름이 첫눈에 보인다.
- TourAPI가 매번 호출되는 것처럼 보이지 않는다.
- LLM 보조가 기본 ON처럼 보이지 않는다.
- 대표 숫자가 README와 맞다.
- 텍스트가 겹치거나 잘리지 않는다.
- repo-relative path만 쓴다.
