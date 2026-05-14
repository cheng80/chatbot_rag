from pathlib import Path

from app.core.config import Settings
from app.services.tourism_chat_service import TourismChatService
from app.services.tourism_query_service import TourismQueryService


class FakeRetriever:
    def retrieve(self, message: str):
        return [
            {
                "id": "chunk-1",
                "text": Path("data/raw/tourism_accessible/seoul_sample_001.md").read_text(encoding="utf-8"),
                "metadata": {"source": "data/raw/tourism_accessible/seoul_sample_001.md", "chunk_index": 0},
                "distance": 0.1,
            },
            {
                "id": "chunk-2",
                "text": Path("data/raw/tourism_accessible/seoul_sample_002.md").read_text(encoding="utf-8"),
                "metadata": {"source": "data/raw/tourism_accessible/seoul_sample_002.md", "chunk_index": 0},
                "distance": 0.2,
            },
            {
                "id": "chunk-3",
                "text": Path("data/raw/tourism_accessible/busan_sample_001.md").read_text(encoding="utf-8"),
                "metadata": {"source": "data/raw/tourism_accessible/busan_sample_001.md", "chunk_index": 0},
                "distance": 0.3,
            },
        ]


def test_tourism_chat_returns_cards_and_sources():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("서울에서 휠체어와 유모차로 가기 좋은 곳 추천해줘")

    assert len(response.cards) == 2
    assert response.cards[0].title == "서울어린이대공원"
    assert response.sources[0].source == "data/raw/tourism_accessible/seoul_sample_001.md"
    assert all("seoul" in source.source for source in response.sources)
    assert "출처" in response.answer


def test_tourism_chat_falls_back_to_local_samples(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    sample = Path("data/raw/tourism_accessible/gangneung_sample_001.md").read_text(encoding="utf-8")
    (sample_dir / "gangneung.md").write_text(sample, encoding="utf-8")

    class BrokenRetriever:
        def retrieve(self, message: str):
            raise RuntimeError("Ollama unavailable")

    service = TourismChatService(
        Settings(tourism_sample_path=sample_dir, tour_api_service_key=None),
        BrokenRetriever(),
        TourismQueryService(),
    )

    response = service.answer("강릉 부모님과 갈만한 무장애 관광지")

    assert len(response.cards) == 1
    assert response.cards[0].title == "오죽헌"
    assert response.sources[0].chunk_id == "sample-gangneung-001"


def test_tourism_chat_does_not_expand_sigungu_without_intent():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("광진구에서 휠체어로 갈만한 곳 추천")

    assert len(response.cards) == 1
    assert response.cards[0].title == "서울어린이대공원"
    assert "요청 지역 안의 결과만 먼저 제공합니다" in response.answer


def test_tourism_chat_expands_sigungu_when_user_asks_nearby():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("광진구 근처에서 휠체어로 갈만한 곳 추천")

    assert 2 <= len(response.cards) <= 5
    assert response.cards[0].title == "서울어린이대공원"
    assert any("서울" in (card.address or "") for card in response.cards)
    assert "서울 범위 후보를 함께 포함했습니다" in response.answer
