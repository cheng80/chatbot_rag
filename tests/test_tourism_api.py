from fastapi.testclient import TestClient

from app.api.deps import get_tourism_chat_service
from app.main import app
from app.schemas.tourism import TourismChatResponse, TourismPlaceCard


class FakeTourismChatService:
    def answer(self, message: str, session_id: str | None = None):
        return TourismChatResponse(
            answer="서울 기준으로 1곳을 추천합니다.",
            cards=[
                TourismPlaceCard(
                    content_id="sample",
                    title="테스트 관광지",
                    recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
                    accessibility_tags=["휠체어 접근"],
                    family_tags=["가족 친화"],
                )
            ],
            sources=[],
        )


def test_tourism_chat_api_smoke():
    app.dependency_overrides[get_tourism_chat_service] = lambda: FakeTourismChatService()
    client = TestClient(app)

    response = client.post("/tourism/chat", json={"message": "서울 휠체어 관광지 추천"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["cards"][0]["title"] == "테스트 관광지"
    assert data["cards"][0]["accessibility_tags"] == ["휠체어 접근"]
