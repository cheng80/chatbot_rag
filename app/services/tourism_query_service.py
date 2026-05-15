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
DEFAULT_ADMIN_REGION_ALIAS_PATH = PROJECT_ROOT / "data" / "processed" / "admin_region_aliases.json"

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
FEATURE_KEYWORDS = {
    "바닷가": ["바닷가", "바다", "해변", "해수욕장", "해안", "해변가"],
}
UNSUPPORTED_INTENT_KEYWORDS = {
    "wheelchair_rental_price": ["휠체어 대여", "대여 가격", "가격이 제일 싼", "제일 싼 곳", "최저가"],
}
logger = logging.getLogger(__name__)


class TourismQueryService:
    def __init__(
        self,
        area_code_cache_path: Path | None = None,
        admin_region_alias_path: Path | None = None,
    ):
        self.area_code_cache_path = area_code_cache_path or DEFAULT_AREA_CODE_CACHE_PATH
        self.admin_region_alias_path = admin_region_alias_path or DEFAULT_ADMIN_REGION_ALIAS_PATH
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
            "features": [
                label
                for label, keywords in FEATURE_KEYWORDS.items()
                if any(keyword in message for keyword in keywords)
            ],
            "unsupported_intent": self._find_unsupported_intent(message),
            "ambiguous_region": ambiguous_region,
            "ambiguous_region_candidates": self.ambiguous_region_aliases.get(ambiguous_region or "", []),
            "region_cache_status": self.cache_status,
            "region_cache_warning": self.cache_warning,
        }

    @staticmethod
    def _find_unsupported_intent(message: str) -> str | None:
        for label, keywords in UNSUPPORTED_INTENT_KEYWORDS.items():
            if any(keyword in message for keyword in keywords):
                return label
        return None

    def _find_region(self, message: str) -> str | None:
        for name in sorted(self.region_index, key=len, reverse=True):
            if name and name in message:
                return name
        return next((name for name in AREA_CODES if name in message), None)

    def _find_ambiguous_region(self, message: str, region: str | None) -> str | None:
        for alias in sorted(self.ambiguous_region_aliases, key=len, reverse=True):
            candidates = self.ambiguous_region_aliases[alias]
            if alias not in message:
                continue
            if region:
                if region == alias:
                    return alias
                if region in AREA_CODES:
                    if any(candidate.get("area_name") == region for candidate in candidates):
                        return None
                    continue
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
        self._merge_admin_region_aliases(loaded_index)
        return loaded_index

    def _merge_admin_region_aliases(self, loaded_index: dict[str, dict[str, str | None]]) -> None:
        if not self.admin_region_alias_path.exists():
            return
        try:
            payload = json.loads(self.admin_region_alias_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("행정동/법정동 매칭 데이터를 읽을 수 없습니다: %s (%s)", self.admin_region_alias_path, exc)
            return

        aliases = payload.get("aliases", {})
        if isinstance(aliases, dict):
            self._merge_alias_candidates(aliases, loaded_index)
        dong_aliases = payload.get("dong_aliases", {})
        if isinstance(dong_aliases, dict):
            self._merge_alias_candidates(dong_aliases, loaded_index)

    def _merge_alias_candidates(
        self,
        aliases: dict,
        loaded_index: dict[str, dict[str, str | None]],
    ) -> None:
        for alias, raw_candidates in aliases.items():
            if not isinstance(raw_candidates, list):
                continue
            candidates = [self._normalize_admin_alias_candidate(candidate) for candidate in raw_candidates]
            candidates = [candidate for candidate in candidates if candidate.get("area_code")]
            if not candidates:
                continue
            unique_candidates = self._unique_region_candidates(candidates)
            if len(unique_candidates) == 1:
                loaded_index.setdefault(str(alias), unique_candidates[0])
            else:
                self.ambiguous_region_aliases.setdefault(str(alias), unique_candidates)

    @staticmethod
    def _normalize_admin_alias_candidate(candidate: dict) -> dict[str, str | None]:
        return {
            "area_code": candidate.get("area_code") or candidate.get("tour_area_code"),
            "sigungu_code": candidate.get("sigungu_code") or candidate.get("tour_sigungu_code"),
            "area_name": candidate.get("area_name"),
            "sigungu_name": candidate.get("sigungu_name"),
        }

    @staticmethod
    def _unique_region_candidates(candidates: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
        result = []
        seen = set()
        for candidate in candidates:
            key = (candidate.get("area_code"), candidate.get("sigungu_code"))
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return result
