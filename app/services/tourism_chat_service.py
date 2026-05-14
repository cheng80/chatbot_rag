from __future__ import annotations

import logging

from app.core.config import Settings
from app.schemas.chat import Source
from app.schemas.tourism import TourismChatResponse, TourismPlaceCard
from app.services.retriever import Retriever
from app.services.tour_api_service import TourAPIError, TourAPIService
from app.services.tourism_card_codec import TourismCardMarkdownCodec
from app.services.tourism_normalizer import TourismNormalizer
from app.services.tourism_query_service import TourismQueryService

logger = logging.getLogger(__name__)


class TourismChatService:
    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        query_service: TourismQueryService,
        tour_api_service: TourAPIService | None = None,
        normalizer: TourismNormalizer | None = None,
        card_codec: TourismCardMarkdownCodec | None = None,
    ):
        self.settings = settings
        self.retriever = retriever
        self.query_service = query_service
        self.tour_api_service = tour_api_service
        self.normalizer = normalizer or TourismNormalizer()
        self.card_codec = card_codec or TourismCardMarkdownCodec()
        self._sample_cards_cache: list[TourismPlaceCard] | None = None
        self._live_cards_cache: dict[str, list[TourismPlaceCard]] = {}

    def answer(self, message: str, session_id: str | None = None) -> TourismChatResponse:
        query = self.query_service.extract(message)
        if query.get("ambiguous_region"):
            return TourismChatResponse(
                answer=self._build_region_clarification_answer(query),
                cards=[],
                sources=[],
                lookup_mode="clarification",
                degraded=False,
                warnings=self._build_warnings(query, degraded=False),
                suggested_messages=self._build_region_clarification_suggestions(query),
            )

        contexts: list[dict] = []
        cards, degraded = self._cards_from_live_tour_api(query)
        lookup_mode = "live" if cards else "unknown"

        if not cards:
            contexts, retrieve_degraded = self._retrieve(message)
            degraded = degraded or retrieve_degraded
            cards = self._cards_from_contexts(contexts)
            if cards:
                lookup_mode = "indexed"

        if not cards:
            cards = self._cards_from_markdown_samples()
            degraded = degraded or bool(cards)
            if cards:
                lookup_mode = "sample"
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
                lookup_mode=lookup_mode,
                degraded=degraded,
                warnings=warnings,
            )

        answer = self._build_answer(cards, query, expanded=expanded)
        return TourismChatResponse(
            answer=answer,
            cards=cards,
            sources=sources,
            lookup_mode=lookup_mode,
            degraded=degraded,
            warnings=warnings,
        )

    def _retrieve(self, message: str) -> tuple[list[dict], bool]:
        try:
            return self.retriever.retrieve(message), False
        except Exception as exc:
            logger.warning("관광 RAG 검색 실패, 로컬 샘플 fallback 사용: %s", exc.__class__.__name__)
            return [], True

    def _cards_from_live_tour_api(self, query: dict) -> tuple[list[TourismPlaceCard], bool]:
        if not self._can_use_live_tour_api(query):
            return [], False

        cache_key = self._live_cache_key(query)
        if cache_key in self._live_cards_cache:
            return list(self._live_cards_cache[cache_key]), False

        api = self.tour_api_service
        assert api is not None
        try:
            list_items = api.accessible_area_based_list(
                area_code=str(query.get("area_code") or ""),
                sigungu_code=str(query.get("sigungu_code")) if query.get("sigungu_code") else None,
                num_of_rows=self.settings.tourism_live_rows,
            )
            cards = self._normalize_live_items(list_items)
        except (TourAPIError, TimeoutError, ValueError) as exc:
            logger.warning("관광 live TourAPI 조회 실패, RAG fallback 사용: %s", exc.__class__.__name__)
            return [], True

        self._live_cards_cache[cache_key] = self._deduplicate(cards)
        return list(self._live_cards_cache[cache_key]), False

    def _can_use_live_tour_api(self, query: dict) -> bool:
        if not self.settings.tourism_live_lookup_enabled:
            return False
        if not self.tour_api_service:
            return False
        if not query.get("area_code"):
            return False
        return bool(self.settings.tour_api_service_key)

    def _normalize_live_items(self, list_items: list[dict]) -> list[TourismPlaceCard]:
        cards = []
        detail_calls = 0
        max_detail_calls = max(self.settings.tourism_live_max_detail_calls, 0)
        api = self.tour_api_service
        assert api is not None

        for item in list_items:
            content_id = str(item.get("contentid") or "").strip()
            if not content_id or detail_calls + 2 > max_detail_calls:
                continue
            try:
                detail_calls += 1
                common = api.detail_common(content_id) or item
                detail_calls += 1
                accessible = api.detail_with_tour(content_id)
            except TourAPIError as exc:
                logger.info("관광 live 상세 조회 일부 실패: %s (%s)", content_id, exc.__class__.__name__)
                continue
            card = self.normalizer.normalize_place(common, accessible)
            if card.raw_fields:
                cards.append(card)
        return cards

    @staticmethod
    def _live_cache_key(query: dict) -> str:
        return ":".join([str(query.get("area_code") or ""), str(query.get("sigungu_code") or "")])

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
                self._filter_cards_by_query_region(cards, query),
                message,
                query,
                filter_region=False,
            )
            if not query.get("allow_region_expansion"):
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

    @staticmethod
    def _filter_cards_by_query_region(cards: list[TourismPlaceCard], query: dict) -> list[TourismPlaceCard]:
        region = query.get("region")
        sigungu_name = query.get("sigungu_name")
        if not region:
            return cards
        terms = [sigungu_name] if sigungu_name else [region]
        filtered = []
        for card in cards:
            haystack = f"{card.title} {card.address or ''}"
            if all(term in haystack for term in terms):
                filtered.append(card)
        return filtered

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

    @staticmethod
    def _build_region_clarification_answer(query: dict) -> str:
        alias = query.get("ambiguous_region") or "해당 지역"
        candidates = query.get("ambiguous_region_candidates") or []
        options = []
        for candidate in candidates:
            area_name = candidate.get("area_name")
            sigungu_name = candidate.get("sigungu_name") or alias
            if area_name and sigungu_name:
                options.append(f"{area_name} {sigungu_name}")
        option_text = ", ".join(dict.fromkeys(options))
        if not option_text:
            return f"'{alias}' 지역이 여러 곳에 있어 어느 지역인지 먼저 알려 주세요."
        return (
            f"'{alias}'는 여러 시도에 있는 지명이라 바로 추천하기 어렵습니다. "
            f"어느 지역인지 함께 적어 주세요. 예: {option_text}"
        )

    @staticmethod
    def _build_region_clarification_suggestions(query: dict) -> list[str]:
        alias = query.get("ambiguous_region") or ""
        candidates = query.get("ambiguous_region_candidates") or []
        conditions = query.get("conditions") or ["무장애"]
        condition_text = " ".join(str(condition) for condition in conditions[:2])
        suggestions = []
        for candidate in candidates:
            area_name = candidate.get("area_name")
            sigungu_name = candidate.get("sigungu_name") or alias
            if area_name and sigungu_name:
                suggestions.append(f"{area_name} {sigungu_name}에서 {condition_text} 관광지 추천해줘")
        return list(dict.fromkeys(suggestions))

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
            warnings.append("live TourAPI 또는 검색 인덱스를 사용할 수 없어 캐시/로컬 샘플 기반 fallback 응답을 사용했습니다.")
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
