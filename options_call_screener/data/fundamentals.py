"""Cached dividend yield for Merton (BSM + dividends) pricing."""

from __future__ import annotations

import streamlit as st
import yfinance as yf

from config import CACHE_TTL_SECONDS


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_dividend_yield(ticker: str) -> float:
    """
    Continuous dividend yield q for Black-Scholes-Merton (annualized, decimal).

    Yahoo may return yield as percent (2.5) or decimal (0.025) — normalized below.
    """
    try:
        info = yf.Ticker(ticker.upper()).info or {}
    except Exception:
        return 0.0

    raw = info.get("dividendYield") or info.get("trailingAnnualDividendYield") or 0.0
    try:
        q = float(raw)
    except (TypeError, ValueError):
        return 0.0

    if q <= 0:
        return 0.0
    if q > 0.5:
        q /= 100.0
    return min(q, 0.15)
