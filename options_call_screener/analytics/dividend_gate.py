"""Ex-dividend gate — confidence haircut for long calls through dividend drops."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf

from config import CACHE_TTL_SECONDS, EXDIV_CONFIDENCE_MULT, EXDIV_LOOKAHEAD_DAYS


def _parse_date(raw: object) -> date | None:
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)) and raw > 1_000_000_000:
            return pd.to_datetime(raw, unit="s").date()
        return pd.to_datetime(str(raw)[:10]).date()
    except Exception:
        return None


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_ex_dividend_dates(ticker: str, *, lookahead_days: int = EXDIV_LOOKAHEAD_DAYS) -> list[date]:
    """
    Upcoming ex-dividend dates for a ticker (Yahoo Finance).

    Uses info fields, calendar, and recent dividend history cadence when available.
    """
    sym = ticker.upper().strip()
    today = date.today()
    cutoff = today + timedelta(days=int(lookahead_days))
    found: set[date] = set()

    try:
        t = yf.Ticker(sym)
        info = t.info or {}
        for key in ("exDividendDate", "dividendDate"):
            parsed = _parse_date(info.get(key))
            if parsed and today <= parsed <= cutoff:
                found.add(parsed)

        cal = t.calendar
        if isinstance(cal, dict):
            for key, val in cal.items():
                if "dividend" in str(key).lower() or "ex" in str(key).lower():
                    if isinstance(val, list):
                        for item in val:
                            parsed = _parse_date(item)
                            if parsed and today <= parsed <= cutoff:
                                found.add(parsed)
                    else:
                        parsed = _parse_date(val)
                        if parsed and today <= parsed <= cutoff:
                            found.add(parsed)
        elif isinstance(cal, pd.DataFrame) and not cal.empty:
            for idx in cal.index:
                label = str(idx).lower()
                if "dividend" in label or "ex" in label:
                    val = cal.loc[idx]
                    cell = val.iloc[0] if hasattr(val, "iloc") else val
                    parsed = _parse_date(cell)
                    if parsed and today <= parsed <= cutoff:
                        found.add(parsed)

        divs = t.dividends
        if divs is not None and len(divs) >= 2:
            idx_dates = [d.date() if hasattr(d, "date") else pd.to_datetime(d).date() for d in divs.index[-4:]]
            if len(idx_dates) >= 2:
                gaps = [(idx_dates[i] - idx_dates[i - 1]).days for i in range(1, len(idx_dates))]
                avg_gap = sum(gaps) / len(gaps)
                if 20 <= avg_gap <= 120:
                    projected = idx_dates[-1] + timedelta(days=int(round(avg_gap)))
                    while projected <= cutoff:
                        if projected >= today:
                            found.add(projected)
                        projected += timedelta(days=int(round(avg_gap)))
    except Exception:
        pass

    return sorted(found)


def expiration_crosses_ex_div(
    expiration: str,
    ex_dates: list[date],
    *,
    as_of: date | None = None,
) -> bool:
    """True when t0 <= ex-div <= expiration (long call holds through the drop)."""
    if not ex_dates:
        return False
    try:
        exp = pd.to_datetime(str(expiration)[:10]).date()
    except Exception:
        return False
    start = as_of or date.today()
    for ex in ex_dates:
        if start <= ex <= exp:
            return True
    return False


def ex_div_confidence_mult(crosses: bool) -> tuple[float, str]:
    """Systematic confidence deduction for calls holding through ex-div."""
    if not crosses:
        return 1.0, ""
    pct = int((1.0 - EXDIV_CONFIDENCE_MULT) * 100)
    return EXDIV_CONFIDENCE_MULT, (
        f"Ex-dividend gate — ex-date falls before expiry; confidence reduced {pct}% "
        "for expected spot drop on the dividend."
    )
