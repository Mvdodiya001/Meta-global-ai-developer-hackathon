
#!/usr/bin/env python3

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.meta.ai/v1/responses"

MODELS = {
    "contributor": {
        "name": "muse-spark-1.3-contributor",
        "input": 0.10,
        "cached_input": 0.002,
        "output": 0.20,
    },
    "standard": {
        "name": "muse-spark-1.3",
        "input": 1.25,
        "cached_input": 0.15,
        "output": 4.25,
    },
}

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "meta_usage.jsonl"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def api_request(payload, model, run_id, stage):
    api_key = "API_KEY"
    # if not api_key:
    #     raise RuntimeError(
    #         "MODEL_API_KEY is missing. Export your Meta API key first."
    #     )

    payload["model"] = model
    body = json.dumps(payload).encode("utf-8")

    request = Request(
        BASE_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    started = time.monotonic()

    try:
        with urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            status = response.status

    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Meta API HTTP {exc.code}: {detail[:2000]}"
        ) from exc

    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Meta API request failed: {exc}") from exc

    latency_ms = round((time.monotonic() - started) * 1000, 2)
    result = json.loads(raw)

    if status < 200 or status >= 300:
        raise RuntimeError(f"Unexpected HTTP status: {status}")

    usage = result.get("usage") or {}

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    total_tokens = int(
        usage.get("total_tokens", input_tokens + output_tokens) or 0
    )

    cached_tokens = int(
        (usage.get("input_tokens_details") or {}).get(
            "cached_tokens", 0
        ) or 0
    )
    cached_tokens = min(cached_tokens, input_tokens)

    prices = next(
        (p for p in MODELS.values() if p["name"] == model),
        None,
    )

    estimated_cost = None
    if prices is not None and "usage" in result:
        uncached_tokens = input_tokens - cached_tokens
        estimated_cost = (
            uncached_tokens * prices["input"]
            + cached_tokens * prices["cached_input"]
            + output_tokens * prices["output"]
        ) / 1_000_000

    record = {
        "timestamp": utc_now(),
        "run_id": run_id,
        "stage": stage,
        "model": model,
        "http_status": status,
        "response_id": result.get("id"),
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost,
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")

    cost_text = (
        f"${estimated_cost:.8f}"
        if estimated_cost is not None
        else "unknown (usage not returned)"
    )

    print(
        f"[{stage}] HTTP {status} | "
        f"in={input_tokens} cached={cached_tokens} "
        f"out={output_tokens} total={total_tokens} | "
        f"cost={cost_text} | {latency_ms} ms"
    )

    return result


def get_function_call(response):
    for item in response.get("output", []):
        if item.get("type") == "function_call":
            return item

    return None


def get_output_text(response):
    texts = []

    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))

    return "\n".join(texts)


def calculator(arguments):
    # Deliberately expose a small, safe function for this test.
    # Never use eval() on model-generated arguments.
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a JSON object.")

    a = arguments.get("a")
    b = arguments.get("b")

    if (
        isinstance(a, bool)
        or isinstance(b, bool)
        or not isinstance(a, (int, float))
        or not isinstance(b, (int, float))
    ):
        raise ValueError("a and b must be numbers.")

    if abs(a) > 1_000_000 or abs(b) > 1_000_000:
        raise ValueError("Numbers exceed the test limit.")

    return {"result": a + b}


def main():
    mode = os.getenv("META_MODE", "standard").lower()

    if mode not in MODELS:
        raise ValueError(
            "META_MODE must be 'contributor' or 'standard'."
        )

    model = MODELS[mode]["name"]
    run_id = str(uuid.uuid4())

    print(f"Run: {run_id}")
    print(f"Mode: {mode}")
    print(f"Model: {model}")

    tool = {
        "type": "function",
        "name": "add_numbers",
        "description": "Add two numbers and return their sum.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    # Request 1: ask the model to call our function.
    first = api_request(
        {
            "input": (
                "Call add_numbers with a=19 and b=23. "
                "Do not calculate the answer yourself."
            ),
            "tools": [tool],
            "tool_choice": "auto",
            "parallel_tool_calls": False,
        },
        model,
        run_id,
        "tool_call",
    )

    call = get_function_call(first)

    if not call:
        raise RuntimeError(
            "No function_call returned. Inspect the API response."
        )

    if call.get("name") != "add_numbers":
        raise RuntimeError(
            f"Unexpected function: {call.get('name')}"
        )

    call_id = call.get("call_id")
    if not call_id:
        raise RuntimeError("Function call is missing call_id.")

    arguments = json.loads(call.get("arguments", "{}"))
    tool_result = calculator(arguments)

    print("Function:", call["name"])
    print("Arguments:", json.dumps(arguments))
    print("Local result:", json.dumps(tool_result))

    # Request 2: give the real function result back to the model.
    second = api_request(
        {
            "previous_response_id": first["id"],
            "input": [
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(tool_result),
                }
            ],
        },
        model,
        run_id,
        "tool_result",
    )

    final_text = get_output_text(second)

    if not final_text.strip():
        raise RuntimeError(
            "The second response returned no output_text."
        )

    print("\nFinal model response:")
    print(final_text)

    print(f"\nUsage log: {LOG_FILE}")
    print("PASS: function-call round trip completed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
