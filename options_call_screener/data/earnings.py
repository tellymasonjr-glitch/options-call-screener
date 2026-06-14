"""Earnings calendar helpers via Yahoo Finance."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from config import EARNINGS_AVOID_DAYS


def fetch_earnings(ticker: str) -> list[dict[str, Any]]:
    try:
        t = yf.Ticker(ticker.upper())
        cal = t.calendar
        if cal is None:
            return []

        # calendar can be dict or DataFrame depending on yfinance version
        if isinstance(cal, dict):
            earn_date = cal.get("Earnings Date") or cal.get("Earnings Date High")
            if earn_date is None:
                return []
            if isinstance(earn_date, list):
                return [{"report_date": str(d)[:10]} for d in earn_date]
            return [{"report_date": str(earn_date)[:10]}]

        if isinstance(cal, pd.DataFrame) and not cal.empty:
            rows = []
            for idx in cal.index:
                val = cal.loc[idx].iloc[0] if hasattr(cal.loc[idx], "iloc") else cal.loc[idx]
                rows.append({"report_date": str(val)[:10], "label": str(idx)})
            return rows
    except Exception:
        pass

    try:
        dates = yf.Ticker(ticker.upper()).earnings_dates
        if dates is not None and not dates.empty:
            return [{"report_date": str(idx)[:10]} for idx in dates.index]
    except Exception:
        pass

    return []


def upcoming_earnings_dates(
    ticker: str,
    earnings: list[dict[str, Any]] | None = None,
    within_days: int = 45,
) -> list[date]:
    if earnings is None:
        earnings = fetch_earnings(ticker)

    today = date.today()
    cutoff = today + timedelta(days=within_days)
    dates: list[date] = []

    for row in earnings:
        text = str(row.get("report_date", ""))[:10]
        try:
            parsed = pd.to_datetime(text).date()
        except Exception:
            continue
        if today <= parsed <= cutoff:
            dates.append(parsed)

    return sorted(set(dates))


def expiration_near_earnings(
    expiration: str,
    earnings_dates: list[date],
    avoid_days: int = EARNINGS_AVOID_DAYS,
) -> bool:
    try:
        exp = pd.to_datetime(expiration).date()
    except Exception:
        return False

    for earn in earnings_dates:
        if abs((exp - earn).days) <= avoid_days:
            return True
    return False
