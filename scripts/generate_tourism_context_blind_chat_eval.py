from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "eval" / "tourism_context_blind_chat_eval.jsonl"


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


def main() -> None:
    rows = build_rows()
    write_jsonl(DEFAULT_OUTPUT, rows)
    print(json.dumps({"output": str(DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
