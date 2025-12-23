import json
from typing import Any, Optional

from django.http import HttpRequest


def _parse_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely parse an integer, returning default on failure."""
    try:
        return int(value)
    except Exception:
        return default


def _parse_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely parse a float, returning default on failure."""
    try:
        return float(value)
    except Exception:
        return default


def _load_json_body(request: HttpRequest) -> Optional[dict]:
    """Load a JSON body from a Django request, returning None on failure."""
    try:
        body = request.body
    except Exception:
        body = b''

    if isinstance(body, (bytes, bytearray)):
        try:
            raw = body.decode('utf-8')
        except UnicodeDecodeError:
            return None
    else:
        raw = body

    if isinstance(raw, str):
        raw = raw.strip()

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
