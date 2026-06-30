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
    MAX_BANKROLL,
    MAX_BUDGET,
    MAX_DTE_LIMIT,
    MAX_BASE_RISK_PCT,
    MAX_PICKS_PER_TICKER,
    MIN_BANKROLL,
    MIN_BUDGET,
    MIN_BASE_RISK_PCT,
    MIN_DTE_LIMIT,
    SAME_DAY_SCALP_DTE_RANGE,
    SAME_DAY_SCALP_MAX_COST,
    SAME_DAY_SCALP_PICKS,
    SAME_DAY_SCALP_TICKERS,
    SCAN_WARN_TICKERS,
    STOCK_PRESETS,
    TICKER_OPTIONS,
    tickers_from_playlists,
    ticker_label,
)
from screener import ScanConfig
from ui.trade_journal import render_mirror_check
from ui.copy import (
    HELP_BANKROLL,
    HELP_BASE_RISK,
    HELP_CUSTOM_TICKER,
    HELP_DTE,
    HELP_MAX_COST,
    HELP_RISK_PROFILE,
    HELP_SIZING_TOGGLE,
    HELP_SKIP_EARNINGS,
    HELP_STOCK_PRESETS,
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


def _init_scan_ticker_state() -> None:
    if "selected_companies" not in st.session_state:
        st.session_state.selected_companies = list(DEFAULT_TICKERS)
    if "scan_playlists" not in st.session_state:
        st.session_state.scan_playlists = []
    if "_prev_playlists" not in st.session_state:
        st.session_state._prev_playlists = []


def _apply_pending_sidebar_preset() -> None:
    """Apply preset before sidebar widgets mount (Streamlit widget-state safe)."""
    action = st.session_state.pop("_sidebar_preset", None)
    if action == "default":
        st.session_state.selected_companies = list(DEFAULT_TICKERS)
        st.session_state.scan_playlists = []
        st.session_state._prev_playlists = []
        st.session_state.max_cost_per_trade = DEFAULT_BUDGET
        st.session_state.dte_range_slider_v2 = (DEFAULT_MIN_DTE, DEFAULT_MAX_DTE)
        st.session_state.picks_per_ticker = DEFAULT_PICKS_PER_TICKER
    elif action == "clear":
        st.session_state.selected_companies = []
        st.session_state.scan_playlists = []
        st.session_state._prev_playlists = []
    elif action == "same_day_scalp":
        st.session_state.selected_companies = [
            t for t in SAME_DAY_SCALP_TICKERS if t in TICKER_OPTIONS
        ]
        st.session_state.scan_playlists = []
        st.session_state._prev_playlists = []
        st.session_state.max_cost_per_trade = SAME_DAY_SCALP_MAX_COST
        st.session_state.dte_range_slider_v2 = SAME_DAY_SCALP_DTE_RANGE
        st.session_state.picks_per_ticker = SAME_DAY_SCALP_PICKS


def _on_playlists_changed() -> None:
    """Callback — may mutate selected_companies while scan_playlists updates."""
    chosen = list(st.session_state.get("scan_playlists") or [])
    if chosen:
        st.session_state.selected_companies = tickers_from_playlists(chosen)
    st.session_state._prev_playlists = list(chosen)


def _render_playlist_preloaders() -> None:
    st.sidebar.markdown("**Smart ticker preloaders**")

    # Preset buttons queue an action; state is applied on the next rerun before widgets draw.
    c1, c2, c3 = st.sidebar.columns(3)
    if c1.button("Default batch", help="Reset to F, SOFI, HOOD, CCL, SNAP"):
        st.session_state._sidebar_preset = "default"
        st.rerun()
    if c2.button("Clear all", help="Empty the scan list"):
        st.session_state._sidebar_preset = "clear"
        st.rerun()
    if c3.button(
        "Same day scalp",
        help=(
            "SPY, QQQ, AAPL, NVDA, TSLA, IWM · $100 max cost · 0DTE only · 5 ideas per stock"
        ),
    ):
        st.session_state._sidebar_preset = "same_day_scalp"
        st.rerun()

    st.sidebar.multiselect(
        "Select playlists to load",
        options=list(STOCK_PRESETS.keys()),
        key="scan_playlists",
        on_change=_on_playlists_changed,
        help=HELP_STOCK_PRESETS,
    )

    chosen_playlists = list(st.session_state.get("scan_playlists") or [])
    if chosen_playlists:
        loaded = tickers_from_playlists(chosen_playlists)
        st.sidebar.caption(
            f"Loaded **{len(loaded)}** tickers from {len(chosen_playlists)} playlist(s): "
            f"{', '.join(loaded[:8])}{'…' if len(loaded) > 8 else ''}. "
            "Remove any symbol below before scanning."
        )


def render_sidebar() -> ScanConfig | None:
    st.sidebar.header(SIDEBAR_SETUP)

    _init_scan_ticker_state()
    _apply_pending_sidebar_preset()
    _render_playlist_preloaders()

    current_tickers = list(st.session_state.get("selected_companies", []))
    custom = st.sidebar.text_input(
        "Add another symbol (optional)",
        help=HELP_CUSTOM_TICKER,
    )
    if custom.strip():
        sym = custom.strip().upper()
        if sym not in current_tickers:
            st.session_state.selected_companies = list(
                dict.fromkeys(current_tickers + [sym])
            )

    tickers = st.sidebar.multiselect(
        "Companies to Scan",
        options=TICKER_OPTIONS,
        format_func=ticker_label,
        key="selected_companies",
        help=HELP_TICKERS,
    )
    st.sidebar.caption(
        f"Default paper batch: {', '.join(DEFAULT_TICKERS)}. "
        f"Scan **{SCAN_WARN_TICKERS} or fewer** at a time on Cloud to avoid rate limits."
    )

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
        key="max_cost_per_trade",
    )

    dte_range = st.sidebar.slider(
        "Time Limit — Days Until Expiry",
        min_value=MIN_DTE_LIMIT,
        max_value=MAX_DTE_LIMIT,
        value=(DEFAULT_MIN_DTE, DEFAULT_MAX_DTE),
        help=HELP_DTE,
        key="dte_range_slider_v2",
    )
    if dte_range[0] == 0 and dte_range[1] == 0:
        st.sidebar.warning(
            "Pure **quick-scalp** mode — scans same-day options first, then **tomorrow** "
            "(or the next session) if today has no chain. Longer-dated conviction ideas are off."
        )
    elif dte_range[0] == 0:
        st.sidebar.warning(
            "Same-day (0DTE) mode is on — separate quick-scalp list at the bottom. "
            f"Regular ideas still scan {CONVICTION_MIN_DTE}–{dte_range[1]} days out. "
            "**Tip:** same-day options work best on **SPY, QQQ, AAPL, NVDA** — many budget tickers only have weekly expiries."
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
        key="picks_per_ticker",
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

    render_mirror_check(in_sidebar=True)

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
