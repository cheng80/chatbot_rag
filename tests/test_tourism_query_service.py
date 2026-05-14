from pathlib import Path
import json

from app.services.tourism_query_service import TourismQueryService


def test_tourism_query_uses_area_code_cache(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
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

    query = service.extract("강릉에서 어르신과 휠체어로 갈만한 관광지")

    assert query["region"] == "강릉"
    assert query["area_code"] == "32"
    assert query["sigungu_code"] == "1"
    assert "고령자" in query["conditions"]
    assert "휠체어" in query["conditions"]


def test_tourism_query_does_not_treat_parent_terms_as_elderly(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "강릉": {
                        "area_code": "32",
                        "sigungu_code": "1",
                        "area_name": "강원",
                        "sigungu_name": "강릉시",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path)

    query = service.extract("강릉에서 휠체어 타시는 어머니와 갈만한 관광지")

    assert "휠체어" in query["conditions"]
    assert "고령자" not in query["conditions"]


def test_tourism_query_does_not_infer_age_from_parent_relationship(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "서울": {
                        "area_code": "1",
                        "sigungu_code": None,
                        "area_name": "서울",
                        "sigungu_name": None,
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path)

    query = service.extract("서울에서 휠체어 타는 아빠와 갈만한 관광지 추천")

    assert query["conditions"] == ["휠체어"]


def test_tourism_query_falls_back_without_cache(tmp_path: Path):
    service = TourismQueryService(area_code_cache_path=tmp_path / "missing.json")

    query = service.extract("부산에서 접근로 좋은 관광지")

    assert query["region"] == "부산"
    assert query["area_code"] == "6"
    assert query["sigungu_code"] is None
    assert "접근로" in query["conditions"]
    assert query["region_cache_status"] == "missing"
    assert "지역 코드 캐시" in query["region_cache_warning"]


def test_tourism_query_reports_invalid_cache(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text("{bad json", encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path)

    query = service.extract("부산에서 접근로 좋은 관광지")

    assert query["region"] == "부산"
    assert query["area_code"] == "6"
    assert query["region_cache_status"] == "invalid"
    assert "지역 코드 캐시" in query["region_cache_warning"]


def test_tourism_query_reports_ambiguous_region_alias(tmp_path: Path):
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
    service = TourismQueryService(area_code_cache_path=cache_path)

    ambiguous = service.extract("중구에서 휠체어 관광지 추천")
    resolved = service.extract("부산 중구에서 휠체어 관광지 추천")

    assert ambiguous["ambiguous_region"] == "중구"
    assert len(ambiguous["ambiguous_region_candidates"]) == 2
    assert resolved["region"] == "부산 중구"
    assert resolved["area_code"] == "6"
    assert resolved["sigungu_code"] == "15"
    assert resolved["area_name"] == "부산"
    assert resolved["sigungu_name"] == "중구"
    assert resolved["ambiguous_region"] is None
