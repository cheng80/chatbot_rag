# Portfolio Screenshots

김택권 포트폴리오에서 FastAPI 기반 관광 챗봇 API와 AI/RAG 백엔드 동작 근거로 사용할 캡처입니다.

이 화면들은 로컬 데모/테스트 실행 결과입니다. 운영 사용자 수, 운영 성과, 상용 트래픽 실적을 나타내지 않습니다. 캡처는 API 키 노출을 피하기 위해 `TOURISM_LIVE_LOOKUP_ENABLED=false` 상태에서 준비된 관광 샘플/캐시 자료로 생성했습니다.

## Files

- `chatbot-rag-hero-response.png` — `hero`
  - 포트폴리오 메인 이미지입니다.
  - 실제 `/tourism-ui/` 화면에서 `서울 강남구에서 휠체어 관광지 추천해줘` 질문을 보낸 뒤의 응답입니다.
  - 질문, 답변, 추천 카드, 출처/근거, 준비 자료 응답 상태가 한 화면에 보입니다.

- `chatbot-rag-proof-api.png` — `proof`
  - Swagger/OpenAPI 보조 증거 이미지입니다.
  - `/tourism/chat` 관광 챗봇 엔드포인트가 보이도록 캡처했습니다.

- `chatbot-rag-proof-response-json.png` — `proof`
  - 실제 `POST /tourism/chat` 응답을 포트폴리오 보조 이미지용으로 요약한 JSON 화면입니다.
  - `lookup_mode`, `card_count`, `source_count`, `sources`, 추천 카드 제목 일부를 표시합니다.
  - 캡처 시점 응답은 `lookup_mode: sample`, 카드 5개, 출처 5개입니다.

- `chatbot-rag-proof-code-or-test.png` — `optional`
  - 실제 구현/테스트 근거가 필요할 때만 사용하는 선택 이미지입니다.
  - `app/services/tourism_chat_service.py` 발췌와 `tests/test_tourism_api.py` 통과 결과를 함께 보여줍니다.

## Verification Notes

- 캡처 전 FastAPI 서버를 로컬에서 실행하고 `/health`, `/openapi.json`, `/tourism/chat`를 실제 HTTP 요청으로 확인했습니다.
- 데모 UI는 브라우저에서 실제 질문 제출 후 응답 카드가 렌더링된 상태를 캡처했습니다.
- `tests/test_tourism_api.py -q`는 4개 테스트 통과를 확인했습니다.
- 스크린샷에는 API 키, `.env` 값, 개인 토큰, 운영 트래픽 수치를 넣지 않았습니다.
- 관광 정보는 방문 전 공식 안내, 전화, 현장 정보로 재확인해야 하며 화면에도 같은 주의 문구가 표시됩니다.
