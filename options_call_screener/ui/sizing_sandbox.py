"""Interactive position sizing sandbox — stateless risk math preview."""

from __future__ import annotations

import streamlit as st

from analytics.margin_monitor import compute_iml
from analytics.position_sizing import calculate_position_size, conviction_tier_multiplier
from config import (
    CONVICTION_TIER1_MIN,
    CONVICTION_TIER1_MULT,
    CONVICTION_TIER2_MIN,
    CONVICTION_TIER2_MULT,
    CONVICTION_TIER3_MIN,
    CONVICTION_TIER3_MULT,
    DEFAULT_BANKROLL,
    DEFAULT_BASE_RISK_PCT,
    MAX_BANKROLL,
    MAX_BASE_RISK_PCT,
    MIN_BANKROLL,
    MIN_BASE_RISK_PCT,
)
from ui.copy import (
    HELP_BANKROLL,
    HELP_BASE_RISK,
    HELP_CONVICTION,
    HELP_SANDBOX_ASK,
    SANDBOX_CAPTION,
    SANDBOX_TITLE,
)


def render_sizing_sandbox(*, expanded: bool = True) -> None:
    """Let users test bankroll, base risk, conviction, and premium before scanning."""
    with st.expander(SANDBOX_TITLE, expanded=expanded):
        st.caption(SANDBOX_CAPTION)

        c1, c2, c3, c4 = st.columns(4)
        bankroll = c1.number_input(
            "Your Total Account ($)",
            min_value=MIN_BANKROLL,
            max_value=MAX_BANKROLL,
            value=DEFAULT_BANKROLL,
            step=1000,
            key="sandbox_bankroll",
            help=HELP_BANKROLL,
        )
        base_risk_pct = c2.number_input(
            "Base Risk per Trade (%)",
            min_value=MIN_BASE_RISK_PCT,
            max_value=MAX_BASE_RISK_PCT,
            value=DEFAULT_BASE_RISK_PCT,
            step=0.25,
            key="sandbox_base_risk",
            help=HELP_BASE_RISK,
        )
        conviction = c3.slider(
            "Confidence Score",
            min_value=0,
            max_value=100,
            value=75,
            key="sandbox_conviction",
            help=HELP_CONVICTION,
        )
        ask = c4.number_input(
            "Contract Price Tag ($)",
            min_value=0.05,
            max_value=50.0,
            value=2.50,
            step=0.05,
            key="sandbox_ask",
            help=HELP_SANDBOX_ASK,
        )

        tier_name, tier_mult = conviction_tier_multiplier(conviction)
        size = calculate_position_size(bankroll, base_risk_pct, conviction, ask)
        cost_per_contract = ask * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Confidence Band", tier_name, help="How much extra or less risk vs. your base %.")
        m2.metric("Size Multiplier", f"{tier_mult:.2f}x", help="Applied to your base risk percent.")
        m3.metric("Dollar Budget", f"${size.risk_budget:,.0f}", help="Max dollars to put on this idea.")
        m4.metric("Contracts to Buy", str(size.contracts), help="Whole contracts your budget can afford.")

        st.info(size.summary)

        st.markdown(
            f"**How we got there:** `${bankroll:,.0f}` account x `{base_risk_pct}%` base risk x "
            f"`{tier_mult}` multiplier = **${size.risk_budget:,.0f}** budget. "
            f"Each contract costs `${cost_per_contract:,.0f}` (${ask:.2f} x 100 shares) -> "
            f"**{size.contracts}** contract(s)."
        )

        st.caption(
            f"Confidence bands: {CONVICTION_TIER1_MIN}+ = {CONVICTION_TIER1_MULT}x (high) · "
            f"{CONVICTION_TIER2_MIN}–{CONVICTION_TIER1_MIN - 1} = {CONVICTION_TIER2_MULT}x (solid) · "
            f"{CONVICTION_TIER3_MIN}–{CONVICTION_TIER2_MIN - 1} = {CONVICTION_TIER3_MULT}x (cautious) · "
            f"below {CONVICTION_TIER3_MIN} = skip"
        )

        st.divider()
        st.markdown("**Intraday Margin Level (IML) — advisory kill switch**")
        open_risk = st.number_input(
            "Premium already at risk ($)",
            min_value=0.0,
            max_value=float(bankroll),
            value=0.0,
            step=100.0,
            key="sandbox_open_risk",
            help="Total premium paid on open option positions (max loss on long calls).",
        )
        snap = compute_iml(bankroll, open_risk)
        im1, im2, im3 = st.columns(3)
        im1.metric("IML (equity cushion)", f"${snap.iml:,.0f}")
        im2.metric("Maintenance req.", f"${snap.maintenance_required:,.0f}")
        im3.metric("Kill switch", "ON" if snap.kill_switch else "OFF")
        if snap.imd:
            st.error(snap.message)
        else:
            st.caption(snap.message)
