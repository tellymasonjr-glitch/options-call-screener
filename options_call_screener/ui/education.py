"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v3.9 — at-a-glance)", expanded=False):
        st.markdown(
            """
**Visual & execution upgrades:**
- **Payoff X-Ray** — Plotly P&L curve on every top pick (breakeven + cliff visible)
- **Landmine Sweeper** — earnings within 3 days = hard NO-GO (0% confidence)
- **Echo Chamber Guard** — 2nd/3rd stock in same sector penalized in batch scans
- **Paper journal** — Execute Paper Trade button → `my_trades.csv`
- **Ghost Tax** — spread ≥10% cuts confidence 50%; ≥8% warns
- **Tide Check** — below 200-day SMA reduces confidence & Kelly
- **Emergency brake** — locks new trades if open P95 risk > 10% of bankroll
            """
        )
