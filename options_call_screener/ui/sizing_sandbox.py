"""Interactive position sizing sandbox — stateless risk math preview."""

from __future__ import annotations

import streamlit as st

from analytics.empirical_kelly import compute_empirical_kelly, get_journal_for_kelly, resolve_kelly_cap
from analytics.margin_monitor import compute_iml
from analytics.position_sizing import calculate_position_size, conviction_tier_multiplier
from analytics.technical import fractional_kelly_risk_pct
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
    HELP_CONTRACTS,
    HELP_DOLLAR_BUDGET,
    HELP_EMPIRICAL_KELLY,
    HELP_IML,
    HELP_KILL_SWITCH,
    HELP_KELLY_FINAL,
    HELP_MAINTENANCE,
    HELP_OPEN_RISK,
    HELP_SANDBOX_ASK,
    HELP_SIZE_MULT,
    HELP_THEORETICAL_KELLY,
    HELP_TIER_BAND,
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

        st.markdown("**Kelly cap comparison (theoretical vs your journal)**")
        k1, k2 = st.columns(2)
        prob_itm = k1.slider(
            "Model prob ITM (theoretical)",
            min_value=0.05,
            max_value=0.95,
            value=0.45,
            step=0.05,
            key="sandbox_prob_itm",
            help=HELP_THEORETICAL_KELLY,
        )
        reward_risk = k2.number_input(
            "Model risk/reward ratio",
            min_value=0.1,
            max_value=10.0,
            value=2.0,
            step=0.1,
            key="sandbox_reward_risk",
            help=HELP_THEORETICAL_KELLY,
        )

        journal = get_journal_for_kelly()
        empirical = compute_empirical_kelly(journal)
        theoretical_kelly = fractional_kelly_risk_pct(prob_itm, reward_risk)
        kelly_cap = resolve_kelly_cap(theoretical_kelly, journal)

        kc1, kc2, kc3 = st.columns(3)
        kc1.metric(
            "Theoretical Quarter-Kelly",
            f"{kelly_cap.theoretical_pct:.1f}%",
            help=HELP_THEORETICAL_KELLY,
        )
        kc2.metric(
            "Empirical Quarter-Kelly",
            f"{kelly_cap.empirical_pct:.1f}%" if kelly_cap.empirical_pct is not None else "—",
            help=HELP_EMPIRICAL_KELLY,
        )
        kc3.metric(
            "Final Kelly cap",
            f"{kelly_cap.final_pct:.1f}%",
            help=HELP_KELLY_FINAL,
        )
        if empirical.sufficient:
            st.caption(empirical.note)
        else:
            st.info(empirical.note)
        if kelly_cap.final_pct <= 0 and empirical.sufficient:
            st.error(
                "Empirical edge is negative — journal Kelly forces **0%** sizing until execution improves."
            )

        tier_name, tier_mult = conviction_tier_multiplier(conviction)
        size = calculate_position_size(
            bankroll,
            base_risk_pct,
            conviction,
            ask,
            max_risk_pct=kelly_cap.final_pct if kelly_cap.final_pct > 0 else None,
        )
        cost_per_contract = ask * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Confidence Band", tier_name, help=HELP_TIER_BAND)
        m2.metric("Size Multiplier", f"{tier_mult:.2f}x", help=HELP_SIZE_MULT)
        m3.metric("Dollar Budget", f"${size.risk_budget:,.0f}", help=HELP_DOLLAR_BUDGET)
        m4.metric("Contracts to Buy", str(size.contracts), help=HELP_CONTRACTS)

        st.info(size.summary)

        st.markdown(
            f"**How we got there:** `${bankroll:,.0f}` account × `{base_risk_pct}%` base risk × "
            f"`{tier_mult}` multiplier, capped by **{kelly_cap.final_pct:.1f}%** Kelly "
            f"(min of theoretical {kelly_cap.theoretical_pct:.1f}%"
            + (
                f" and empirical {kelly_cap.empirical_pct:.1f}%"
                if kelly_cap.empirical_pct is not None
                else ""
            )
            + f") → **${size.risk_budget:,.0f}** budget. "
            f"Each contract costs `${cost_per_contract:,.0f}` → **{size.contracts}** contract(s)."
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
            help=HELP_OPEN_RISK,
        )
        snap = compute_iml(bankroll, open_risk)
        im1, im2, im3 = st.columns(3)
        im1.metric("IML (equity cushion)", f"${snap.iml:,.0f}", help=HELP_IML)
        im2.metric("Maintenance req.", f"${snap.maintenance_required:,.0f}", help=HELP_MAINTENANCE)
        im3.metric("Kill switch", "ON" if snap.kill_switch else "OFF", help=HELP_KILL_SWITCH)
        if snap.imd:
            st.error(snap.message)
        else:
            st.caption(snap.message)
