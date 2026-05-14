from app.schemas.tourism import TourismPlaceCard
from app.services.tourism_normalizer import TourismNormalizer
from scripts.fetch_accessible_tourism_samples import collect_existing_content_ids


def test_collect_existing_content_ids_reads_sample_and_live_cache_dirs(tmp_path):
    sample_dir = tmp_path / "samples"
    live_cache_dir = tmp_path / "live_cache"
    sample_dir.mkdir()
    live_cache_dir.mkdir()
    normalizer = TourismNormalizer()

    sample_card = TourismPlaceCard(
        content_id="sample-1",
        title="샘플 관광지",
        address="서울 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    live_card = TourismPlaceCard(
        content_id="live-1",
        title="라이브 캐시 관광지",
        address="부산 중구",
        recommendation_reason="휠체어 접근 정보가 확인되었습니다.",
        accessibility_tags=["휠체어 접근"],
    )
    (sample_dir / "sample.md").write_text(normalizer.card_to_markdown(sample_card), encoding="utf-8")
    (live_cache_dir / "live.md").write_text(normalizer.card_to_markdown(live_card), encoding="utf-8")

    assert collect_existing_content_ids([sample_dir, live_cache_dir], normalizer.codec) == {"sample-1", "live-1"}
