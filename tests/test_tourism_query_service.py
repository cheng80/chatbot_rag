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


def test_tourism_query_extracts_place_feature_keywords(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "서울 강남구": {
                        "area_code": "1",
                        "sigungu_code": "1",
                        "area_name": "서울",
                        "sigungu_name": "강남구",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("서울 강남구에 바닷가 휠체어 관광지 추천해줘")

    assert query["region"] == "서울 강남구"
    assert query["features"] == ["바닷가"]


def test_tourism_query_marks_unsupported_price_comparison(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(json.dumps({"ambiguous_region_aliases": {}, "region_index": {}}, ensure_ascii=False), encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("휠체어 대여 가격이 제일 싼 곳 알려줘")

    assert query["unsupported_intent"] == "wheelchair_rental_price"


def test_tourism_query_marks_mixed_scope_request(tmp_path: Path):
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

    query = service.extract("서울에서 휠체어 관광지 추천하면서 근처 응급실과 약국도 같이 알려줘")

    assert query["region"] == "서울"
    assert "휠체어" in query["conditions"]
    assert query["unsupported_intent"] == "medical_lookup"


def test_tourism_query_ignores_negated_unsupported_keyword(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "부산 중구": {
                        "area_code": "6",
                        "sigungu_code": "15",
                        "area_name": "부산",
                        "sigungu_name": "중구",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("부산 중구에서 응급실 말고 휠체어 관광지만 추천해줘")

    assert query["region"] == "부산 중구"
    assert "휠체어" in query["conditions"]
    assert query["unsupported_intent"] is None


def test_tourism_query_maps_legacy_region_name_to_current_sigungu(tmp_path: Path):
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
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("청원군에서 휠체어 관광지 추천해줘")

    assert query["region"] == "청주시"
    assert query["area_code"] == "33"
    assert query["sigungu_code"] == "10"
    assert query["sigungu_name"] == "청주시"
    assert query["legacy_region"] == "청원군"
    assert query["legacy_region_replacement"] == "청주시"
    assert "청원군은 현재 행정구역 기준 청주시" in query["legacy_region_notice"]


def test_tourism_query_maps_legacy_jeju_county_to_current_city(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "남제주군": {
                        "area_code": "39",
                        "sigungu_code": "2",
                        "area_name": "제주",
                        "sigungu_name": "남제주군",
                    },
                    "서귀포시": {
                        "area_code": "39",
                        "sigungu_code": "3",
                        "area_name": "제주",
                        "sigungu_name": "서귀포시",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("제주특별자치도 남제주군에서 유모차 관광지 추천해줘")

    assert query["region"] == "서귀포시"
    assert query["area_code"] == "39"
    assert query["sigungu_code"] == "3"
    assert query["sigungu_name"] == "서귀포시"
    assert query["legacy_region"] == "제주특별자치도 남제주군"
    assert "남제주군은 현재 행정구역 기준 서귀포시" in query["legacy_region_notice"]


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


def test_tourism_query_keeps_bare_ambiguous_alias_even_if_admin_alias_has_single_default(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(
        json.dumps(
            {
                "region_index": {},
                "ambiguous_region_aliases": {
                    "남구": [
                        {
                            "area_code": "6",
                            "sigungu_code": "4",
                            "area_name": "부산",
                            "sigungu_name": "남구",
                        },
                        {
                            "area_code": "7",
                            "sigungu_code": "2",
                            "area_name": "울산",
                            "sigungu_name": "남구",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {
                    "남구": [
                        {
                            "area_name": "경북",
                            "sigungu_name": "포항시",
                            "tour_area_code": "35",
                            "tour_sigungu_code": "23",
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

    query = service.extract("남구에서 유모차로 갈 수 있는 곳 추천해줘")

    assert query["region"] == "남구"
    assert query["ambiguous_region"] == "남구"
    assert len(query["ambiguous_region_candidates"]) == 2


def test_tourism_query_does_not_treat_common_word_alias_as_region_when_area_is_known(tmp_path: Path):
    area_cache_path = tmp_path / "tour_area_codes.json"
    admin_alias_path = tmp_path / "admin_region_aliases.json"
    area_cache_path.write_text(
        json.dumps(
            {
                "region_index": {
                    "서울": {
                        "area_code": "1",
                        "sigungu_code": None,
                        "area_name": "서울",
                        "sigungu_name": None,
                    }
                },
                "ambiguous_region_aliases": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    admin_alias_path.write_text(
        json.dumps(
            {
                "aliases": {},
                "dong_aliases": {
                    "이동": [
                        {
                            "area_name": "경기",
                            "sigungu_name": "의왕시",
                            "tour_area_code": "31",
                            "tour_sigungu_code": "24",
                        },
                        {
                            "area_name": "경남",
                            "sigungu_name": "김해시",
                            "tour_area_code": "36",
                            "tour_sigungu_code": "4",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=area_cache_path, admin_region_alias_path=admin_alias_path)

    query = service.extract("서울에서 고령자 부모님과 휠체어로 이동하기 좋은 실내 관광지 추천해줘")

    assert query["region"] == "서울"
    assert query["ambiguous_region"] is None
    assert "휠체어" in query["conditions"]
    assert "고령자" in query["conditions"]


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


def test_tourism_query_uses_region_after_replacement_marker(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "서귀포": {
                        "area_code": "39",
                        "sigungu_code": "3",
                        "area_name": "제주",
                        "sigungu_name": "서귀포시",
                    },
                    "제주시": {
                        "area_code": "39",
                        "sigungu_code": "4",
                        "area_name": "제주",
                        "sigungu_name": "제주시",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("서귀포시 말고 제주시")

    assert query["region"] == "제주시"
    assert query["sigungu_code"] == "4"


def test_tourism_query_splits_excluded_and_replacement_preferences(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(json.dumps({"ambiguous_region_aliases": {}, "region_index": {}}, ensure_ascii=False), encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("시장 말고 실내 박물관 쪽으로 바꿔줘")

    assert query["preferences"] == ["실내", "박물관_전시"]
    assert query["excluded_preferences"] == ["시장_먹거리"]


def test_tourism_query_handles_particle_before_exclusion_marker(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(json.dumps({"ambiguous_region_aliases": {}, "region_index": {}}, ensure_ascii=False), encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("호텔이나 숙박은 빼고 관광지만 계속")

    assert query["preferences"] == []
    assert query["excluded_preferences"] == ["숙박"]


def test_tourism_query_ignores_negated_legacy_region(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(
        json.dumps(
            {
                "ambiguous_region_aliases": {},
                "region_index": {
                    "제주시": {
                        "area_code": "39",
                        "sigungu_code": "4",
                        "area_name": "제주",
                        "sigungu_name": "제주시",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("남제주군 말고 제주시로")

    assert query["region"] == "제주시"
    assert query["legacy_region"] is None


def test_tourism_query_extracts_required_evidence_terms_for_explicit_details(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(json.dumps({"ambiguous_region_aliases": {}, "region_index": {}}, ensure_ascii=False), encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    query = service.extract("대구에서 점자블록과 안내견 가능한 곳 추천")

    assert ["점자블록", "점자"] in query["required_evidence_terms"]
    assert ["보조견", "안내견"] in query["required_evidence_terms"]
    assert "specific_facility_required" in query["context_labels"]


def test_tourism_query_requires_all_conditions_only_when_explicit(tmp_path: Path):
    cache_path = tmp_path / "tour_area_codes.json"
    cache_path.write_text(json.dumps({"ambiguous_region_aliases": {}, "region_index": {}}, ensure_ascii=False), encoding="utf-8")
    service = TourismQueryService(area_code_cache_path=cache_path, admin_region_alias_path=tmp_path / "missing_admin_aliases.json")

    loose = service.extract("서울에서 휠체어와 유모차 가능한 관광지 추천")
    strict = service.extract("서울에서 휠체어와 유모차 둘 다 가능한 관광지 추천")

    assert loose["require_all_conditions"] is False
    assert strict["require_all_conditions"] is True
    assert "soft_and" in loose["context_labels"]
    assert "strict_and" in strict["context_labels"]
