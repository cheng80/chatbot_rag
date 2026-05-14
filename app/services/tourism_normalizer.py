from __future__ import annotations

from typing import Any

from app.schemas.tourism import AccessibilityInfo, TourismPlaceCard


ACCESSIBILITY_FIELD_LABELS = {
    "parking": "주차",
    "route": "접근로",
    "publictransport": "대중교통",
    "ticketoffice": "매표소",
    "promotion": "홍보물",
    "wheelchair": "휠체어",
    "exit": "출입통로",
    "elevator": "엘리베이터",
    "restroom": "화장실",
    "auditorium": "관람석",
    "room": "객실",
    "handicapetc": "기타 장애인 편의",
    "braileblock": "점자블록",
    "helpdog": "보조견",
    "guidehuman": "안내요원",
    "audioguide": "오디오가이드",
    "bigprint": "큰활자",
    "brailepromotion": "점자홍보물",
    "guidesystem": "안내시스템",
    "blindhandicapetc": "시각장애 편의",
    "signguide": "수어안내",
    "videoguide": "자막/영상안내",
    "hearingroom": "청각장애 객실",
    "hearinghandicapetc": "청각장애 편의",
    "stroller": "유모차",
    "lactationroom": "수유실",
    "babysparechair": "유아용 의자",
    "infantsfamilyetc": "영유아 가족 편의",
}


class TourismNormalizer:
    def normalize_place(self, common_item: dict[str, Any], accessible_item: dict[str, Any] | None = None) -> TourismPlaceCard:
        accessible_item = accessible_item or {}
        content_id = self._string(common_item.get("contentid") or accessible_item.get("contentid"))
        title = self._string(common_item.get("title") or accessible_item.get("title") or "이름 미상")

        raw_fields = self._extract_raw_accessibility_fields(accessible_item)
        accessibility = AccessibilityInfo(
            wheelchair=self._first_present(raw_fields, ["wheelchair", "exit"]),
            parking=self._first_present(raw_fields, ["parking"]),
            restroom=self._first_present(raw_fields, ["restroom"]),
            stroller=self._first_present(raw_fields, ["stroller"]),
            nursing_room=self._first_present(raw_fields, ["lactationroom"]),
            elevator=self._first_present(raw_fields, ["elevator"]),
            route=self._first_present(raw_fields, ["route", "publictransport"]),
        )
        accessibility_tags = self._build_accessibility_tags(raw_fields)
        family_tags = self._build_family_tags(raw_fields, common_item)

        return TourismPlaceCard(
            content_id=content_id,
            title=title,
            address=self._optional_string(common_item.get("addr1")),
            image_url=self._optional_string(common_item.get("firstimage") or common_item.get("firstimage2")),
            tel=self._optional_string(common_item.get("tel")),
            map_x=self._optional_float(common_item.get("mapx")),
            map_y=self._optional_float(common_item.get("mapy")),
            recommendation_reason=self._build_reason(title, accessibility_tags, family_tags),
            accessibility=accessibility,
            family_tags=family_tags,
            accessibility_tags=accessibility_tags,
            source_url=f"https://access.visitkorea.or.kr/detail/{content_id}" if content_id else None,
            raw_fields=raw_fields,
        )

    def card_to_markdown(self, card: TourismPlaceCard) -> str:
        accessibility_lines = [f"- {ACCESSIBILITY_FIELD_LABELS.get(key, key)}: {value}" for key, value in card.raw_fields.items()]
        if not accessibility_lines:
            accessibility_lines = ["- 확인 필요: OpenAPI 응답에 세부 편의정보가 없습니다."]

        return "\n".join(
            [
                f"# {card.title}",
                "",
                f"관광지명: {card.title}",
                f"콘텐츠ID: {card.content_id}",
                f"주소: {card.address or '확인 필요'}",
                f"전화번호: {card.tel or '확인 필요'}",
                f"대표이미지: {card.image_url or '확인 필요'}",
                f"추천근거: {card.recommendation_reason}",
                f"접근성태그: {', '.join(card.accessibility_tags) if card.accessibility_tags else '확인 필요'}",
                f"가족태그: {', '.join(card.family_tags) if card.family_tags else '확인 필요'}",
                f"출처: {card.source_name}",
                f"출처URL: {card.source_url or '확인 필요'}",
                "",
                "편의정보:",
                *accessibility_lines,
                "",
            ]
        )

    def _extract_raw_accessibility_fields(self, item: dict[str, Any]) -> dict[str, str]:
        fields: dict[str, str] = {}
        for key, label in ACCESSIBILITY_FIELD_LABELS.items():
            value = self._optional_string(item.get(key))
            if value:
                fields[key] = value
        return fields

    def _build_accessibility_tags(self, raw_fields: dict[str, str]) -> list[str]:
        tag_map = {
            "wheelchair": "휠체어 접근",
            "exit": "휠체어 접근",
            "parking": "장애인 주차",
            "restroom": "장애인 화장실",
            "elevator": "엘리베이터",
            "route": "접근로",
            "publictransport": "대중교통",
            "braileblock": "점자블록",
            "helpdog": "보조견 동반",
            "signguide": "수어안내",
            "videoguide": "자막/영상안내",
        }
        return self._unique(tag for key, tag in tag_map.items() if key in raw_fields)

    def _build_family_tags(self, raw_fields: dict[str, str], common_item: dict[str, Any]) -> list[str]:
        tags = []
        if "stroller" in raw_fields:
            tags.append("유모차 대여")
        if "lactationroom" in raw_fields:
            tags.append("수유실")
        if "babysparechair" in raw_fields:
            tags.append("유아용 의자")
        if "infantsfamilyetc" in raw_fields:
            tags.append("영유아 동반")
        overview = self._string(common_item.get("overview"))
        if any(word in overview for word in ["가족", "어린이", "아이", "유아"]):
            tags.append("가족 친화")
        return self._unique(tags)

    def _build_reason(self, title: str, accessibility_tags: list[str], family_tags: list[str]) -> str:
        tags = accessibility_tags + family_tags
        if tags:
            return f"{title}은(는) {', '.join(tags[:4])} 정보가 확인되어 조건에 맞는 후보입니다."
        return f"{title}은(는) 한국관광공사 무장애 여행 정보에 포함된 관광지입니다. 세부 편의정보는 확인이 필요합니다."

    @staticmethod
    def _first_present(raw_fields: dict[str, str], keys: list[str]) -> str | None:
        for key in keys:
            if key in raw_fields:
                return raw_fields[key]
        return None

    @staticmethod
    def _unique(values) -> list[str]:
        result = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result

    @staticmethod
    def _string(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _optional_string(self, value: Any) -> str | None:
        text = self._string(value)
        return text or None

    def _optional_float(self, value: Any) -> float | None:
        text = self._string(value)
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
