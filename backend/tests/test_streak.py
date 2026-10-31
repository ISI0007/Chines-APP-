"""Streak logic (unit) and that activity updates it through the API."""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from services.streak_service import record_activity


def u(streak=0, last=None):
    return SimpleNamespace(streak_days=streak, last_active_on=last)


def test_first_activity_starts_streak_at_one():
    user = u()
    assert record_activity(user, date(2026, 11, 1)) is True
    assert user.streak_days == 1 and user.last_active_on == date(2026, 11, 1)


def test_same_day_activity_does_not_change_streak():
    user = u(streak=3, last=date(2026, 11, 1))
    assert record_activity(user, date(2026, 11, 1)) is False
    assert user.streak_days == 3


def test_consecutive_day_increments():
    user = u(streak=3, last=date(2026, 11, 1))
    assert record_activity(user, date(2026, 11, 2)) is True
    assert user.streak_days == 4 and user.last_active_on == date(2026, 11, 2)


def test_gap_resets_to_one():
    user = u(streak=10, last=date(2026, 11, 1))
    assert record_activity(user, date(2026, 11, 4)) is True   # 2-day gap
    assert user.streak_days == 1


def test_null_last_active_starts_at_one():
    user = u(streak=0, last=None)
    record_activity(user, date(2026, 11, 1))
    assert user.streak_days == 1


def test_a_week_of_consecutive_days():
    user = u()
    start = date(2026, 11, 1)
    for i in range(7):
        record_activity(user, start + timedelta(days=i))
    assert user.streak_days == 7
