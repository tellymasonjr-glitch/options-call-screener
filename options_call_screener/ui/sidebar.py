"""Streamlit sidebar inputs."""

from __future__ import annotations

import streamlit as st

from config import (
    CONVICTION_MIN_DTE,
    DEFAULT_BANKROLL,
    DEFAULT_BASE_RISK_PCT,
    DEFAULT_BUDGET,
    DEFAULT_MAX_DTE,
    DEFAULT_MIN_DTE,
    DEFAULT_PICKS_PER_TICKER,
    DEFAULT_TICKERS,
    LOW_BUDGET_TICKERS,
    MAX_BANKROLL,
    MAX_BUDGET,
    MAX_DTE_LIMIT,
    MAX_BASE_RISK_PCT,
    MAX_PICKS_PER_TICKER,
    MIN_BANKROLL,
    MIN_BUDGET,
    MIN_BASE_RISK_PCT,
    MIN_DTE_LIMIT,
    SCAN_WARN_TICKERS,
    TICKER_OPTIONS,
)
from screener import ScanConfig
from ui.copy import (
    HELP_BANKROLL,
    HELP_BASE_RISK,
    HELP_CUSTOM_TICKER,
    HELP_DTE,
    HELP_MAX_COST,
    HELP_RISK_PROFILE,
    HELP_SIZING_TOGGLE,
    HELP_SKIP_EARNINGS,
    HELP_TICKERS,
    HELP_TOP_IDEAS,
    SIDEBAR_RISK,
    SIDEBAR_SETUP,
)

_RISK_LABELS = {
    "conservative": "Careful — safer strikes, smaller moves needed",
    "moderate": "Balanced — default for most users",
    "aggressive": "Bold — closer strikes, bigger payoff if right",
}


def render_sidebar() -> ScanConfig | None:
    st.sidebar.header(SIDEBAR_SETUP)

    tickers = st.sidebar.multiselect(
        "Companies to Scan",
        options=TICKER_OPTIONS,
        default=DEFAULT_TICKERS,
        help=HELP_TICKERS,
    )
    st.sidebar.caption(
        f"**Default batch (5):** {', '.join(DEFAULT_TICKERS)} · "
        f"**Full preset:** {', '.join(LOW_BUDGET_TICKERS)}. "
        "Scan 5 at a time on Cloud, then add the next batch."
    )
    custom = st.sidebar.text_input(
        "Add another symbol (optional)",
        help=HELP_CUSTOM_TICKER,
    )
    if custom.strip():
        tickers = list(dict.fromkeys(tickers + [custom.strip().upper()]))
    if len(tickers) > SCAN_WARN_TICKERS:
        st.sidebar.warning(
            f"**{len(tickers)} tickers** selected — Yahoo may rate-limit on Cloud. "
            f"Stick to **{SCAN_WARN_TICKERS} or fewer** per scan for best reliability."
        )

    max_budget = st.sidebar.number_input(
        "Max Cost per Trade ($)",
        min_value=MIN_BUDGET,
        max_value=MAX_BUDGET,
        value=DEFAULT_BUDGET,
        step=50,
        help=HELP_MAX_COST,
    )

    dte_range = st.sidebar.slider(
        "Time Limit — Days Until Expiry",
        min_value=MIN_DTE_LIMIT,
        max_value=MAX_DTE_LIMIT,
        value=(DEFAULT_MIN_DTE, DEFAULT_MAX_DTE),
        help=HELP_DTE,
        key="dte_range_slider_v2",
    )
    if dte_range[0] == 0:
        st.sidebar.warning(
            "Same-day (0DTE) mode is on — those contracts use a separate quick-scalp score, "
            f"not long-term confidence. Regular ideas still scan {CONVICTION_MIN_DTE}–{dte_range[1]} days out."
        )

    risk_profile = st.sidebar.selectbox(
        "How Aggressive?",
        options=["conservative", "moderate", "aggressive"],
        index=1,
        format_func=lambda k: _RISK_LABELS[k],
        help=HELP_RISK_PROFILE,
    )

    avoid_earnings = st.sidebar.checkbox(
        "Skip Earnings Weeks",
        value=True,
        help=HELP_SKIP_EARNINGS,
    )

    picks_per_ticker = st.sidebar.slider(
        "Top Ideas per Stock",
        min_value=1,
        max_value=MAX_PICKS_PER_TICKER,
        value=DEFAULT_PICKS_PER_TICKER,
        help=HELP_TOP_IDEAS,
    )

    st.sidebar.subheader(SIDEBAR_RISK)
    enable_position_sizing = st.sidebar.checkbox(
        "Auto-calculate position size",
        value=True,
        help=HELP_SIZING_TOGGLE,
    )
    bankroll = st.sidebar.number_input(
        "Your Total Trading Account ($)",
        min_value=MIN_BANKROLL,
        max_value=MAX_BANKROLL,
        value=DEFAULT_BANKROLL,
        step=1000,
        disabled=not enable_position_sizing,
        help=HELP_BANKROLL,
    )
    base_risk_pct = st.sidebar.number_input(
        "Base Risk per Trade (%)",
        min_value=MIN_BASE_RISK_PCT,
        max_value=MAX_BASE_RISK_PCT,
        value=DEFAULT_BASE_RISK_PCT,
        step=0.25,
        disabled=not enable_position_sizing,
        help=HELP_BASE_RISK,
    )

    if st.sidebar.button("Clear cache & reload", help="Fix stale data or after an app update."):
        st.cache_data.clear()
        st.rerun()

    analyze = st.sidebar.button("Scan for Trading Ideas", type="primary")

    if not analyze:
        return None

    if not tickers:
        st.sidebar.error("Pick at least one company to scan.")
        return None

    return ScanConfig(
        tickers=tickers,
        max_budget=float(max_budget),
        min_dte=int(dte_range[0]),
        max_dte=int(dte_range[1]),
        risk_profile=risk_profile,
        avoid_earnings=avoid_earnings,
        picks_per_ticker=int(picks_per_ticker),
        bankroll=float(bankroll) if enable_position_sizing else 0.0,
        base_risk_pct=float(base_risk_pct),
        enable_position_sizing=enable_position_sizing,
    )
