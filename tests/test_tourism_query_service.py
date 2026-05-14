from pathlib import Path
import json

from app.services.tourism_query_service import TourismQueryService


def test_tourism_query_uses_area_code_cache(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "region_index": {
                    "강릉": {
                        "area_code": "32",
                        "sigungu_code": "1",
                        "area_name": "강원",
                        "sigungu_name": "강릉시",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path)

    query = service.extract("강릉에서 부모님과 휠체어로 갈만한 관광지")

    assert query["region"] == "강릉"
    assert query["area_code"] == "32"
    assert query["sigungu_code"] == "1"
    assert "고령자" in query["conditions"]
    assert "휠체어" in query["conditions"]


def test_tourism_query_falls_back_without_cache(tmp_path: Path):
    service = TourismQueryService(area_code_cache_path=tmp_path / "missing.json")

    query = service.extract("부산에서 접근로 좋은 관광지")

    assert query["region"] == "부산"
    assert query["area_code"] == "6"
    assert query["sigungu_code"] is None
    assert "접근로" in query["conditions"]
