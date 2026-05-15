from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import Settings
from app.schemas.chat import Source
from app.schemas.tourism import TourismChatResponse, TourismPlaceCard
from app.services.llm_service import LLMService
from app.services.retriever import Retriever
from app.services.tour_api_service import TourAPIError, TourAPIService
from app.services.tourism_card_codec import TourismCardMarkdownCodec
from app.services.tourism_normalizer import TourismNormalizer
from app.services.tourism_query_event_logger import TourismQueryEventLogger
from app.services.tourism_query_service import FEATURE_KEYWORDS, TourismQueryService

logger = logging.getLogger(__name__)

REASONING_ASSIST_KEYWORDS = [
    "오래 걷",
    "걷기 힘",
    "비 오",
    "비가",
    "붐비지",
    "조용",
    "실내",
    "쉬기 좋은",
    "아이랑",
    "아이와",
    "가족이 같이",
    "멀지 않은",
    "가까운",
    "동선",
]


class TourismChatService:
    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        query_service: TourismQueryService,
        tour_api_service: TourAPIService | None = None,
        normalizer: TourismNormalizer | None = None,
        card_codec: TourismCardMarkdownCodec | None = None,
        event_logger: TourismQueryEventLogger | None = None,
        llm_service: LLMService | None = None,
    ):
        self.settings = settings
        self.retriever = retriever
        self.query_service = query_service
        self.tour_api_service = tour_api_service
        self.normalizer = normalizer or TourismNormalizer()
        self.card_codec = card_codec or TourismCardMarkdownCodec()
        self.event_logger = event_logger
        self.llm_service = llm_service
        self._sample_cards_cache: list[TourismPlaceCard] | None = None
        self._live_cards_cache: dict[str, list[TourismPlaceCard]] = {}
        self._live_markdown_cards_cache: list[TourismPlaceCard] | None = None

    def answer(self, message: str, session_id: str | None = None) -> TourismChatResponse:
        query = self.query_service.extract(message)
        if query.get("unsupported_intent"):
            response = TourismChatResponse(
                answer=(
                    "현재 MVP는 관광지의 무장애 접근성, 가족 편의, 위치 기반 추천을 우선 지원합니다. "
                    "휠체어 대여 가격 비교나 최저가 정보는 확인된 데이터가 없어 추천하지 않겠습니다. "
                    "대신 방문하려는 지역과 접근성 조건을 알려주면 갈 수 있는 관광지를 찾아드릴 수 있습니다."
                ),
                cards=[],
                sources=[],
                lookup_mode="unsupported",
                degraded=False,
                warnings=self._build_warnings(query, degraded=False),
            )
            self._log_event(message, session_id, query, response, live_api_called=False)
            return response
        if query.get("ambiguous_region"):
            response = TourismChatResponse(
                answer=self._build_region_clarification_answer(query),
                cards=[],
                sources=[],
                lookup_mode="clarification",
                degraded=False,
                warnings=self._build_warnings(query, degraded=False),
                suggested_messages=self._build_region_clarification_suggestions(query, message),
            )
            self._log_event(message, session_id, query, response, live_api_called=False)
            return response

        degraded = False
        lookup_mode = "unknown"
        contexts: list[dict] = []
        source_contexts: list[dict] = []
        cards: list[TourismPlaceCard] = []
        expanded = False
        live_api_called = False

        candidates = self._cards_from_live_markdown_cache(query)
        cards, expanded = self._select_stage_cards(candidates, message, query)
        if cards:
            lookup_mode = "cache"

        if not cards:
            contexts, retrieve_degraded = self._retrieve(message)
            degraded = degraded or retrieve_degraded
            candidates = self._cards_from_contexts(contexts)
            cards, expanded = self._select_stage_cards(candidates, message, query)
            if cards:
                lookup_mode = "indexed"
                source_contexts = contexts

        if not cards:
            candidates = self._cards_from_markdown_samples()
            cards, expanded = self._select_stage_cards(candidates, message, query)
            if cards:
                lookup_mode = "sample"

        if not cards:
            candidates, live_degraded, api_called = self._cards_from_live_tour_api(query)
            live_api_called = live_api_called or api_called
            degraded = degraded or live_degraded
            cards, expanded = self._select_stage_cards(candidates, message, query)
            if cards:
                lookup_mode = "live"

        sources = self._build_sources(source_contexts, cards)
        warnings = self._build_warnings(query, degraded)

        if not cards:
            response = TourismChatResponse(
                answer="조건에 맞는 관광지를 확인하지 못했습니다. 지역이나 접근성 조건을 조금 넓혀 다시 질문해 주세요.",
                cards=[],
                sources=sources,
                lookup_mode=lookup_mode,
                degraded=degraded,
                warnings=warnings,
            )
            self._log_event(message, session_id, query, response, live_api_called)
            return response

        cards, reasoning_used, reasoning_notes = self._apply_reasoning_assist(cards, message, query)
        answer = self._build_answer(cards, query, expanded=expanded, reasoning_notes=reasoning_notes)
        response = TourismChatResponse(
            answer=answer,
            cards=cards,
            sources=sources,
            lookup_mode=lookup_mode,
            degraded=degraded,
            warnings=warnings,
            reasoning_assist_used=reasoning_used,
            reasoning_assist_notes=reasoning_notes,
        )
        self._log_event(message, session_id, query, response, live_api_called)
        return response

    def _select_stage_cards(
        self,
        candidates: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> tuple[list[TourismPlaceCard], bool]:
        if not candidates:
            return [], False
        if query.get("allow_region_expansion"):
            candidates = self._deduplicate([*candidates, *self._cards_from_markdown_samples()])
        return self._select_cards(candidates, message, query)

    def _retrieve(self, message: str) -> tuple[list[dict], bool]:
        try:
            return self.retriever.retrieve(message), False
        except Exception as exc:
            logger.warning("관광 RAG 검색 실패, 로컬 샘플 fallback 사용: %s", exc.__class__.__name__)
            return [], True

    def _cards_from_live_tour_api(self, query: dict) -> tuple[list[TourismPlaceCard], bool, bool]:
        if not self._can_use_live_tour_api(query):
            return [], False, False

        cache_key = self._live_cache_key(query)
        if cache_key in self._live_cards_cache:
            return list(self._live_cards_cache[cache_key]), False, False

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
            return [], True, True

        self._live_cards_cache[cache_key] = self._deduplicate(cards)
        self._persist_live_cards(query, self._live_cards_cache[cache_key])
        return list(self._live_cards_cache[cache_key]), False, True

    def _log_event(
        self,
        message: str,
        session_id: str | None,
        query: dict,
        response: TourismChatResponse,
        live_api_called: bool,
    ) -> None:
        if self.event_logger:
            self.event_logger.log(
                message=message,
                session_id=session_id,
                query=query,
                response=response,
                live_api_called=live_api_called,
            )

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

    def _apply_reasoning_assist(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> tuple[list[TourismPlaceCard], bool, list[str]]:
        if not self._should_use_reasoning_assist(cards, message, query):
            return cards, False, []
        assert self.llm_service is not None
        try:
            payload = self._call_reasoning_assist(cards, message, query)
        except Exception as exc:  # noqa: BLE001 - reasoning assist must never break the main answer.
            logger.warning("관광 추론 보조 실패, 기존 카드 순서 유지: %s", exc.__class__.__name__)
            return cards, False, []

        ranked_cards = self._reorder_cards_by_reasoning(cards, payload.get("ranked_ids"))
        notes = self._normalize_reasoning_notes(payload)
        return ranked_cards, True, notes

    def _should_use_reasoning_assist(self, cards: list[TourismPlaceCard], message: str, query: dict) -> bool:
        if not self.settings.tourism_reasoning_assist_enabled:
            return False
        if not self.llm_service:
            return False
        if len(cards) < 2:
            return False
        if query.get("ambiguous_region") or query.get("unsupported_intent"):
            return False
        conditions = query.get("conditions") or []
        if len(conditions) >= 3:
            return True
        return any(keyword in message for keyword in REASONING_ASSIST_KEYWORDS)

    def _call_reasoning_assist(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> dict[str, Any]:
        prompt = self._build_reasoning_assist_prompt(cards, message, query)
        raw = self.llm_service.generate(prompt)
        return self._parse_reasoning_assist_json(raw)

    def _build_reasoning_assist_prompt(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> str:
        max_cards = max(self.settings.tourism_reasoning_assist_max_cards, 1)
        card_payload = []
        for index, card in enumerate(cards[:max_cards], start=1):
            card_payload.append(
                {
                    "id": card.content_id,
                    "rank": index,
                    "title": card.title,
                    "address": card.address,
                    "accessibility_tags": card.accessibility_tags,
                    "family_tags": card.family_tags,
                    "recommendation_reason": card.recommendation_reason,
                    "known_fields": card.raw_fields,
                }
            )
        payload = {
            "message": message,
            "region": query.get("region"),
            "conditions": query.get("conditions") or [],
            "features": query.get("features") or [],
            "cards": card_payload,
        }
        return (
            "너는 무장애 관광 챗봇의 후보 재랭킹 보조 계층이다.\n"
            "규칙:\n"
            "- 후보 카드에 없는 장소나 접근성 정보를 만들지 않는다.\n"
            "- 후보 카드 id만 ranked_ids에 넣는다.\n"
            "- 사용자의 복합 상황을 해석해 후보 순서와 확인 필요 메모만 정리한다.\n"
            "- 출력은 JSON 객체만 한다. Markdown 코드블록을 쓰지 않는다.\n\n"
            "입력 JSON:\n"
            f"{json.dumps(payload, ensure_ascii=False)}\n\n"
            "출력 JSON 형식:\n"
            "{\"ranked_ids\":[\"card-id\"],\"missing_or_uncertain\":[\"확인 필요 메모\"]}"
        )

    @staticmethod
    def _parse_reasoning_assist_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("추론 보조 JSON 객체를 찾지 못했습니다.")
        parsed = json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("추론 보조 응답이 JSON 객체가 아닙니다.")
        return parsed

    @staticmethod
    def _reorder_cards_by_reasoning(cards: list[TourismPlaceCard], ranked_ids: Any) -> list[TourismPlaceCard]:
        if not isinstance(ranked_ids, list):
            return cards
        by_id = {card.content_id: card for card in cards}
        ordered = []
        seen = set()
        for raw_id in ranked_ids:
            content_id = str(raw_id)
            if content_id in by_id and content_id not in seen:
                ordered.append(by_id[content_id])
                seen.add(content_id)
        return [*ordered, *[card for card in cards if card.content_id not in seen]]

    @staticmethod
    def _normalize_reasoning_notes(payload: dict[str, Any]) -> list[str]:
        notes = payload.get("missing_or_uncertain") or payload.get("notes") or []
        if isinstance(notes, str):
            notes = [notes]
        if not isinstance(notes, list):
            return []
        result = []
        for note in notes:
            text = str(note).strip()
            if text:
                result.append(text)
        return result[:3]

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

    def _cards_from_live_markdown_cache(self, query: dict) -> list[TourismPlaceCard]:
        if not query.get("area_code"):
            return []
        cards = self._filter_cards_by_query_region(self._load_live_markdown_cards(), query)
        return self._deduplicate(cards)

    def _load_live_markdown_cards(self) -> list[TourismPlaceCard]:
        if self._live_markdown_cards_cache is not None:
            return list(self._live_markdown_cards_cache)

        cache_path = self.settings.resolved_tourism_live_cache_path
        cards = []
        if cache_path.exists():
            for path in sorted(cache_path.glob("*.md")):
                card = self.card_codec.from_markdown(path.read_text(encoding="utf-8"))
                if card:
                    cards.append(card)
        self._live_markdown_cards_cache = self._deduplicate(cards)
        return list(self._live_markdown_cards_cache)

    def _persist_live_cards(self, query: dict, cards: list[TourismPlaceCard]) -> None:
        if not cards:
            return
        cache_path = self.settings.resolved_tourism_live_cache_path
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            for card in cards:
                path = cache_path / self._live_card_cache_filename(query, card)
                if not path.exists():
                    path.write_text(self.card_codec.to_markdown(card), encoding="utf-8")
            self._live_markdown_cards_cache = None
        except OSError as exc:
            logger.warning("관광 live Markdown 캐시 저장 실패: %s", exc.__class__.__name__)

    @staticmethod
    def _live_card_cache_filename(query: dict, card: TourismPlaceCard) -> str:
        area_name = str(query.get("area_name") or query.get("area_code") or "area")
        sigungu_name = str(query.get("sigungu_name") or query.get("sigungu_code") or "")
        region = "_".join(part for part in [area_name, sigungu_name] if part)
        safe_region = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", region).strip("_") or "area"
        safe_content_id = re.sub(r"[^0-9A-Za-z_-]+", "_", card.content_id).strip("_") or "unknown"
        return f"{safe_region}_{safe_content_id}.md"

    def _select_cards(
        self,
        cards: list[TourismPlaceCard],
        message: str,
        query: dict,
    ) -> tuple[list[TourismPlaceCard], bool]:
        region = query.get("region")
        if region and query.get("is_sigungu"):
            query_region_cards = self._filter_cards_by_query_region(cards, query)
            if query.get("features"):
                query_region_cards = self._filter_cards_by_features(query_region_cards, query)
                if not query_region_cards and not query.get("allow_region_expansion"):
                    return [], False
            region_cards = self._rank_cards(
                query_region_cards,
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
        feature_cards = self._filter_cards_by_features(cards, query)
        if feature_cards:
            cards = feature_cards

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
            for feature in query.get("features") or []:
                if feature in haystack:
                    value += 3
            for token in message.split():
                if len(token) >= 2 and token in haystack:
                    value += 1
            return value

        return sorted(cards, key=score, reverse=True)

    @staticmethod
    def _filter_cards_by_features(cards: list[TourismPlaceCard], query: dict) -> list[TourismPlaceCard]:
        features = query.get("features") or []
        if not features:
            return cards
        filtered = []
        for card in cards:
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
            if all(any(term in haystack for term in FEATURE_KEYWORDS.get(feature, [feature])) for feature in features):
                filtered.append(card)
        return filtered

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

    def _build_answer(
        self,
        cards: list[TourismPlaceCard],
        query: dict,
        expanded: bool = False,
        reasoning_notes: list[str] | None = None,
    ) -> str:
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
        if reasoning_notes:
            lines.append(f"복합 조건을 반영해 후보 순서를 조정했습니다. 확인 필요: {', '.join(reasoning_notes)}")
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
    def _build_region_clarification_suggestions(query: dict, message: str) -> list[str]:
        alias = query.get("ambiguous_region") or ""
        candidates = query.get("ambiguous_region_candidates") or []
        conditions = query.get("conditions") or ["무장애"]
        condition_text = " ".join(str(condition) for condition in conditions[:2])
        suggestions = []
        for candidate in candidates:
            area_name = candidate.get("area_name")
            sigungu_name = candidate.get("sigungu_name") or alias
            if area_name and sigungu_name:
                region_text = f"{area_name} {sigungu_name}"
                if alias and alias in message:
                    suggestions.append(message.replace(alias, region_text, 1))
                else:
                    suggestions.append(f"{region_text}에서 {condition_text} 관광지 추천해줘")
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
