"""The study day boundary.

Timestamps are stored in UTC, but "today" has to mean the user's day. With a UTC day
boundary, practising at 9pm in EDT lands on the next date: tomorrow's queue shows up in
the evening and the streak counter breaks overnight. These tests pin a timezone explicitly
so they assert the same thing on any machine and on a UTC CI runner.
"""
from datetime import date, datetime, timezone

import pytest

from app import deps
from app.config import settings


@pytest.fixture
def tz(monkeypatch):
    def _set(name: str):
        monkeypatch.setattr(settings, "timezone", name)
    return _set


def test_evening_west_of_utc_belongs_to_that_evening(tz):
    """20:44 EDT is already the next day in UTC — it must still count as the 22nd."""
    tz("America/Toronto")
    assert deps.local_date(datetime(2026, 9, 23, 0, 44)) == date(2026, 9, 22)


def test_morning_east_of_utc_belongs_to_the_next_day(tz):
    """08:00 in Tokyo is the previous day in UTC — it must count as the 23rd."""
    tz("Asia/Tokyo")
    assert deps.local_date(datetime(2026, 9, 22, 23, 0)) == date(2026, 9, 23)


def test_aware_timestamps_are_not_shifted_twice(tz):
    tz("America/Toronto")
    aware = datetime(2026, 9, 23, 0, 44, tzinfo=timezone.utc)
    naive = datetime(2026, 9, 23, 0, 44)
    assert deps.local_date(aware) == deps.local_date(naive)


def test_unknown_timezone_falls_back_instead_of_crashing(tz):
    tz("Mars/Olympus_Mons")
    assert isinstance(deps.today(), date)


def test_today_matches_the_configured_zone(tz):
    tz("Asia/Tokyo")
    expected = datetime.now(timezone.utc).astimezone(deps._zone()).date()
    assert deps.today() == expected


def test_streak_counts_an_evening_session_on_that_evening(client, sample_problems, tz):
    """End to end: an attempt recorded now must make today's streak 1, not 0."""
    tz("America/Toronto")
    client.post("/review/1/attempt", json={"grade": "good", "seconds": 300})
    assert client.get("/stats").json()["streak_days"] == 1
