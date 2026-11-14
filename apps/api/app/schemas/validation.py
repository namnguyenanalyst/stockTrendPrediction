"""Reject non-JSON numbers and unbounded nested data before database serialization."""

import json


def validate_json_payload(value):
    try:
        encoded = json.dumps(value, allow_nan=False, ensure_ascii=False)
    except (ValueError, TypeError, RecursionError):
        raise ValueError("Payload must contain finite JSON values") from None
    if len(encoded.encode("utf-8")) > 512_000:
        raise ValueError("JSON payload exceeds 512 KB")
    return value
