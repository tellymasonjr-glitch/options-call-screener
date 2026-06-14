"""Streamlit sidebar inputs."""

from __future__ import annotations

import streamlit as st

from config import (
    CONVICTION_MIN_DTE,
    DEFAULT_BUDGET,
    DEFAULT_MAX_DTE,
    DEFAULT_MIN_DTE,
    DEFAULT_PICKS_PER_TICKER,
    DEFAULT_TICKERS,
    MAX_BUDGET,
    MAX_DTE_LIMIT,
    MAX_PICKS_PER_TICKER,
    MIN_BUDGET,
    MIN_DTE_LIMIT,
)
from screener import ScanConfig


def render_sidebar() -> ScanConfig | None:
    st.sidebar.header("Scan Settings")

    tickers = st.sidebar.multiselect(
        "Tickers",
        options=DEFAULT_TICKERS + ["SPY", "TSLA", "NVDA", "MSFT", "AMZN"],
        default=DEFAULT_TICKERS,
    )
    custom = st.sidebar.text_input("Add custom ticker (optional)")
    if custom.strip():
        tickers = list(dict.fromkeys(tickers + [custom.strip().upper()]))

    max_budget = st.sidebar.number_input(
        "Max budget per contract ($)",
        min_value=MIN_BUDGET,
        max_value=MAX_BUDGET,
        value=DEFAULT_BUDGET,
        step=50,
    )

    dte_range = st.sidebar.slider(
        "Days to expiration (DTE)",
        min_value=MIN_DTE_LIMIT,
        max_value=MAX_DTE_LIMIT,
        value=(DEFAULT_MIN_DTE, DEFAULT_MAX_DTE),
        help=(
            f"Set left handle to 0 for same-day (0DTE) calls — scored separately as scalper picks. "
            f"Conviction scoring uses {CONVICTION_MIN_DTE}+ DTE."
        ),
        key="dte_range_slider_v2",
    )
    if dte_range[0] == 0:
        st.sidebar.warning(
            "0 DTE enabled — same-day calls use volume/gamma scalper scoring, "
            f"not conviction EV. Conviction scan still runs at {CONVICTION_MIN_DTE}–{dte_range[1]} DTE."
        )

    risk_profile = st.sidebar.selectbox(
        "Risk profile",
        options=["conservative", "moderate", "aggressive"],
        index=1,
    )

    avoid_earnings = st.sidebar.checkbox("Avoid earnings week", value=True)

    picks_per_ticker = st.sidebar.slider(
        "Picks per ticker",
        min_value=1,
        max_value=MAX_PICKS_PER_TICKER,
        value=DEFAULT_PICKS_PER_TICKER,
    )

    if st.sidebar.button("Clear cache & reload"):
        st.cache_data.clear()
        st.rerun()

    analyze = st.sidebar.button("Analyze Market Opportunities", type="primary")

    if not analyze:
        return None

    if not tickers:
        st.sidebar.error("Select at least one ticker.")
        return None

    return ScanConfig(
        tickers=tickers,
        max_budget=float(max_budget),
        min_dte=int(dte_range[0]),
        max_dte=int(dte_range[1]),
        risk_profile=risk_profile,
        avoid_earnings=avoid_earnings,
        picks_per_ticker=int(picks_per_ticker),
    )
