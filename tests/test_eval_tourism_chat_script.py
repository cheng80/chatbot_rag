import json

import pytest

from scripts.eval_tourism_chat import load_eval_items, write_jsonl


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
