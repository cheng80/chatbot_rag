from pathlib import Path
import json

from app.core.config import Settings
from app.schemas.tourism import TourismPlaceCard
from app.services.tour_api_service import TourAPIError
from app.services.tourism_chat_service import TourismChatService
from app.services.tourism_normalizer import TourismNormalizer
from app.services.tourism_query_event_logger import TourismQueryEventLogger
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


class EmptyRetriever:
    def retrieve(self, message: str):
        return []


class FakeLLMService:
    def __init__(self, response: str):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


def test_tourism_chat_returns_cards_and_sources():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("서울에서 휠체어와 유모차로 가기 좋은 곳 추천해줘")

    assert len(response.cards) == 2
    assert response.cards[0].title == "서울어린이대공원"
    assert response.lookup_mode == "indexed"
    assert response.sources[0].source == "data/raw/tourism_accessible/seoul_sample_001.md"
    assert all("seoul" in source.source for source in response.sources)
    assert "출처" in response.answer


def test_tourism_chat_uses_reasoning_assist_for_complex_question():
    llm = FakeLLMService(
        '{"ranked_ids":["sample-seoul-002","sample-seoul-001"],'
        '"missing_or_uncertain":["혼잡도는 확인 필요"]}'
    )
    service = TourismChatService(
        Settings(tourism_reasoning_assist_enabled=True),
        FakeRetriever(),
        TourismQueryService(),
        llm_service=llm,
    )

    response = service.answer("서울에서 휠체어 타는 아버지와 아이가 비 오면 이동하기 편한 실내 관광지 추천")

    assert response.reasoning_assist_used is True
    assert response.reasoning_assist_notes == ["혼잡도는 확인 필요"]
    assert response.cards[0].title == "국립중앙박물관"
    assert "복합 조건을 반영해 후보 순서를 조정했습니다" in response.answer
    assert "후보 카드에 없는 장소나 접근성 정보를 만들지 않는다" in llm.prompts[0]


def test_tourism_chat_disables_reasoning_assist_by_default():
    llm = FakeLLMService(
        '{"ranked_ids":["sample-seoul-002","sample-seoul-001"],'
        '"missing_or_uncertain":["혼잡도는 확인 필요"]}'
    )
    service = TourismChatService(
        Settings(),
        FakeRetriever(),
        TourismQueryService(),
        llm_service=llm,
    )

    response = service.answer("서울에서 휠체어 타는 아버지와 아이가 비 오면 이동하기 편한 실내 관광지 추천")

    assert response.reasoning_assist_used is False
    assert response.reasoning_assist_notes == []
    assert response.cards[0].title == "서울어린이대공원"
    assert llm.prompts == []


def test_tourism_chat_skips_reasoning_assist_for_simple_question():
    llm = FakeLLMService('{"ranked_ids":["sample-seoul-002"]}')
    service = TourismChatService(
        Settings(tourism_reasoning_assist_enabled=True),
        FakeRetriever(),
        TourismQueryService(),
        llm_service=llm,
    )

    response = service.answer("서울에서 휠체어 관광지 추천")

    assert response.reasoning_assist_used is False
    assert response.cards[0].title == "서울어린이대공원"
    assert llm.prompts == []


def test_tourism_chat_keeps_existing_order_when_reasoning_assist_fails():
    llm = FakeLLMService("not-json")
    service = TourismChatService(
        Settings(tourism_reasoning_assist_enabled=True),
        FakeRetriever(),
        TourismQueryService(),
        llm_service=llm,
    )

    response = service.answer("서울에서 휠체어 타는 아버지와 아이가 비 오면 이동하기 편한 실내 관광지 추천")

    assert response.reasoning_assist_used is False
    assert response.cards[0].title == "서울어린이대공원"


def test_tourism_chat_prefers_live_tour_api_when_available(tmp_path):
    class FakeTourAPI:
        def __init__(self):
            self.list_calls = 0
            self.detail_common_calls = 0
            self.detail_with_tour_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": "live-1"}, {"contentid": "live-2"}]

        def detail_common(self, content_id: str):
            self.detail_common_calls += 1
            return {
                "contentid": content_id,
                "title": f"Live 관광지 {content_id}",
                "addr1": "서울 중구",
            }

        def detail_with_tour(self, content_id: str):
            self.detail_with_tour_calls += 1
            return {"contentid": content_id, "wheelchair": "주 출입구 휠체어 접근 가능"}

    tour_api = FakeTourAPI()
    service = TourismChatService(
        Settings(
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_rows=2,
            tourism_live_max_detail_calls=4,
            tourism_live_cache_path=tmp_path / "live_cache",
            tourism_sample_path=tmp_path / "samples",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("서울에서 휠체어 관광지 추천")

    assert [card.content_id for card in response.cards] == ["live-1", "live-2"]
    assert response.lookup_mode == "live"
    assert response.degraded is False
    assert response.sources[0].source == "한국관광공사 무장애 여행 정보 OpenAPI"
    assert tour_api.list_calls == 1
    assert tour_api.detail_common_calls == 2
    assert tour_api.detail_with_tour_calls == 2


def test_tourism_chat_uses_indexed_cards_before_live_tour_api(tmp_path):
    class CountingTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": "should-not-call"}]

    tour_api = CountingTourAPI()
    service = TourismChatService(
        Settings(
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_cache_path=tmp_path / "live_cache",
            tourism_sample_path=tmp_path / "samples",
        ),
        FakeRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("서울에서 휠체어 관광지 추천")

    assert response.lookup_mode == "indexed"
    assert response.cards[0].title == "서울어린이대공원"
    assert tour_api.list_calls == 0


def test_tourism_chat_caches_live_tour_api_region_results(tmp_path):
    class FakeTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": "live-cache"}]

        def detail_common(self, content_id: str):
            return {"contentid": content_id, "title": "Live 캐시 관광지", "addr1": "서울 중구"}

        def detail_with_tour(self, content_id: str):
            return {"contentid": content_id, "wheelchair": "휠체어 접근 가능"}

    tour_api = FakeTourAPI()
    service = TourismChatService(
        Settings(
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_cache_path=tmp_path / "live_cache",
            tourism_sample_path=tmp_path / "samples",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    assert service.answer("서울 휠체어 관광지").cards[0].title == "Live 캐시 관광지"
    assert service.answer("서울 유모차 관광지").cards[0].title == "Live 캐시 관광지"
    assert tour_api.list_calls == 1


def test_tourism_chat_reads_persisted_live_markdown_before_api_call(tmp_path):
    live_cache_dir = tmp_path / "live_cache"
    live_cache_dir.mkdir()
    card = TourismPlaceCard(
        content_id="persisted-live",
        title="저장된 라이브 관광지",
        address="서울 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    (live_cache_dir / "서울_persisted-live.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")

    class CountingTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": "should-not-call"}]

    tour_api = CountingTourAPI()
    service = TourismChatService(
        Settings(
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_cache_path=live_cache_dir,
            tourism_sample_path=tmp_path / "samples",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("서울에서 휠체어 관광지 추천")

    assert response.cards[0].title == "저장된 라이브 관광지"
    assert response.lookup_mode == "cache"
    assert tour_api.list_calls == 0


def test_tourism_chat_persists_live_tour_api_cards_to_markdown(tmp_path):
    live_cache_dir = tmp_path / "live_cache"

    class FakeTourAPI:
        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            return [{"contentid": "live-persist"}]

        def detail_common(self, content_id: str):
            return {"contentid": content_id, "title": "저장 대상 관광지", "addr1": "서울 중구"}

        def detail_with_tour(self, content_id: str):
            return {"contentid": content_id, "wheelchair": "휠체어 접근 가능"}

    service = TourismChatService(
        Settings(
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_cache_path=live_cache_dir,
            tourism_sample_path=tmp_path / "samples",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=FakeTourAPI(),
    )

    response = service.answer("서울에서 휠체어 관광지 추천")

    assert response.lookup_mode == "live"
    cached_files = list(live_cache_dir.glob("*.md"))
    assert len(cached_files) == 1
    assert "저장 대상 관광지" in cached_files[0].read_text(encoding="utf-8")


def test_tourism_chat_logs_query_card_event(tmp_path):
    log_path = tmp_path / "events.jsonl"
    service = TourismChatService(
        Settings(
            tourism_query_event_log_path=log_path,
            tourism_query_event_log_enabled=True,
            tourism_query_event_log_include_message=False,
            tour_api_service_key=None,
        ),
        FakeRetriever(),
        TourismQueryService(),
        event_logger=TourismQueryEventLogger(
            Settings(
                tourism_query_event_log_path=log_path,
                tourism_query_event_log_enabled=True,
                tourism_query_event_log_include_message=False,
            )
        ),
    )

    response = service.answer("서울에서 휠체어 관광지 추천", session_id="test-session")

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert response.lookup_mode == "indexed"
    assert payload["session_id"] == "test-session"
    assert payload["message"] is None
    assert payload["lookup_mode"] == "indexed"
    assert payload["live_api_called"] is False
    assert payload["reasoning_assist_used"] is False
    assert payload["reasoning_assist_notes"] == []
    assert payload["cards"][0]["title"] == "서울어린이대공원"


def test_tourism_chat_uses_local_samples_before_live_tour_api(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    sample = Path("data/raw/tourism_accessible/gangneung_sample_001.md").read_text(encoding="utf-8")
    (sample_dir / "gangneung.md").write_text(sample, encoding="utf-8")

    class BrokenTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            raise TourAPIError("quota exhausted")

    tour_api = BrokenTourAPI()
    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("강릉 휠체어 관광지")

    assert len(response.cards) == 1
    assert response.cards[0].title == "오죽헌"
    assert response.lookup_mode == "sample"
    assert response.degraded is False
    assert response.warnings == []
    assert tour_api.list_calls == 0


def test_tourism_chat_suggests_live_top_up_when_fallback_has_less_than_five_cards(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    for index in range(3):
        card = TourismPlaceCard(
            content_id=f"jeju-fallback-{index}",
            title=f"제주 폴백 관광지 {index}",
            address="제주특별자치도 제주시",
            recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
            accessibility_tags=["휠체어 접근"],
        )
        (sample_dir / f"jeju_{index}.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")

    class CountingTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": "live-extra"}]

    tour_api = CountingTourAPI()
    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("제주시에서 휠체어 관광지 추천해줘")

    assert len(response.cards) == 3
    assert tour_api.list_calls == 0
    assert response.suggested_messages == ["제주시에서 휠체어 관광지 추천해줘 최신 정보 더 찾기"]


def test_tourism_chat_live_top_up_runs_only_when_user_requests_it(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    for index in range(3):
        card = TourismPlaceCard(
            content_id=f"jeju-fallback-topup-{index}",
            title=f"제주 폴백 보강 관광지 {index}",
            address="제주특별자치도 제주시",
            recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
            accessibility_tags=["휠체어 접근"],
        )
        (sample_dir / f"jeju_{index}.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")

    class FakeTourAPI:
        def __init__(self):
            self.list_calls = 0

        def accessible_area_based_list(self, area_code: str, sigungu_code=None, num_of_rows=10):
            self.list_calls += 1
            return [{"contentid": f"jeju-live-{index}"} for index in range(5)]

        def detail_common(self, content_id: str):
            return {
                "contentid": content_id,
                "title": f"제주 라이브 관광지 {content_id}",
                "addr1": "제주특별자치도 제주시",
            }

        def detail_with_tour(self, content_id: str):
            return {"contentid": content_id, "wheelchair": "휠체어 접근 가능"}

    tour_api = FakeTourAPI()
    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key="test",
            tour_api_accessible_service_key="test",
            tourism_live_rows=5,
            tourism_live_max_detail_calls=10,
        ),
        EmptyRetriever(),
        TourismQueryService(),
        tour_api_service=tour_api,
    )

    response = service.answer("제주시에서 휠체어 관광지 추천해줘 최신 정보 더 찾기")

    assert response.lookup_mode == "live_top_up"
    assert len(response.cards) == 5
    assert any(card.content_id.startswith("jeju-live-") for card in response.cards)
    assert response.suggested_messages == ["제주시에서 휠체어 관광지 추천해줘 더 보기"]
    assert tour_api.list_calls == 1


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
    assert response.degraded is True
    assert "fallback" in response.warnings[0]


def test_tourism_chat_does_not_expand_sigungu_without_intent():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("광진구에서 휠체어로 갈만한 곳 추천")

    assert len(response.cards) == 1
    assert response.cards[0].title == "서울어린이대공원"
    assert "요청 지역 안의 결과만 먼저 제공합니다" in response.answer


def test_tourism_chat_expands_sigungu_when_user_asks_nearby(tmp_path):
    service = TourismChatService(
        Settings(tourism_live_cache_path=tmp_path / "live_cache"),
        FakeRetriever(),
        TourismQueryService(),
    )

    response = service.answer("광진구 근처에서 휠체어로 갈만한 곳 추천")

    assert 2 <= len(response.cards) <= 5
    assert response.cards[0].title == "서울어린이대공원"
    assert any("서울" in (card.address or "") for card in response.cards)
    assert "서울 범위 후보를 함께 포함했습니다" in response.answer


def test_tourism_chat_asks_to_clarify_ambiguous_region(tmp_path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "region_index": {
                    "서울": {
                        "area_code": "1",
                        "sigungu_code": None,
                        "area_name": "서울",
                        "sigungu_name": None,
                    },
                    "부산": {
                        "area_code": "6",
                        "sigungu_code": None,
                        "area_name": "부산",
                        "sigungu_name": None,
                    },
                },
                "ambiguous_region_aliases": {
                    "중구": [
                        {
                            "area_code": "1",
                            "sigungu_code": "24",
                            "area_name": "서울",
                            "sigungu_name": "중구",
                        },
                        {
                            "area_code": "6",
                            "sigungu_code": "15",
                            "area_name": "부산",
                            "sigungu_name": "중구",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService(area_code_cache_path=cache_path))

    response = service.answer("중구에서 휠체어 타시는 아버지와 갈 관광지 추천")

    assert response.cards == []
    assert response.lookup_mode == "clarification"
    assert "'중구'는 여러 시도에 있는 지명" in response.answer
    assert "어느 지역인지" in response.answer
    assert "서울 중구" in response.answer
    assert "부산 중구" in response.answer
    assert response.suggested_messages == [
        "서울 중구에서 휠체어 타시는 아버지와 갈 관광지 추천",
        "부산 중구에서 휠체어 타시는 아버지와 갈 관광지 추천",
    ]


def test_tourism_chat_resolves_area_qualified_ambiguous_region(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    sample = Path("data/raw/tourism_accessible/부산_2609623.md").read_text(encoding="utf-8")
    (sample_dir / "busan_junggu.md").write_text(sample, encoding="utf-8")
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "region_index": {
                    "부산": {
                        "area_code": "6",
                        "sigungu_code": None,
                        "area_name": "부산",
                        "sigungu_name": None,
                    },
                },
                "ambiguous_region_aliases": {
                    "중구": [
                        {
                            "area_code": "1",
                            "sigungu_code": "24",
                            "area_name": "서울",
                            "sigungu_name": "중구",
                        },
                        {
                            "area_code": "6",
                            "sigungu_code": "15",
                            "area_name": "부산",
                            "sigungu_name": "중구",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    class EmptyRetriever:
        def retrieve(self, message: str):
            return []

    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key=None,
        ),
        EmptyRetriever(),
        TourismQueryService(area_code_cache_path=cache_path),
    )

    response = service.answer("부산 중구에서 휠체어 타시는 어머니를 모시고 다닐수 있는 관광지를 추천해줘")

    assert len(response.cards) == 1
    assert response.cards[0].title == "개미집 본점"
    assert "부산 중구 기준" in response.answer


def test_tourism_chat_filters_same_sigungu_name_by_area(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    busan_card = TourismPlaceCard(
        content_id="busan-junggu",
        title="부산 중구 관광지",
        address="부산광역시 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    ulsan_card = TourismPlaceCard(
        content_id="ulsan-junggu",
        title="울산중구어린이역사과학체험관",
        address="울산광역시 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    (sample_dir / "busan.md").write_text(TourismNormalizer().card_to_markdown(busan_card), encoding="utf-8")
    (sample_dir / "ulsan.md").write_text(TourismNormalizer().card_to_markdown(ulsan_card), encoding="utf-8")

    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key=None,
        ),
        EmptyRetriever(),
        TourismQueryService(),
    )

    response = service.answer("부산 중구에서 휠체어 관광지 추천해줘")

    assert [card.title for card in response.cards] == ["부산 중구 관광지"]


def test_tourism_chat_explains_legacy_region_name_replacement(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    card = TourismPlaceCard(
        content_id="legacy-cheongju",
        title="청주 무장애 관광지",
        address="충청북도 청주시 청원구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    (sample_dir / "cheongju.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "청원군": {
                        "area_code": "33",
                        "sigungu_code": "9",
                        "area_name": "충북",
                        "sigungu_name": "청원군",
                    },
                    "청주시": {
                        "area_code": "33",
                        "sigungu_code": "10",
                        "area_name": "충북",
                        "sigungu_name": "청주시",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismChatService(
        Settings(tourism_sample_path=sample_dir, tour_api_service_key=None),
        EmptyRetriever(),
        TourismQueryService(area_code_cache_path=cache_path),
    )

    response = service.answer("청원군에서 휠체어 관광지 추천해줘")

    assert len(response.cards) == 1
    assert response.cards[0].title == "청주 무장애 관광지"
    assert "청주시 기준" in response.answer
    assert "청원군은 현재 행정구역 기준 청주시" in response.answer


def test_tourism_chat_suggests_more_when_more_than_five_cards_exist(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    for index in range(6):
        card = TourismPlaceCard(
            content_id=f"jeju-more-{index}",
            title=f"제주 더보기 관광지 {index}",
            address="제주특별자치도 제주시",
            recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
            accessibility_tags=["휠체어 접근"],
        )
        (sample_dir / f"jeju_{index}.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")
    service = TourismChatService(
        Settings(tourism_sample_path=sample_dir, tourism_live_cache_path=tmp_path / "live_cache", tour_api_service_key=None),
        EmptyRetriever(),
        TourismQueryService(),
    )

    response = service.answer("제주시에서 휠체어 관광지 추천해줘")

    assert len(response.cards) == 5
    assert response.suggested_messages == ["제주시에서 휠체어 관광지 추천해줘 더 보기"]


def test_tourism_chat_returns_more_cards_when_more_is_requested(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    for index in range(6):
        card = TourismPlaceCard(
            content_id=f"jeju-more-requested-{index}",
            title=f"제주 전체 관광지 {index}",
            address="제주특별자치도 제주시",
            recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
            accessibility_tags=["휠체어 접근"],
        )
        (sample_dir / f"jeju_{index}.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")
    service = TourismChatService(
        Settings(tourism_sample_path=sample_dir, tourism_live_cache_path=tmp_path / "live_cache", tour_api_service_key=None),
        EmptyRetriever(),
        TourismQueryService(),
    )

    response = service.answer("제주시에서 휠체어 관광지 추천해줘 더 보기")

    assert len(response.cards) == 6
    assert response.suggested_messages == []


def test_tourism_chat_handles_empty_retrieval_and_empty_samples(tmp_path):
    sample_dir = tmp_path / "empty"
    sample_dir.mkdir()

    class EmptyRetriever:
        def retrieve(self, message: str):
            return []

    service = TourismChatService(
        Settings(tourism_sample_path=sample_dir, tour_api_service_key=None),
        EmptyRetriever(),
        TourismQueryService(),
    )

    response = service.answer("서울 휠체어 관광지 추천")

    assert response.cards == []
    assert "조건에 맞는 관광지를 확인하지 못했습니다" in response.answer


def test_tourism_chat_does_not_return_region_cards_for_unmatched_place_feature():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("서울 강남구에 바닷가 휠체어 관광지 추천해줘")

    assert response.cards == []
    assert "조건에 맞는 관광지를 확인하지 못했습니다" in response.answer


def test_tourism_chat_does_not_return_broad_region_cards_for_unmatched_place_feature():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("대전에서 바닷가 휠체어 관광지 추천해줘")

    assert response.cards == []
    assert "조건에 맞는 관광지를 확인하지 못했습니다" in response.answer


def test_tourism_chat_asks_for_region_before_searching():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("휠체어 타는 가족이랑 갈 만한 관광지 추천해줘")

    assert response.cards == []
    assert response.lookup_mode == "clarification"
    assert "추천할 지역을 먼저 알려 주세요" in response.answer
    assert response.suggested_messages


def test_tourism_chat_rejects_unsupported_price_comparison():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("휠체어 대여 가격이 제일 싼 곳 알려줘")

    assert response.cards == []
    assert response.lookup_mode == "unsupported"
    assert "가격 비교" in response.answer


def test_tourism_chat_answers_supported_part_when_scope_request_is_mixed():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("서울에서 휠체어 관광지 추천하면서 근처 응급실과 약국도 같이 알려줘")

    assert response.cards
    assert response.lookup_mode == "indexed"
    assert "현재 MVP의 확인 데이터 범위 밖" in response.answer
    assert response.warnings


def test_tourism_chat_clarifies_when_unsupported_condition_is_core():
    service = TourismChatService(Settings(), FakeRetriever(), TourismQueryService())

    response = service.answer("제주에서 지하철역 바로 연결된 무장애 관광지 추천해줘")

    assert response.cards == []
    assert response.lookup_mode == "clarification"
    assert "핵심 조건" in response.answer
    assert response.suggested_messages == ["제주에서 휠체어 관광지 추천해줘"]


def test_tourism_chat_sample_cards_are_cached(tmp_path):
    sample_dir = tmp_path / "tourism"
    sample_dir.mkdir()
    card = TourismPlaceCard(
        content_id="cache-sample",
        title="캐시 테스트 관광지",
        address="서울 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    (sample_dir / "sample.md").write_text(TourismNormalizer().card_to_markdown(card), encoding="utf-8")

    class CountingCodec:
        def __init__(self):
            self.calls = 0

        def from_markdown(self, text: str):
            self.calls += 1
            return TourismNormalizer().codec.from_markdown(text)

    class EmptyRetriever:
        def retrieve(self, message: str):
            return []

    codec = CountingCodec()
    service = TourismChatService(
        Settings(
            tourism_sample_path=sample_dir,
            tourism_live_cache_path=tmp_path / "live_cache",
            tour_api_service_key=None,
        ),
        EmptyRetriever(),
        TourismQueryService(),
        card_codec=codec,
    )

    assert service.answer("서울 휠체어 관광지").cards[0].title == "캐시 테스트 관광지"
    assert service.answer("서울 휠체어 관광지").cards[0].title == "캐시 테스트 관광지"
    assert codec.calls == 1
