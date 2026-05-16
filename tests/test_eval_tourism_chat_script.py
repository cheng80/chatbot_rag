import json

import pytest

from scripts import eval_tourism_chat
from scripts.eval_tourism_chat import classify_eval_failures, load_eval_items, run_eval, write_jsonl


def test_load_eval_items_requires_id_and_message(tmp_path):
    eval_file = tmp_path / "eval.jsonl"
    eval_file.write_text(json.dumps({"id": "TQ001"}, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError):
        load_eval_items(eval_file)


def test_write_jsonl_keeps_korean_text(tmp_path):
    output = tmp_path / "nested" / "result.jsonl"
    write_jsonl(output, [{"id": "TQ001", "message": "서울 휠체어 관광지 추천"}])

    saved = output.read_text(encoding="utf-8")
    assert "서울 휠체어 관광지 추천" in saved


def test_run_eval_direct_uses_in_process_client(monkeypatch, tmp_path):
    eval_file = tmp_path / "eval.jsonl"
    output = tmp_path / "result.jsonl"
    eval_file.write_text(
        json.dumps(
            {
                "id": "TQ001",
                "message": "서울 휠체어 관광지 추천",
                "category": "smoke",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_post_tourism_chat_direct(message: str, session_id: str):
        assert message == "서울 휠체어 관광지 추천"
        assert session_id == "eval-TQ001"
        return 200, {"answer": "ok", "cards": [{"title": "sample"}], "lookup_mode": "sample"}

    monkeypatch.setattr(eval_tourism_chat, "post_tourism_chat_direct", fake_post_tourism_chat_direct)

    rows = run_eval(eval_file, "http://unused.test", output, timeout=1.0, direct=True)

    assert rows[0]["status_code"] == 200
    assert rows[0]["card_count"] == 1
    assert rows[0]["lookup_mode"] == "sample"
    assert rows[0]["passed"] is True
    assert "서울 휠체어 관광지 추천" in output.read_text(encoding="utf-8")


def test_classify_eval_failures_detects_wrong_region_and_missing_terms():
    item = {
        "must_not_include_regions": ["울산광역시 중구"],
        "must_contain_answer_terms": ["출처"],
        "min_cards": 1,
    }
    response = {
        "answer": "부산 중구 기준 추천입니다.",
        "cards": [{"title": "울산중구어린이역사과학체험관", "address": "울산광역시 중구"}],
    }

    failures = classify_eval_failures(item, 200, response, None)

    assert "wrong_region_card" in failures
    assert "answer_missing_term" in failures


def test_classify_eval_failures_checks_card_terms_and_first_card():
    item = {
        "must_include_any_card_terms": [["점자블록", "오디오가이드"]],
        "first_card_must_include_any_terms": ["박물관", "전시관"],
        "must_not_include_card_terms": [["호텔", "숙박"]],
        "must_include_answer_any_terms": ["확인했습니다", "추천합니다"],
        "min_suggestions": 1,
    }
    response = {
        "answer": "조건에 맞는 곳을 추천합니다.",
        "cards": [
            {"title": "서울 전시관", "raw_fields": {"시각장애 편의": "점자블록 있음"}},
            {"title": "서울 호텔", "raw_fields": {"숙박": "객실 있음"}},
        ],
        "suggested_messages": [],
    }

    failures = classify_eval_failures(item, 200, response, None)

    assert "card_contains_forbidden_terms" in failures
    assert "suggestion_count_low" in failures
    assert "card_missing_required_terms" not in failures
    assert "first_card_missing_required_terms" not in failures
    assert "answer_missing_any_term" not in failures


def test_run_eval_records_failure_reasons(monkeypatch, tmp_path):
    eval_file = tmp_path / "eval.jsonl"
    output = tmp_path / "result.jsonl"
    eval_file.write_text(
        json.dumps(
            {
                "id": "TQ001",
                "message": "서울 휠체어 관광지 추천",
                "min_cards": 2,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_post_tourism_chat_direct(message: str, session_id: str):
        return 200, {"answer": "ok", "cards": [{"title": "sample"}], "lookup_mode": "sample"}

    monkeypatch.setattr(eval_tourism_chat, "post_tourism_chat_direct", fake_post_tourism_chat_direct)

    rows = run_eval(eval_file, "http://unused.test", output, timeout=1.0, direct=True)

    assert rows[0]["passed"] is False
    assert rows[0]["failure_reasons"] == ["card_count_low"]
