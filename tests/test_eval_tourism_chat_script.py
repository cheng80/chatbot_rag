import json

import pytest

from scripts import eval_tourism_chat
from scripts.eval_tourism_chat import load_eval_items, run_eval, write_jsonl


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
    assert "서울 휠체어 관광지 추천" in output.read_text(encoding="utf-8")
