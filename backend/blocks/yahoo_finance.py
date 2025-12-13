import logging
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote"
_USER_AGENT = "PlaygroundMiner/1.0"
_DEFAULT_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept": "application/json",
}


def _ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware datetime in UTC for API calls."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_numeric(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        # Yahoo quote endpoints sometimes wrap numbers in {"raw": 0.05, "fmt": "5%"}
        for key in ("raw", "fmt"):
            inner = value.get(key)
            parsed = _extract_numeric(inner)
            if parsed is not None:
                return parsed
        return None
    if isinstance(value, str):
        cleaned = value.strip().replace("%", "")
        try:
            number = float(cleaned)
        except ValueError:
            return None
        if value.endswith("%"):
            return number / 100.0
        return number
    return None


def fetch_price_history(
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    *,
    interval: str = "1mo",
    auto_adjust: bool = True,
    timeout: int = 15,
) -> List[Tuple[datetime, float]]:
    """Fetch historical prices from Yahoo Finance's chart endpoint."""
    if not symbol:
        return []

    start_ts = int(_ensure_utc(start_dt).timestamp())
    end_ts = int(_ensure_utc(end_dt).timestamp())
    if end_ts <= start_ts:
        end_ts = start_ts + 86400

    params = {
        "period1": start_ts,
        "period2": end_ts,
        "interval": interval,
        "includePrePost": "false",
        "events": "div,splits",
        "includeAdjustedClose": "true",
    }

    url = _CHART_URL.format(symbol=quote_plus(symbol.strip()))
    response = requests.get(url, params=params, timeout=timeout, headers=_DEFAULT_HEADERS)
    response.raise_for_status()
    payload = response.json()

    chart = payload.get("chart", {})
    result_seq: Sequence = chart.get("result") or []
    if not result_seq:
        error = chart.get("error")
        if error:
            raise RuntimeError(f"Yahoo Finance error: {error.get('description')}")
        return []

    result = result_seq[0]
    timestamps: Sequence = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    if auto_adjust:
        closes_seq: Sequence = (indicators.get("adjclose") or [{}])[0].get("adjclose") or []
    else:
        closes_seq = (indicators.get("quote") or [{}])[0].get("close") or []

    rows: List[Tuple[datetime, float]] = []
    for idx, ts in enumerate(timestamps):
        if ts is None:
            continue
        price = closes_seq[idx] if idx < len(closes_seq) else None
        if price in (None, "null"):
            continue
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            continue
        if price_value <= 0:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)
        rows.append((dt, price_value))

    return rows


def fetch_latest_quote(symbol: str, timeout: int = 10) -> Optional[dict]:
    """Fetch the latest Yahoo Finance quote for a symbol."""
    if not symbol:
        return None
    params = {"symbols": symbol}
    response = requests.get(_QUOTE_URL, params=params, timeout=timeout, headers=_DEFAULT_HEADERS)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("quoteResponse", {}).get("result") or []
    return results[0] if results else None


def fetch_dividend_yield(symbol: str) -> Optional[float]:
    """Return dividend yield ratio (0.05 = 5%) if available."""
    quote = fetch_latest_quote(symbol)
    if not quote:
        return None
    for key in ("trailingAnnualDividendYield", "dividendYield", "fiftyTwoWeekDividendYield"):
        ratio = _extract_numeric(quote.get(key))
        if ratio is not None:
            return ratio
    return None


def fetch_latest_price_if_stale(
    symbol: str,
    *,
    start_dt: datetime,
    end_dt: datetime,
    auto_adjust: bool,
) -> Optional[Tuple[datetime, float]]:
    """Fetch a recent daily close when the monthly series misses the current month."""
    try:
        daily_rows = fetch_price_history(
            symbol,
            start_dt,
            end_dt,
            interval="1d",
            auto_adjust=auto_adjust,
        )
    except Exception as exc:  # pragma: no cover - network failure
        logger.warning("[%s] Latest daily price fetch failed: %s", symbol, exc)
        return None
    return daily_rows[-1] if daily_rows else None
