from __future__ import annotations

import json
from pathlib import Path
import argparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "eval" / "tourism_context_blind_chat_eval.jsonl"
DEFAULT_OUTPUT_V2 = PROJECT_ROOT / "data" / "eval" / "tourism_context_blind_chat_eval_v2.jsonl"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_rows() -> list[dict]:
    return [
        {
            "id": "TCBLIND001",
            "category": "blind_chat_required_facility",
            "message": "서울 중구에서 휠체어 접근 가능하고 장애인 화장실도 확인된 카드만 보고 싶다",
            "min_cards": 1,
            "must_include_any_card_terms": [["휠체어", "무장애", "경사로", "출입통로", "장애인 화장실", "화장실"]],
            "must_contain_answer_terms": ["서울"],
            "scoring_focus": ["required facility evidence", "region retention"],
        },
        {
            "id": "TCBLIND002",
            "category": "blind_chat_family_soft",
            "message": "부산 중구에서 아이랑 편한 분위기면 충분하고 수유실은 있으면 고맙고 없으면 말고",
            "min_cards": 1,
            "must_include_answer_any_terms": ["부산", "중구"],
            "scoring_focus": ["soft family condition", "no unsupported strict filtering"],
        },
        {
            "id": "TCBLIND003",
            "category": "blind_chat_or_condition",
            "message": "대구에서 수어 안내나 자막 안내 중 확인되는 쪽이면 돼",
            "min_cards": 0,
            "must_include_answer_any_terms": ["대구", "수어", "자막", "확인"],
            "scoring_focus": ["OR sensory condition", "answer transparency"],
        },
        {
            "id": "TCBLIND004",
            "category": "blind_chat_mobility",
            "message": "제주시에서 무릎이 안 좋아서 오르막 적은 곳 위주로 추천해줘",
            "min_cards": 1,
            "must_include_answer_any_terms": ["제주", "이동", "경사로", "휠체어", "접근"],
            "scoring_focus": ["implicit mobility context"],
        },
        {
            "id": "TCBLIND005",
            "category": "blind_chat_exclude",
            "message": "전주에서 시장 골목 말고 조용한 곳만 보고 싶어",
            "min_cards": 1,
            "must_not_include_card_terms": ["시장"],
            "must_include_answer_any_terms": ["전주", "시장"],
            "scoring_focus": ["negative place preference"],
        },
        {
            "id": "TCBLIND006",
            "category": "blind_chat_negative_near_miss",
            "message": "서울에서 주차 말고 주제가 독특한 박물관 추천해줘",
            "min_cards": 1,
            "must_not_include_answer_terms": ["장애인 주차가 확인"],
            "scoring_focus": ["facility word negated", "theme preference"],
        },
        {
            "id": "TCBLIND007",
            "category": "blind_chat_multiturn_replace",
            "turns": [
                {
                    "message": "부산 중구에서 시장 위주로 추천해줘",
                    "min_cards": 1,
                    "must_include_answer_any_terms": ["부산", "중구"],
                },
                {
                    "message": "시장 위주였던 건 취소하고 실내 전시 쪽으로 다시 추천해줘",
                    "min_cards": 0,
                    "must_not_include_card_terms": ["시장"],
                    "must_include_answer_any_terms": ["실내", "전시", "후보", "조건"],
                },
            ],
            "scoring_focus": ["multi-turn replacement", "previous preference removal"],
        },
        {
            "id": "TCBLIND008",
            "category": "blind_chat_multiturn_add",
            "turns": [
                {
                    "message": "서울 중구에서 관광지 추천해줘",
                    "min_cards": 1,
                    "must_include_answer_any_terms": ["서울", "중구"],
                },
                {
                    "message": "위 카드들 중 주차 문구가 확인되는 것만 남겨줘",
                    "min_cards": 0,
                    "must_include_answer_any_terms": ["주차", "확인", "조건"],
                },
            ],
            "scoring_focus": ["multi-turn add condition", "required evidence explanation"],
        },
        {
            "id": "TCBLIND009",
            "category": "blind_chat_region_clarify",
            "message": "중구에서 엘베 있으면 좋다가 아니라 엘리베이터 확인된 카드만",
            "expect_clarification": True,
            "expect_no_cards": True,
            "scoring_focus": ["ambiguous region", "facility requirement"],
        },
        {
            "id": "TCBLIND010",
            "category": "blind_chat_low_coverage",
            "message": "계룡시에서 전동 스쿠터로 움직여도 동선이 끊기지 않는 곳",
            "min_cards": 0,
            "must_include_answer_any_terms": ["계룡", "부족", "확인", "후보"],
            "scoring_focus": ["low coverage", "implicit mobility"],
        },
    ]


def build_rows_v2() -> list[dict]:
    return [
        {
            "id": "TCBLINDV2-001",
            "category": "chat_required_all_facilities",
            "message": "서울 중구에서 장애인 주차랑 장애인 화장실 둘 다 확인되는 관광지 추천해줘",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["서울", "중구"],
            "must_include_any_card_terms": [["주차", "화장실", "장애인"]],
            "scoring_focus": ["strict facility evidence", "region precision"],
        },
        {
            "id": "TCBLINDV2-002",
            "category": "chat_or_sensory",
            "message": "경기도 성남시에서 수어 안내나 자막 안내 중 하나라도 확인되는 곳",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["성남"],
            "must_include_any_card_terms": [["수어", "수화", "자막", "영상안내", "문자안내"]],
            "scoring_focus": ["OR sensory evidence", "no strict both requirement"],
        },
        {
            "id": "TCBLINDV2-003",
            "category": "chat_soft_condition",
            "message": "부산 중구에서 아이랑 편하면 좋고 수유실은 후보 많을 때만 참고해",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["부산", "중구"],
            "scoring_focus": ["soft family condition", "avoid over-filtering"],
        },
        {
            "id": "TCBLINDV2-004",
            "category": "chat_negative_facility_near_miss",
            "message": "서울에서 주차 말고 주제가 독특한 박물관이나 전시관 추천해줘",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["서울"],
            "must_not_contain_answer_terms": ["장애인 주차가 확인"],
            "first_card_must_include_any_terms": ["박물관", "전시관", "미술관", "갤러리", "전시"],
            "scoring_focus": ["facility word negation", "theme preference"],
        },
        {
            "id": "TCBLINDV2-005",
            "category": "chat_exclude_preference",
            "message": "부산 중구에서 시장 말고 휠체어로 갈 수 있는 관광지",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["부산", "중구"],
            "must_include_any_card_terms": [["휠체어", "장애인", "무장애"]],
            "must_not_include_card_terms": [["시장", "먹자골목"]],
            "scoring_focus": ["exclude market", "accessibility fit"],
        },
        {
            "id": "TCBLINDV2-006",
            "category": "chat_wrong_premise",
            "message": "서울 강남구에서 해수욕장 휠체어 관광지 추천해줘",
            "expect_no_cards": True,
            "must_include_answer_any_terms": ["확인하지 못했습니다", "조건에 맞는"],
            "scoring_focus": ["wrong premise", "no hallucinated beach"],
        },
        {
            "id": "TCBLINDV2-007",
            "category": "chat_unsupported_pure",
            "message": "오늘 환율 알려줘",
            "expected_lookup_mode": "unsupported",
            "expect_no_cards": True,
            "must_include_answer_any_terms": ["현재 MVP", "범위"],
            "scoring_focus": ["unsupported boundary", "no context leakage"],
        },
        {
            "id": "TCBLINDV2-008",
            "category": "chat_unsupported_negated",
            "turns": [
                {
                    "message": "부산 중구에서 휠체어 관광지 추천해줘",
                    "min_cards": 1,
                    "must_contain_answer_terms": ["부산", "중구"],
                },
                {
                    "message": "응급실은 말고 관광지만 계속",
                    "min_cards": 1,
                    "must_contain_answer_terms": ["부산", "중구"],
                    "must_include_any_card_terms": [["휠체어", "장애인", "무장애"]],
                },
            ],
            "scoring_focus": ["negated unsupported keyword", "context retention"],
        },
        {
            "id": "TCBLINDV2-009",
            "category": "chat_multiturn_reset_condition",
            "turns": [
                {
                    "message": "강릉에서 보조견 동반 가능한 관광지 추천해줘",
                    "min_cards": 1,
                    "must_contain_answer_terms": ["강릉"],
                },
                {
                    "message": "수어 안내나 자막 안내 있는 곳으로 다시 찾아줘",
                    "expect_no_cards": True,
                    "min_suggestions": 1,
                    "must_include_answer_any_terms": ["강릉", "확인하지 못했습니다", "조건"],
                },
            ],
            "scoring_focus": ["condition reset", "empty-result recovery suggestion"],
        },
        {
            "id": "TCBLINDV2-010",
            "category": "chat_multiturn_replace_region",
            "turns": [
                {
                    "message": "강릉에서 휠체어 관광지 추천해줘",
                    "min_cards": 1,
                    "must_contain_answer_terms": ["강릉"],
                },
                {
                    "message": "강릉 말고 서울 중구로 바꿔줘",
                    "min_cards": 1,
                    "must_contain_answer_terms": ["서울", "중구"],
                    "must_not_include_regions": ["강릉"],
                },
            ],
            "scoring_focus": ["region replacement", "no previous sigungu leakage"],
        },
        {
            "id": "TCBLINDV2-011",
            "category": "chat_ambiguous_region",
            "message": "중구에서 엘리베이터 확인된 관광지 추천해줘",
            "expect_clarification": True,
            "expect_no_cards": True,
            "must_include_answer_any_terms": ["어느", "중구", "지역"],
            "scoring_focus": ["ambiguous region clarification"],
        },
        {
            "id": "TCBLINDV2-012",
            "category": "chat_legacy_region",
            "message": "남제주군에서 유모차로 갈 수 있는 실내 관광지 추천해줘",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["서귀포시"],
            "must_include_any_card_terms": [["유모차", "수유실", "영유아", "기저귀", "실내", "박물관", "전시관"]],
            "scoring_focus": ["legacy region mapping", "family condition"],
        },
        {
            "id": "TCBLINDV2-013",
            "category": "chat_specific_facility",
            "message": "대구에서 점자블록이 실제 편의정보에 있는 카드만",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["대구"],
            "must_include_any_card_terms": [["점자블록", "점자"]],
            "scoring_focus": ["specific facility evidence"],
        },
        {
            "id": "TCBLINDV2-014",
            "category": "chat_low_coverage_no_hallucination",
            "message": "계룡시에서 수어 안내나 자막 안내 확인되는 곳",
            "expect_no_cards": True,
            "min_suggestions": 1,
            "must_include_answer_any_terms": ["계룡", "확인하지 못했습니다", "조건"],
            "scoring_focus": ["low coverage", "no unsupported cards", "suggestions"],
        },
        {
            "id": "TCBLINDV2-015",
            "category": "chat_preference_ranking",
            "message": "서울에서 비 오는 날 휠체어로 갈 실내 전시나 박물관 위주로",
            "min_cards": 1,
            "max_cards": 5,
            "must_contain_answer_terms": ["서울"],
            "first_card_must_include_any_terms": ["박물관", "전시관", "미술관", "갤러리", "실내"],
            "scoring_focus": ["soft preference ranking", "indoor museum priority"],
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["v1", "v2"], default="v1")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    rows = build_rows_v2() if args.variant == "v2" else build_rows()
    output = args.output or (DEFAULT_OUTPUT_V2 if args.variant == "v2" else DEFAULT_OUTPUT)
    write_jsonl(output, rows)
    print(json.dumps({"output": str(output.relative_to(PROJECT_ROOT)), "variant": args.variant, "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
