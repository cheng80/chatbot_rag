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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("서울에서 휠체어 타는 아빠와 갈만한 관광지 추천")

    assert query["conditions"] == ["휠체어"]


def test_tourism_query_falls_back_without_cache(tmp_path: Path):
    service = TourismQueryService(area_code_cache_path=tmp_path / "missing.json", admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

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


def test_tourism_query_resolves_short_sigungu_with_admin_aliases(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(json.dumps({"region_index": {}, "ambiguous_region_aliases": {}}, ensure_ascii=False))
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {
                    "부산 중구": [
                        {
                            "area_name": "부산",
                            "sigungu_name": "중구",
                            "tour_area_code": "6",
                            "tour_sigungu_code": "15",
                        }
                    ]
                },
                "dong_aliases": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=area_cache_path, admin_region_alias_path=admin_alias_path)

    query = service.extract("부산 중구에서 휠체어 관광지 추천해줘")

    assert query["region"] == "부산 중구"
    assert query["area_code"] == "6"
    assert query["sigungu_code"] == "15"
    assert query["area_name"] == "부산"
    assert query["sigungu_name"] == "중구"


def test_tourism_query_resolves_unique_legal_dong_to_sigungu(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(json.dumps({"region_index": {}, "ambiguous_region_aliases": {}}, ensure_ascii=False))
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {},
                "dong_aliases": {
                    "좌동": [
                        {
                            "area_name": "부산",
                            "sigungu_name": "해운대구",
                            "admin_dong_name": "좌제1동",
                            "legal_dong_name": "좌동",
                            "tour_area_code": "6",
                            "tour_sigungu_code": "16",
                        },
                        {
                            "area_name": "부산",
                            "sigungu_name": "해운대구",
                            "admin_dong_name": "좌제2동",
                            "legal_dong_name": "좌동",
                            "tour_area_code": "6",
                            "tour_sigungu_code": "16",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=area_cache_path, admin_region_alias_path=admin_alias_path)

    query = service.extract("해운대 좌동에서 유모차로 갈만한 관광지 추천")

    assert query["region"] == "좌동"
    assert query["area_code"] == "6"
    assert query["sigungu_code"] == "16"
    assert query["area_name"] == "부산"
    assert query["sigungu_name"] == "해운대구"
    assert "유모차" in query["conditions"]


def test_tourism_query_keeps_ambiguous_admin_alias_as_clarification(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(json.dumps({"region_index": {}, "ambiguous_region_aliases": {}}, ensure_ascii=False))
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {
                    "중구": [
                        {
                            "area_name": "서울",
                            "sigungu_name": "중구",
                            "tour_area_code": "1",
                            "tour_sigungu_code": "24",
                        },
                        {
                            "area_name": "부산",
                            "sigungu_name": "중구",
                            "tour_area_code": "6",
                            "tour_sigungu_code": "15",
                        },
                    ]
                },
                "dong_aliases": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=area_cache_path, admin_region_alias_path=admin_alias_path)

    query = service.extract("중구에서 휠체어 타시는 아버지와 갈 관광지 추천")

    assert query["region"] is None
    assert query["ambiguous_region"] == "중구"
    assert len(query["ambiguous_region_candidates"]) == 2
    assert "휠체어" in query["conditions"]


def test_tourism_query_maps_general_gu_to_parent_tourapi_sigungu(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(json.dumps({"region_index": {}, "ambiguous_region_aliases": {}}, ensure_ascii=False))
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {},
                "dong_aliases": {
                    "마산합포구": [
                        {
                            "area_name": "경남",
                            "sigungu_name": "창원시",
                            "admin_dong_name": "마산합포구",
                            "legal_dong_name": "창원시마산합포구",
                            "tour_area_code": "36",
                            "tour_sigungu_code": "16",
                        }
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=area_cache_path, admin_region_alias_path=admin_alias_path)

    query = service.extract("창원 마산합포구에서 이동약자 관광지 추천")

    assert query["region"] == "마산합포구"
    assert query["area_code"] == "36"
    assert query["sigungu_code"] == "16"
    assert query["area_name"] == "경남"
    assert query["sigungu_name"] == "창원시"
    assert "휠체어" in query["conditions"]
