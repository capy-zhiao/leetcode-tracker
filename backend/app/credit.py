"""Remaining API credit for the configured LLM provider, shown on the Stats page.

Two shapes are understood:
  relay     new-api / one-api gateways (e.g. the one the DeepSeek key was bought through):
            GET {root}/api/usage/token/ gives granted / used / available in quota units,
            and GET {base}/dashboard/billing/subscription gives the same total in USD, so
            the units-per-dollar ratio is measured rather than assumed.
  deepseek  the official API: GET {base}/user/balance, which may be in CNY.

Results are cached briefly: the Stats page should not hit the provider on every view.
"""
from __future__ import annotations

import logging
import time

import httpx

from .config import settings

log = logging.getLogger(__name__)

CACHE_SECONDS = 60
DEFAULT_UNITS_PER_USD = 500_000        # new-api's default, used only if the ratio can't be read

_cache: tuple[float, dict | None] | None = None


def _get_json(url: str, key: str) -> dict | None:
    """GET with the API key; None on any network, HTTP or JSON failure."""
    try:
        r = httpx.get(url, headers={"Authorization": f"Bearer {key}"},
                      timeout=10, follow_redirects=True)
        if r.status_code != 200:
            return None
        return r.json()
    except (httpx.HTTPError, ValueError):
        return None


def _relay(base: str, key: str) -> dict | None:
    root = base.rstrip("/").removesuffix("/v1")
    token = _get_json(f"{root}/api/usage/token/", key)
    data = (token or {}).get("data") if isinstance(token, dict) else None
    if not isinstance(data, dict) or "total_available" not in data:
        return None

    granted, used, available = (float(data.get(k, 0)) for k in
                                ("total_granted", "total_used", "total_available"))
    sub = _get_json(f"{base.rstrip('/')}/dashboard/billing/subscription", key) or {}
    limit_usd = float(sub.get("hard_limit_usd") or 0)
    per_usd = granted / limit_usd if granted and limit_usd else DEFAULT_UNITS_PER_USD

    return {
        "source": "relay",
        "currency": "USD",
        "granted": round(granted / per_usd, 2),
        "used": round(used / per_usd, 2),
        "available": round(available / per_usd, 2),
        "unlimited": bool(data.get("unlimited_quota")),
        "expires_at": int(data.get("expires_at") or 0),   # 0 = never
    }


def _official_deepseek(base: str, key: str) -> dict | None:
    body = _get_json(f"{base.rstrip('/').removesuffix('/v1')}/user/balance", key)
    infos = (body or {}).get("balance_infos") if isinstance(body, dict) else None
    if not infos:
        return None
    info = infos[0]
    return {
        "source": "deepseek",
        "currency": info.get("currency", "CNY"),
        "granted": None,
        "used": None,
        "available": round(float(info.get("total_balance", 0)), 2),
        "unlimited": False,
        "expires_at": 0,
    }


def fetch_credit(force: bool = False) -> dict | None:
    """Remaining credit, or None when AI is off or no balance endpoint answered."""
    global _cache
    if not force and _cache and time.monotonic() - _cache[0] < CACHE_SECONDS:
        return _cache[1]

    result = None
    if settings.llm_provider.strip().lower() == "deepseek" and settings.deepseek_api_key:
        base, key = settings.deepseek_base_url, settings.deepseek_api_key
        result = _relay(base, key) or _official_deepseek(base, key)
        if result is None:
            log.warning("Could not read API credit from %s", base)

    _cache = (time.monotonic(), result)
    return result


def clear_cache() -> None:
    global _cache
    _cache = None
