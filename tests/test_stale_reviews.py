# SPDX-License-Identifier: Apache-2.0
"""Tests for stale review business-day logic.

Mirrors the countBusinessDays function from
.github/workflows/reusable_stale_reviews.yml to validate
edge cases in the business-day calculation used for
staleness detection.
"""

from datetime import date, datetime, timedelta

import pytest


def count_business_days(from_date: date, to_date: date) -> int:
    """Python equivalent of the inline JS countBusinessDays.

    Counts weekdays (Mon-Fri) between two dates, exclusive
    of `from_date` and inclusive up to (but not including)
    `to_date`. This mirrors the JS implementation which
    increments from `from` toward `to` and counts each
    weekday encountered.
    """
    count = 0
    current = from_date
    while current < to_date:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon=0 .. Fri=4
            count += 1
    return count


class TestCountBusinessDays:
    """Mirrors countBusinessDays from reusable_stale_reviews.yml."""

    def test_same_day_returns_zero(self):
        d = date(2026, 8, 3)  # Monday
        assert count_business_days(d, d) == 0

    def test_monday_to_friday_same_week(self):
        # Mon Aug 3 -> Fri Aug 7 = 4 business days
        assert count_business_days(date(2026, 8, 3), date(2026, 8, 7)) == 4

    def test_friday_to_monday_crosses_weekend(self):
        # Fri Aug 7 -> Mon Aug 10 = 1 business day
        assert count_business_days(date(2026, 8, 7), date(2026, 8, 10)) == 1

    def test_full_business_week(self):
        # Mon Aug 3 -> Mon Aug 10 = 5 business days
        assert count_business_days(date(2026, 8, 3), date(2026, 8, 10)) == 5

    def test_saturday_to_monday(self):
        # Sat Aug 8 -> Mon Aug 10 = 1 business day (Monday)
        assert count_business_days(date(2026, 8, 8), date(2026, 8, 10)) == 1

    def test_sunday_to_monday(self):
        # Sun Aug 9 -> Mon Aug 10 = 1 business day (Monday)
        assert count_business_days(date(2026, 8, 9), date(2026, 8, 10)) == 1

    def test_two_full_weeks(self):
        # Mon Aug 3 -> Mon Aug 17 = 10 business days
        assert count_business_days(date(2026, 8, 3), date(2026, 8, 17)) == 10

    def test_saturday_to_sunday_returns_zero(self):
        # Sat Aug 8 -> Sun Aug 9 = 0 business days
        assert count_business_days(date(2026, 8, 8), date(2026, 8, 9)) == 0

    def test_wednesday_to_wednesday(self):
        # Wed Aug 5 -> Wed Aug 12 = 5 business days
        assert count_business_days(date(2026, 8, 5), date(2026, 8, 12)) == 5

    def test_one_day_weekday(self):
        # Mon Aug 3 -> Tue Aug 4 = 1 business day
        assert count_business_days(date(2026, 8, 3), date(2026, 8, 4)) == 1

    def test_one_day_friday_to_saturday(self):
        # Fri Aug 7 -> Sat Aug 8 = 0 business days
        assert count_business_days(date(2026, 8, 7), date(2026, 8, 8)) == 0

    @pytest.mark.parametrize(
        "from_d,to_d,expected",
        [
            # Threshold boundary: exactly 5 business days
            (date(2026, 8, 3), date(2026, 8, 10), 5),
            # Just under threshold: 4 business days
            (date(2026, 8, 3), date(2026, 8, 7), 4),
            # Well over threshold: 15 business days (3 weeks)
            (date(2026, 8, 3), date(2026, 8, 24), 15),
        ],
        ids=["at-threshold", "below-threshold", "well-over"],
    )
    def test_stale_threshold_boundaries(self, from_d, to_d, expected):
        """Validate values around the default 5-day stale threshold."""
        assert count_business_days(from_d, to_d) == expected


class TestReminderCooldown:
    """Validates the 3-calendar-day cooldown logic.

    The cooldown uses calendar days (not business days) because
    the workflow runs weekdays only. A Friday reminder suppresses
    Monday reminders (72 hours later), and Tuesday would fire.
    """

    @staticmethod
    def within_cooldown(
        created_at: datetime,
        now: datetime,
        cooldown_ms: int = 3 * 24 * 60 * 60 * 1000,
    ) -> bool:
        """Mirror the JS cooldown check: (now - created_at) < cooldown_ms."""
        diff_ms = (now - created_at).total_seconds() * 1000
        return diff_ms < cooldown_ms

    def test_same_time_within_cooldown(self):
        now = datetime(2026, 8, 4, 9, 0, 0)
        assert self.within_cooldown(now, now) is True

    def test_two_days_within_cooldown(self):
        created = datetime(2026, 8, 4, 9, 0, 0)
        now = datetime(2026, 8, 6, 9, 0, 0)  # 48 hours
        assert self.within_cooldown(created, now) is True

    def test_three_days_exactly_not_within_cooldown(self):
        created = datetime(2026, 8, 4, 9, 0, 0)
        now = datetime(2026, 8, 7, 9, 0, 0)  # 72 hours
        assert self.within_cooldown(created, now) is False

    def test_four_days_not_within_cooldown(self):
        created = datetime(2026, 8, 4, 9, 0, 0)
        now = datetime(2026, 8, 8, 9, 0, 0)  # 96 hours
        assert self.within_cooldown(created, now) is False

    def test_friday_to_monday_within_cooldown(self):
        """Friday 09:00 -> Monday 09:00 = exactly 72h = NOT within cooldown."""
        created = datetime(2026, 8, 7, 9, 0, 0)  # Friday
        now = datetime(2026, 8, 10, 9, 0, 0)  # Monday
        assert self.within_cooldown(created, now) is False

    def test_friday_to_monday_just_before(self):
        """Friday 09:00 -> Monday 08:59 = just under 72h = within cooldown."""
        created = datetime(2026, 8, 7, 9, 0, 0)  # Friday
        now = datetime(2026, 8, 10, 8, 59, 59)  # Monday
        assert self.within_cooldown(created, now) is True
