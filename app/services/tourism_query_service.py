from __future__ import annotations

from pathlib import Path
import json
import logging

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
    "고령자": ["고령자", "어르신", "노인"],
    "주차": ["주차", "장애인 주차"],
    "화장실": ["화장실", "장애인 화장실"],
    "접근로": ["접근로", "동선", "경사로", "턱 없음", "턱이 없어"],
    "대중교통": ["대중교통", "버스", "지하철"],
    "엘리베이터": ["엘리베이터", "승강기"],
}

EXPANSION_KEYWORDS = ["근처", "주변", "가까운", "인근"]
logger = logging.getLogger(__name__)


class TourismQueryService:
    def __init__(self, area_code_cache_path: Path | None = None):
        self.area_code_cache_path = area_code_cache_path or DEFAULT_AREA_CODE_CACHE_PATH
        self.cache_status = "loaded"
        self.cache_warning: str | None = None
        self.ambiguous_region_aliases: dict[str, list[dict[str, str | None]]] = {}
        self.region_index = self._load_region_index()

    def extract(self, message: str) -> dict[str, list[str] | str | None]:
        region = self._find_region(message)
        ambiguous_region = self._find_ambiguous_region(message, region)
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
            "sigungu_name": cached_region.get("sigungu_name"),
            "is_sigungu": bool(sigungu_code),
            "allow_region_expansion": any(keyword in message for keyword in EXPANSION_KEYWORDS),
            "conditions": conditions,
            "ambiguous_region": ambiguous_region,
            "ambiguous_region_candidates": self.ambiguous_region_aliases.get(ambiguous_region or "", []),
            "region_cache_status": self.cache_status,
            "region_cache_warning": self.cache_warning,
        }

    def _find_region(self, message: str) -> str | None:
        for name in sorted(self.region_index, key=len, reverse=True):
            if name and name in message:
                return name
        return next((name for name in AREA_CODES if name in message), None)

    def _find_ambiguous_region(self, message: str, region: str | None) -> str | None:
        if region and region not in AREA_CODES:
            return None
        for alias in sorted(self.ambiguous_region_aliases, key=len, reverse=True):
            candidates = self.ambiguous_region_aliases[alias]
            if alias not in message:
                continue
            if region and any(candidate.get("area_name") == region for candidate in candidates):
                return None
            return alias
        return None

    def _load_region_index(self) -> dict[str, dict[str, str | None]]:
        if not self.area_code_cache_path.exists():
            self.cache_status = "missing"
            self.cache_warning = f"지역 코드 캐시를 찾지 못했습니다: {self.area_code_cache_path}"
            logger.warning(self.cache_warning)
            return {}
        try:
            payload = json.loads(self.area_code_cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.cache_status = "invalid"
            self.cache_warning = f"지역 코드 캐시를 읽을 수 없습니다: {self.area_code_cache_path}"
            logger.warning("%s (%s)", self.cache_warning, exc.__class__.__name__)
            return {}
        region_index = payload.get("region_index", {})
        if not isinstance(region_index, dict):
            self.cache_status = "invalid"
            self.cache_warning = f"지역 코드 캐시 형식이 올바르지 않습니다: {self.area_code_cache_path}"
            logger.warning(self.cache_warning)
            return {}
        ambiguous_region_aliases = payload.get("ambiguous_region_aliases", {})
        if isinstance(ambiguous_region_aliases, dict):
            self.ambiguous_region_aliases = {
                str(alias): [candidate for candidate in candidates if isinstance(candidate, dict)]
                for alias, candidates in ambiguous_region_aliases.items()
                if isinstance(candidates, list)
            }
        loaded_index = {
            str(name): value
            for name, value in region_index.items()
            if isinstance(value, dict)
        }
        for alias, candidates in self.ambiguous_region_aliases.items():
            for candidate in candidates:
                area_name = candidate.get("area_name")
                sigungu_name = candidate.get("sigungu_name") or alias
                if area_name:
                    loaded_index.setdefault(f"{area_name} {alias}", candidate)
                    loaded_index.setdefault(f"{area_name} {sigungu_name}", candidate)
        return loaded_index
