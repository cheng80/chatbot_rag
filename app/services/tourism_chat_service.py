from __future__ import annotations

import logging

from app.core.config import Settings
from app.schemas.chat import Source
from app.schemas.tourism import TourismChatResponse, TourismPlaceCard
from app.services.retriever import Retriever
from app.services.tourism_card_codec import TourismCardMarkdownCodec
from app.services.tourism_query_service import TourismQueryService

logger = logging.getLogger(__name__)


class TourismChatService:
    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        query_service: TourismQueryService,
        card_codec: TourismCardMarkdownCodec | None = None,
    ):
        self.settings = settings
        self.retriever = retriever
        self.query_service = query_service
        self.card_codec = card_codec or TourismCardMarkdownCodec()
        self._sample_cards_cache: list[TourismPlaceCard] | None = None

    def answer(self, message: str, session_id: str | None = None) -> TourismChatResponse:
        query = self.query_service.extract(message)
        contexts, degraded = self._retrieve(message)
        cards = self._cards_from_contexts(contexts)

        if not cards:
            cards = self._cards_from_markdown_samples()
            degraded = degraded or bool(cards)
        elif query.get("allow_region_expansion"):
            cards = self._deduplicate([*cards, *self._cards_from_markdown_samples()])

        cards, expanded = self._select_cards(cards, message, query)
        sources = self._build_sources(contexts, cards)
        warnings = self._build_warnings(query, degraded)

        if not cards:
            return TourismChatResponse(
                answer="조건에 맞는 관광지를 확인하지 못했습니다. 지역이나 접근성 조건을 조금 넓혀 다시 질문해 주세요.",
                cards=[],
                sources=sources,
                degraded=degraded,
                warnings=warnings,
            )

        answer = self._build_answer(cards, query, expanded=expanded)
        return TourismChatResponse(answer=answer, cards=cards, sources=sources, degraded=degraded, warnings=warnings)

    def _retrieve(self, message: str) -> tuple[list[dict], bool]:
        try:
            return self.retriever.retrieve(message), False
        except Exception as exc:
            logger.warning("관광 RAG 검색 실패, 로컬 샘플 fallback 사용: %s", exc.__class__.__name__)
            return [], True

    def _cards_from_contexts(self, contexts: list[dict]) -> list[TourismPlaceCard]:
        cards = []
        for context in contexts:
            card = self.card_codec.from_markdown(context.get("text") or "")
            if card:
                cards.append(card)
        return self._deduplicate(cards)

    def _cards_from_markdown_samples(self) -> list[TourismPlaceCard]:
        if self._sample_cards_cache is not None:
            return list(self._sample_cards_cache)

        sample_path = self.settings.resolved_tourism_sample_path
        cards = []
        for path in sorted(sample_path.glob("*.md")):
            card = self.card_codec.from_markdown(path.read_text(encoding="utf-8"))
            if card:
                cards.append(card)
        self._sample_cards_cache = self._deduplicate(cards)
        return list(self._sample_cards_cache)

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
            context_card = self.card_codec.from_markdown(context.get("text") or "")
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
    def _build_warnings(query: dict, degraded: bool) -> list[str]:
        warnings = []
        if degraded:
            warnings.append("검색 인덱스를 사용할 수 없어 로컬 샘플 기반 fallback 응답을 사용했습니다.")
        cache_warning = query.get("region_cache_warning")
        if cache_warning:
            warnings.append(str(cache_warning))
        return warnings

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
