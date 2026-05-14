from app.core.config import Settings
from app.services.tour_api_service import TourAPIError, TourAPIService


def test_tour_api_requires_service_key():
    service = TourAPIService(Settings(tour_api_service_key=None))

    try:
        service.area_based_list("1")
    except TourAPIError as exc:
        assert "TOUR_API_SERVICE_KEY" in str(exc)
    else:
        raise AssertionError("TourAPIError was not raised")


def test_tour_api_extracts_single_item_dict():
    service = TourAPIService(Settings(tour_api_service_key="test"))
    payload = {
        "response": {
            "header": {"resultCode": "0000"},
            "body": {"items": {"item": {"contentid": "1", "title": "관광지"}}},
        }
    }

    assert service._extract_items(payload) == [{"contentid": "1", "title": "관광지"}]


def test_tour_api_extracts_top_level_error():
    service = TourAPIService(Settings(tour_api_service_key="test"))

    try:
        service._extract_items({"resultCode": "10", "resultMsg": "INVALID_REQUEST_PARAMETER_ERROR(listYN)"})
    except TourAPIError as exc:
        assert "listYN" in str(exc)
    else:
        raise AssertionError("TourAPIError was not raised")


def test_area_based_list_does_not_send_listyn(monkeypatch):
    service = TourAPIService(Settings(tour_api_service_key="test"))
    captured = {}

    def fake_request_items(operation, params, base_url=None):
        captured["operation"] = operation
        captured["params"] = params
        captured["base_url"] = base_url
        return []

    monkeypatch.setattr(service, "_request_items", fake_request_items)

    assert service.area_based_list("1") == []
    assert captured["operation"] == "areaBasedList2"
    assert "listYN" not in captured["params"]
    assert captured["params"]["areaCode"] == "1"
    assert captured["base_url"] is None

    service.area_based_list("32", sigungu_code="1")
    assert captured["params"]["sigunguCode"] == "1"


def test_accessible_area_based_list_uses_accessible_service(monkeypatch):
    settings = Settings(
        tour_api_service_key="default",
        tour_api_accessible_service_key="accessible",
        tour_api_accessible_base_url="https://example.com/with",
    )
    service = TourAPIService(settings)
    captured = {}

    def fake_request_items(operation, params, base_url=None, service_key=None):
        captured["operation"] = operation
        captured["params"] = params
        captured["base_url"] = base_url
        captured["service_key"] = service_key
        return []

    monkeypatch.setattr(service, "_request_items", fake_request_items)

    assert service.accessible_area_based_list("32", sigungu_code="1") == []
    assert captured["operation"] == "areaBasedList2"
    assert "listYN" not in captured["params"]
    assert captured["params"]["areaCode"] == "32"
    assert captured["params"]["sigunguCode"] == "1"
    assert captured["base_url"] == "https://example.com/with"
    assert captured["service_key"] == "accessible"


def test_detail_common_uses_service2_minimal_parameters(monkeypatch):
    service = TourAPIService(Settings(tour_api_service_key="test"))
    captured = {}

    def fake_request_items(operation, params, base_url=None):
        captured["operation"] = operation
        captured["params"] = params
        captured["base_url"] = base_url
        return [{"contentid": "1"}]

    monkeypatch.setattr(service, "_request_items", fake_request_items)

    assert service.detail_common("1") == {"contentid": "1"}
    assert captured == {
        "operation": "detailCommon2",
        "params": {"contentId": "1"},
        "base_url": None,
    }


def test_detail_with_tour_uses_accessible_base_url(monkeypatch):
    settings = Settings(
        tour_api_service_key="default",
        tour_api_accessible_service_key="accessible",
        tour_api_accessible_base_url="https://example.com/with",
    )
    service = TourAPIService(settings)
    captured = {}

    def fake_request_items(operation, params, base_url=None, service_key=None):
        captured["operation"] = operation
        captured["params"] = params
        captured["base_url"] = base_url
        captured["service_key"] = service_key
        return [{"contentid": "1"}]

    monkeypatch.setattr(service, "_request_items", fake_request_items)

    assert service.detail_with_tour("1") == {"contentid": "1"}
    assert captured == {
        "operation": "detailWithTour2",
        "params": {"contentId": "1"},
        "base_url": "https://example.com/with",
        "service_key": "accessible",
    }
