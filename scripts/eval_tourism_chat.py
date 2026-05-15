from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_INPUT = PROJECT_ROOT / "data" / "eval" / "tourism_20_questions.jsonl"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "generated" / "tour_api" / "eval_runs"


def load_eval_items(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        if "id" not in item or "message" not in item:
            raise ValueError(f"{path}:{line_number} must include id and message")
        items.append(item)
    return items


def post_tourism_chat(base_url: str, message: str, session_id: str, timeout: float) -> tuple[int, dict[str, Any]]:
    payload = json.dumps({"message": message, "session_id": session_id}).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/tourism/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed: dict[str, Any] = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"error": body}
        return exc.code, parsed


def post_tourism_chat_direct(message: str, session_id: str) -> tuple[int, dict[str, Any]]:
    from fastapi.testclient import TestClient

    from app.main import app

    payload = {"message": message, "session_id": session_id}
    with TestClient(app) as client:
        response = client.post("/tourism/chat", json=payload)
    return response.status_code, response.json()


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_eval(
    input_path: Path,
    base_url: str,
    output_path: Path,
    timeout: float,
    direct: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in load_eval_items(input_path):
        started = time.perf_counter()
        status_code = 0
        response_body: dict[str, Any]
        error_message: str | None = None
        try:
            session_id = f"eval-{item['id']}"
            if direct:
                status_code, response_body = post_tourism_chat_direct(
                    message=item["message"],
                    session_id=session_id,
                )
            else:
                status_code, response_body = post_tourism_chat(
                    base_url=base_url,
                    message=item["message"],
                    session_id=session_id,
                    timeout=timeout,
                )
        except Exception as exc:  # noqa: BLE001 - eval runner must keep going.
            response_body = {}
            error_message = str(exc)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        results.append(
            {
                "id": item["id"],
                "category": item.get("category"),
                "message": item["message"],
                "expected_region": item.get("expected_region"),
                "expected_conditions": item.get("expected_conditions", []),
                "expected_behavior": item.get("expected_behavior"),
                "scoring_focus": item.get("scoring_focus", []),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "lookup_mode": response_body.get("lookup_mode"),
                "degraded": response_body.get("degraded"),
                "warnings": response_body.get("warnings", []),
                "card_count": len(response_body.get("cards", [])),
                "suggested_message_count": len(response_body.get("suggested_messages", [])),
                "answer": response_body.get("answer"),
                "response": response_body,
                "error": error_message,
            }
        )
        print(f"{item['id']} {status_code} {duration_ms}ms cards={results[-1]['card_count']} mode={results[-1]['lookup_mode']}")
    write_jsonl(output_path, results)
    return results


def default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"tourism_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the tourism 20-question eval set against /tourism/chat.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--base-url", default=os.environ.get("TOURISM_EVAL_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--output", type=Path, default=default_output_path())
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Call the FastAPI app in-process with TestClient instead of requiring a running server.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_eval(
        input_path=args.input,
        base_url=args.base_url,
        output_path=args.output,
        timeout=args.timeout,
        direct=args.direct,
    )
    failures = [row for row in results if row["status_code"] >= 400 or row["error"]]
    print(f"\nWrote {len(results)} rows to {args.output}")
    print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
