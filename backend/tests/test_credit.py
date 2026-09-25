"""API credit on the Stats page. No network: credit._get_json is replaced per test."""
import pytest

from app import credit
from app.config import settings


@pytest.fixture
def fake_http(monkeypatch):
    """Install canned responses keyed by URL suffix; records every URL requested."""
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    monkeypatch.setattr(settings, "deepseek_base_url", "https://relay.example/v1")
    credit.clear_cache()
    seen = []

    def install(routes):
        def get(url, key):
            seen.append(url)
            for suffix, body in routes.items():
                if url.endswith(suffix):
                    return body
            return None
        monkeypatch.setattr(credit, "_get_json", get)
        return seen
    yield install
    credit.clear_cache()


TOKEN = {"data": {"total_granted": 1_000_000, "total_used": 250_000,
                  "total_available": 750_000, "unlimited_quota": False, "expires_at": 0}}


def test_relay_ratio_is_measured_not_assumed(fake_http):
    """1,000,000 units = $20 here, i.e. 50,000 per dollar — not new-api's default 500,000."""
    seen = fake_http({"/api/usage/token/": TOKEN,
                      "/dashboard/billing/subscription": {"hard_limit_usd": 20}})
    c = credit.fetch_credit()
    assert (c["granted"], c["used"], c["available"]) == (20.0, 5.0, 15.0)
    assert c["source"] == "relay" and c["expires_at"] == 0
    assert "https://relay.example/api/usage/token/" in seen, "/v1 stripped for the token route"


def test_relay_without_subscription_uses_default_ratio(fake_http):
    fake_http({"/api/usage/token/": TOKEN})
    c = credit.fetch_credit()
    assert c["granted"] == 2.0          # 1,000,000 / 500,000


def test_official_deepseek_balance(fake_http):
    fake_http({"/user/balance": {"is_available": True, "balance_infos": [
        {"currency": "CNY", "total_balance": "42.50"}]}})
    c = credit.fetch_credit()
    assert c["source"] == "deepseek" and c["currency"] == "CNY" and c["available"] == 42.5


def test_nothing_answers_returns_none(fake_http):
    fake_http({})
    assert credit.fetch_credit() is None


def test_result_is_cached(fake_http):
    seen = fake_http({"/api/usage/token/": TOKEN})
    credit.fetch_credit()
    n = len(seen)
    credit.fetch_credit()
    assert len(seen) == n, "second read inside the cache window must not hit the network"
    credit.fetch_credit(force=True)
    assert len(seen) > n


def test_endpoint_off_when_ai_is_off(client):
    assert client.get("/stats/credit").status_code == 503


def test_endpoint_reports_credit(client, fake_http):
    fake_http({"/api/usage/token/": TOKEN,
               "/dashboard/billing/subscription": {"hard_limit_usd": 20}})
    r = client.get("/stats/credit")
    assert r.status_code == 200 and r.json()["available"] == 15.0


def test_endpoint_502_when_no_balance(client, fake_http):
    fake_http({})
    assert client.get("/stats/credit").status_code == 502
