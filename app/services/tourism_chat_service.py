from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.schemas.chat import Source
from app.schemas.tourism import AccessibilityInfo, TourismChatResponse, TourismPlaceCard
from app.services.retriever import Retriever
from app.services.tourism_query_service import TourismQueryService


class TourismChatService:
    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        query_service: TourismQueryService,
    ):
        self.settings = settings
        self.retriever = retriever
        self.query_service = query_service

    def answer(self, message: str, session_id: str | None = None) -> TourismChatResponse:
        query = self.query_service.extract(message)
        contexts = self._retrieve(message)
        cards = self._cards_from_contexts(contexts)

        if not cards:
            cards = self._cards_from_markdown_samples()
        elif query.get("allow_region_expansion"):
            cards = self._deduplicate([*cards, *self._cards_from_markdown_samples()])

        cards, expanded = self._select_cards(cards, message, query)
        sources = self._build_sources(contexts, cards)

        if not cards:
            return TourismChatResponse(
                answer="조건에 맞는 관광지를 확인하지 못했습니다. 지역이나 접근성 조건을 조금 넓혀 다시 질문해 주세요.",
                cards=[],
                sources=sources,
            )

        answer = self._build_answer(cards, query, expanded=expanded)
        return TourismChatResponse(answer=answer, cards=cards, sources=sources)

    def _retrieve(self, message: str) -> list[dict]:
        try:
            return self.retriever.retrieve(message)
        except Exception:
            return []

    def _cards_from_contexts(self, contexts: list[dict]) -> list[TourismPlaceCard]:
        cards = []
        for context in contexts:
            card = self._parse_card_text(context.get("text") or "")
            if card:
                cards.append(card)
        return self._deduplicate(cards)

    def _cards_from_markdown_samples(self) -> list[TourismPlaceCard]:
        sample_path = self.settings.resolved_tourism_sample_path
        cards = []
        for path in sorted(sample_path.glob("*.md")):
            card = self._parse_card_text(path.read_text(encoding="utf-8"))
            if card:
                cards.append(card)
        return self._deduplicate(cards)

    def _parse_card_text(self, text: str) -> TourismPlaceCard | None:
        fields: dict[str, str] = {}
        raw_fields: dict[str, str] = {}
        in_facilities = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "편의정보:":
                in_facilities = True
                continue
            if in_facilities and stripped.startswith("- ") and ":" in stripped:
                key, value = stripped[2:].split(":", 1)
                if value.strip() and value.strip() != "확인 필요":
                    raw_fields[key.strip()] = value.strip()
                continue
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                fields[key.strip()] = value.strip()

        title = fields.get("관광지명")
        content_id = fields.get("콘텐츠ID")
        if not title or not content_id:
            return None

        accessibility_tags = self._split_tags(fields.get("접근성태그"))
        family_tags = self._split_tags(fields.get("가족태그"))
        return TourismPlaceCard(
            content_id=content_id,
            title=title,
            address=self._none_if_unknown(fields.get("주소")),
            image_url=self._none_if_unknown(fields.get("대표이미지")),
            tel=self._none_if_unknown(fields.get("전화번호")),
            recommendation_reason=fields.get("추천근거") or f"{title}은(는) 무장애 여행 정보에 포함된 관광지입니다.",
            accessibility=AccessibilityInfo(
                wheelchair=self._find_raw(raw_fields, ["휠체어", "출입통로"]),
                parking=self._find_raw(raw_fields, ["주차"]),
                restroom=self._find_raw(raw_fields, ["화장실"]),
                stroller=self._find_raw(raw_fields, ["유모차"]),
                nursing_room=self._find_raw(raw_fields, ["수유실"]),
                elevator=self._find_raw(raw_fields, ["엘리베이터"]),
                route=self._find_raw(raw_fields, ["접근로", "대중교통"]),
            ),
            accessibility_tags=accessibility_tags,
            family_tags=family_tags,
            source_url=self._none_if_unknown(fields.get("출처URL")),
            raw_fields=raw_fields,
        )

    def _select_cards(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> tuple[list[TourismPlaceCard], bool]:
        region = query.get("region")
        if region and query.get("is_sigungu"):
            region_cards = self._rank_cards(
                self._filter_cards_by_region(cards, region),
                message,
                query,
                filter_region=False,
            )
            if len(region_cards) >= 3 or not query.get("allow_region_expansion"):
                return region_cards[:5], False

            area_name = query.get("area_name")
            expanded_cards = self._rank_cards(
                self._filter_cards_by_region(cards, area_name),
                message,
                query,
                filter_region=False,
            )
            return self._deduplicate([*region_cards, *expanded_cards])[:5], True

        return self._rank_cards(cards, message, query)[:5], False

    def _rank_cards(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
        filter_region: bool = True,
    ) -> list[TourismPlaceCard]:
        conditions = query.get("conditions") or []
        region = query.get("region")
        if filter_region and region:
            region_cards = [card for card in cards if region in f"{card.title} {card.address or ''}"]
            if region_cards:
                cards = region_cards

        def score(card: TourismPlaceCard) -> int:
            haystack = " ".join(
                [
                    card.title,
                    card.address or "",
                    card.recommendation_reason,
                    " ".join(card.accessibility_tags),
                    " ".join(card.family_tags),
                    " ".join(card.raw_fields.values()),
                ]
            )
            value = 0
            if region and region in haystack:
                value += 4
            for condition in conditions:
                if condition in haystack:
                    value += 3
            for token in message.split():
                if len(token) >= 2 and token in haystack:
                    value += 1
            return value

        return sorted(cards, key=score, reverse=True)

    @staticmethod
    def _filter_cards_by_region(cards: list[TourismPlaceCard], region: str | None) -> list[TourismPlaceCard]:
        if not region:
            return cards
        return [card for card in cards if region in f"{card.title} {card.address or ''}"]

    def _build_answer(self, cards: list[TourismPlaceCard], query: dict, expanded: bool = False) -> str:
        region = query.get("region") or "요청 지역"
        conditions = ", ".join(query.get("conditions") or ["무장애/가족 친화"])
        lines = [f"{region} 기준으로 {conditions} 조건에 맞는 관광지 {len(cards)}곳을 추천합니다."]
        if query.get("is_sigungu") and len(cards) < 3 and not expanded:
            lines.append(
                f"{region} 안에서 확인된 후보가 {len(cards)}곳이라 요청 지역 안의 결과만 먼저 제공합니다. "
                "더 많은 후보가 필요하면 '근처'나 '주변'을 포함해 다시 물어보면 상위 지역까지 넓혀 찾겠습니다."
            )
        if expanded:
            area_name = query.get("area_name") or "상위 지역"
            lines.append(f"{region} 안의 후보가 부족해 요청 표현에 따라 {area_name} 범위 후보를 함께 포함했습니다.")
        for index, card in enumerate(cards, start=1):
            tags = card.accessibility_tags + card.family_tags
            basis = ", ".join(tags[:4]) if tags else "세부 편의정보 확인 필요"
            lines.append(f"{index}. {card.title}: {basis}. 출처는 {card.source_name}입니다.")
        lines.append("OpenAPI에 없는 편의정보는 추측하지 않고 카드에 '확인 필요'로 남겼습니다.")
        return "\n".join(lines)

    def _build_sources(self, contexts: list[dict], cards: list[TourismPlaceCard]) -> list[Source]:
        sources = []
        card_ids = {card.content_id for card in cards}
        sourced_card_ids = set()
        for context in contexts:
            context_card = self._parse_card_text(context.get("text") or "")
            if card_ids and (not context_card or context_card.content_id not in card_ids):
                continue
            metadata = context.get("metadata") or {}
            source = metadata.get("source") or metadata.get("file_path")
            if source:
                sources.append(
                    Source(
                        source=source,
                        page=metadata.get("page"),
                        chunk_id=context.get("id") or "",
                        chunk_index=metadata.get("chunk_index"),
                        distance=context.get("distance"),
                    )
                )
                if context_card:
                    sourced_card_ids.add(context_card.content_id)

        for card in cards:
            if card.content_id not in sourced_card_ids:
                sources.append(
                    Source(source=card.source_name, page=None, chunk_id=card.content_id, chunk_index=None, distance=None)
                )
        return sources

    @staticmethod
    def _deduplicate(cards: list[TourismPlaceCard]) -> list[TourismPlaceCard]:
        result = []
        seen = set()
        for card in cards:
            if card.content_id in seen:
                continue
            seen.add(card.content_id)
            result.append(card)
        return result

    @staticmethod
    def _split_tags(value: str | None) -> list[str]:
        if not value or value == "확인 필요":
            return []
        return [tag.strip() for tag in value.split(",") if tag.strip()]

    @staticmethod
    def _none_if_unknown(value: str | None) -> str | None:
        if not value or value == "확인 필요":
            return None
        return value

    @staticmethod
    def _find_raw(raw_fields: dict[str, str], labels: list[str]) -> str | None:
        for label in labels:
            for key, value in raw_fields.items():
                if label in key:
                    return value
        return None
