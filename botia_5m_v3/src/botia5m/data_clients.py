from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen


def _get_json(url: str, timeout: int = 8):
    with urlopen(url, timeout=timeout) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))


def discover_btc_5m_market(urls: list[str]) -> dict:
    for url in urls:
        try:
            data = _get_json(url)
            if isinstance(data, list):
                for m in data:
                    text = " ".join(str(m.get(k, "")).lower() for k in ["question", "slug", "description"])
                    if "btc" in text and ("5m" in text or "5 min" in text) and ("up" in text or "down" in text):
                        return {
                            "slug": m.get("slug", "btc-5m"),
                            "question": m.get("question", "BTC 5m up/down"),
                            "close_time": m.get("endDate", "unknown"),
                            "last_price": float(m.get("lastTradePrice", 0) or 0),
                            "raw": m,
                        }
        except Exception:
            continue
    return {
        "slug": "btc-5m-fallback",
        "question": "BTC 5m up/down (fallback)",
        "close_time": "unknown",
        "last_price": 0.0,
        "raw": {"reason": "market_discovery_unavailable"},
    }


def fetch_reference_price(urls: list[str]) -> tuple[float | None, str]:
    for url in urls:
        try:
            data = _get_json(url)
            if "binance" in url:
                return float(data["price"]), "binance"
            if "coinbase" in url:
                return float(data["data"]["amount"]), "coinbase"
        except (KeyError, ValueError, URLError, TimeoutError, Exception):
            continue
    return None, "unavailable"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sleep_backoff(current: int, max_seconds: int) -> int:
    time.sleep(current)
    return min(max_seconds, current * 2)
