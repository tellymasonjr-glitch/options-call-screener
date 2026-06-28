"""US equity session calendar helpers for options DTE."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def market_today() -> date:
    """Trading calendar 'today' in US Eastern — matches option expiry dates from Yahoo."""
    return datetime.now(ET).date()


def is_us_weekday(d: date | None = None) -> bool:
    """Weekday check (Mon–Fri ET). Does not include exchange holidays."""
    d = d or market_today()
    return d.weekday() < 5
