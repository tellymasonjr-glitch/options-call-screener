"""Interactive position sizing sandbox — stateless risk math preview."""

from __future__ import annotations

import streamlit as st

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


def render_sizing_sandbox(*, expanded: bool = True) -> None:
    """Let users test bankroll, base risk, conviction, and premium before scanning."""
    with st.expander("Position Sizing Sandbox", expanded=expanded):
        st.caption(
            "Stateless risk math — same engine as conviction picks. "
            "Adjust inputs to see how tier multipliers translate into contract count."
        )

        c1, c2, c3, c4 = st.columns(4)
        bankroll = c1.number_input(
            "Bankroll ($)",
            min_value=MIN_BANKROLL,
            max_value=MAX_BANKROLL,
            value=DEFAULT_BANKROLL,
            step=1000,
            key="sandbox_bankroll",
        )
        base_risk_pct = c2.number_input(
            "Base risk (%)",
            min_value=MIN_BASE_RISK_PCT,
            max_value=MAX_BASE_RISK_PCT,
            value=DEFAULT_BASE_RISK_PCT,
            step=0.25,
            key="sandbox_base_risk",
        )
        conviction = c3.slider(
            "Conviction score",
            min_value=0,
            max_value=100,
            value=75,
            key="sandbox_conviction",
        )
        ask = c4.number_input(
            "Option premium / ask ($)",
            min_value=0.05,
            max_value=50.0,
            value=2.50,
            step=0.05,
            key="sandbox_ask",
        )

        tier_name, tier_mult = conviction_tier_multiplier(conviction)
        size = calculate_position_size(bankroll, base_risk_pct, conviction, ask)
        cost_per_contract = ask * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tier", tier_name)
        m2.metric("Tier multiplier", f"{tier_mult:.2f}x")
        m3.metric("Risk budget", f"${size.risk_budget:,.0f}")
        m4.metric("Contracts", str(size.contracts))

        st.info(size.summary)

        st.markdown(
            f"**Formula:** `${bankroll:,.0f}` x `{base_risk_pct}%` x `{tier_mult}` "
            f"= **${size.risk_budget:,.0f}** risk budget -> "
            f"`floor(${size.risk_budget:,.0f} / ${cost_per_contract:,.0f})` "
            f"= **{size.contracts}** contract(s)"
        )

        st.caption(
            f"Tier bands: {CONVICTION_TIER1_MIN}+ -> {CONVICTION_TIER1_MULT}x | "
            f"{CONVICTION_TIER2_MIN}-{CONVICTION_TIER1_MIN - 1} -> {CONVICTION_TIER2_MULT}x | "
            f"{CONVICTION_TIER3_MIN}-{CONVICTION_TIER2_MIN - 1} -> {CONVICTION_TIER3_MULT}x | "
            f"below {CONVICTION_TIER3_MIN} -> no size"
        )
