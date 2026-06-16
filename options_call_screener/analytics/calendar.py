"""Options expiration calendar effects (OPEX week seasonality)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def third_friday(year: int, month: int) -> date:
    """Third Friday of a month — standard U.S. equity monthly OPEX."""
    fridays = [
        d
        for d in calendar.Calendar(firstweekday=calendar.MONDAY).itermonthdates(
            year, month
        )
        if d.weekday() == 4 and d.month == month
    ]
    return fridays[2]


def calendar_multiplier(today: date | None = None) -> tuple[float, str]:
    """
    Historical OPEX-week seasonality modifier for conviction scoring.

    Returns (multiplier, human-readable note). Based on published OPEX-week studies;
    effect is modest — used as a small tilt, not a standalone signal.
    """
    today = today or date.today()
    opex = third_friday(today.year, today.month)
    opex_week_start = opex - timedelta(days=4)
    post_opex_end = opex + timedelta(days=5)

    if opex_week_start <= today <= opex:
        if today.month == 4:
            return 1.05, "OPEX week — April historically shows above-average index returns."
        if today.month in (1, 7):
            return 0.92, "OPEX week — January/July have shown weaker OPEX-week returns."
        return 1.02, "OPEX week — slight historical tailwind for broad markets."

    if opex < today <= post_opex_end:
        if today.month == 9:
            return 0.95, "Post-OPEX week — September often underperforms after expiration."
        return 0.98, "Post-OPEX week — slight historical headwind as funds rebalance."

    return 1.0, ""
