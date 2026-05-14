from __future__ import annotations

from pathlib import Path
import json
import sys

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.tour_api_service import TourAPIError, TourAPIService  # noqa: E402
from app.services.tourism_normalizer import TourismNormalizer  # noqa: E402
from app.services.tourism_query_service import TourismQueryService  # noqa: E402


TARGET_REGIONS = ["서울", "부산", "강릉"]
IMPORTANT_FIELDS = ["wheelchair", "parking", "restroom", "stroller", "lactationroom", "elevator", "route"]
RAW_OUTPUT_DIR = PROJECT_ROOT / "data" / "generated" / "tour_api"


def main() -> None:
    settings = get_settings()
    output_dir = settings.resolved_tourism_sample_path
    output_dir.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not settings.tour_api_service_key:
        print("TOUR_API_SERVICE_KEY가 없어 live TourAPI 샘플 수집은 건너뜁니다.")
        print(f"로컬 샘플 디렉터리: {settings.tourism_sample_path}")
        print("판정: 2차 검토 필요 - API 키 설정 후 live 수집을 다시 실행해야 합니다.")
        return

    api = TourAPIService(settings)
    normalizer = TourismNormalizer()
    query_service = TourismQueryService()
    summary: dict[str, dict[str, int]] = {}

    for region in TARGET_REGIONS:
        for old_path in output_dir.glob(f"{region}_*.md"):
            old_path.unlink()

    for region in TARGET_REGIONS:
        query = query_service.extract(region)
        area_code = str(query.get("area_code") or "")
        sigungu_code = query.get("sigungu_code")
        region_cards = []
        field_hits = {field: 0 for field in IMPORTANT_FIELDS}
        accessible_errors = 0
        skipped_without_accessibility = 0

        try:
            if not area_code:
                raise TourAPIError(f"{region} 지역코드를 찾을 수 없습니다.")
            list_items = api.accessible_area_based_list(
                area_code=area_code,
                sigungu_code=str(sigungu_code) if sigungu_code else None,
                num_of_rows=5,
            )
            raw_path = RAW_OUTPUT_DIR / f"{region}_area_based_raw.json"
            raw_path.write_text(json.dumps(list_items, ensure_ascii=False, indent=2), encoding="utf-8")

            for item in list_items:
                content_id = str(item.get("contentid") or "").strip()
                if not content_id:
                    continue
                common = api.detail_common(content_id) or item
                try:
                    accessible = api.detail_with_tour(content_id)
                except TourAPIError as exc:
                    accessible_errors += 1
                    accessible = {}
                    print(f"{region} {content_id} 무장애 상세 조회 실패: {exc}")
                card = normalizer.normalize_place(common, accessible)
                for field in IMPORTANT_FIELDS:
                    if field in card.raw_fields:
                        field_hits[field] += 1

                if not card.raw_fields:
                    skipped_without_accessibility += 1
                    continue

                region_cards.append(card)
                markdown_path = output_dir / f"{region}_{content_id}.md"
                markdown_path.write_text(normalizer.card_to_markdown(card), encoding="utf-8")

            normalized_path = RAW_OUTPUT_DIR / f"{region}_normalized_cards.json"
            normalized_path.write_text(
                json.dumps([card.model_dump() for card in region_cards], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            summary[region] = {
                "listed": len(list_items),
                "cards": len(region_cards),
                "accessible_errors": accessible_errors,
                "skipped_without_accessibility": skipped_without_accessibility,
                **field_hits,
            }
        except (TourAPIError, requests.RequestException, TimeoutError, ValueError) as exc:
            summary[region] = {"cards": 0, "error": 1}
            print(f"{region} 수집 실패: {exc}")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    enough_regions = sum(1 for result in summary.values() if result.get("cards", 0) >= 3)
    field_total = sum(result.get(field, 0) for result in summary.values() for field in IMPORTANT_FIELDS)
    if enough_regions >= 3 and field_total > 0:
        print("판정: 1차 진행 가능 - 무장애/가족 친화 필드를 포함한 샘플을 확보했습니다.")
    else:
        print("판정: 2차 검토 필요 - 지역별 3개 이상 카드 또는 핵심 편의정보가 부족합니다.")


if __name__ == "__main__":
    main()
