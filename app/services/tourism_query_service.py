from __future__ import annotations

from pathlib import Path
import json

from app.core.config import PROJECT_ROOT


AREA_CODES = {
    "서울": "1",
    "인천": "2",
    "대전": "3",
    "대구": "4",
    "광주": "5",
    "부산": "6",
    "울산": "7",
    "세종": "8",
    "경기": "31",
    "강원": "32",
    "강릉": "32",
    "충북": "33",
    "충남": "34",
    "경북": "35",
    "경남": "36",
    "전북": "37",
    "전남": "38",
    "제주": "39",
}

SIGUNGU_CODES = {
    "강릉": "1",
}

DEFAULT_AREA_CODE_CACHE_PATH = PROJECT_ROOT / "data" / "processed" / "tour_area_codes.json"

CONDITION_KEYWORDS = {
    "휠체어": ["휠체어", "장애인", "무장애", "접근성", "이동약자"],
    "유모차": ["유모차", "아기", "영유아", "아이", "가족", "수유실"],
    "고령자": ["고령자", "어르신", "노인", "부모님"],
    "주차": ["주차", "장애인 주차"],
    "화장실": ["화장실", "장애인 화장실"],
    "접근로": ["접근로", "동선", "경사로", "턱 없음", "턱이 없어"],
    "대중교통": ["대중교통", "버스", "지하철"],
    "엘리베이터": ["엘리베이터", "승강기"],
}

EXPANSION_KEYWORDS = ["근처", "주변", "가까운", "인근"]


class TourismQueryService:
    def __init__(self, area_code_cache_path: Path | None = None):
        self.area_code_cache_path = area_code_cache_path or DEFAULT_AREA_CODE_CACHE_PATH
        self.region_index = self._load_region_index()

    def extract(self, message: str) -> dict[str, list[str] | str | None]:
        region = self._find_region(message)
        conditions = [
            label
            for label, keywords in CONDITION_KEYWORDS.items()
            if any(keyword in message for keyword in keywords)
        ]
        cached_region = self.region_index.get(region or "", {})
        sigungu_code = cached_region.get("sigungu_code") or SIGUNGU_CODES.get(region or "")
        area_name = cached_region.get("area_name")
        return {
            "region": region,
            "area_code": cached_region.get("area_code") or AREA_CODES.get(region or ""),
            "sigungu_code": sigungu_code,
            "area_name": area_name,
            "is_sigungu": bool(sigungu_code),
            "allow_region_expansion": any(keyword in message for keyword in EXPANSION_KEYWORDS),
            "conditions": conditions,
        }

    def _find_region(self, message: str) -> str | None:
        for name in sorted(self.region_index, key=len, reverse=True):
            if name and name in message:
                return name
        return next((name for name in AREA_CODES if name in message), None)

    def _load_region_index(self) -> dict[str, dict[str, str | None]]:
        if not self.area_code_cache_path.exists():
            return {}
        try:
            payload = json.loads(self.area_code_cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        region_index = payload.get("region_index", {})
        if not isinstance(region_index, dict):
            return {}
        return {
            str(name): value
            for name, value in region_index.items()
            if isinstance(value, dict)
        }
