"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v4.0 — fund manager)", expanded=False):
        st.markdown(
            """
**System management (v4.0):**
- **Empty Room** — OI &lt; 50 or volume &lt; 10 → 0% confidence (no liquidity trap)
- **Mirror Check** — beta-weighted SPY-equivalent shares in sidebar + dashboard
- **Autopsy Engine** — close a journal trade → P&L split into Delta / Theta / Vega

**Capital preservation (v3.9):**
- **Payoff X-Ray** — Plotly P&L curve on every top pick
- **Landmine Sweeper** — earnings within 3 days = hard NO-GO
- **Echo Chamber Guard** — duplicate sectors penalized in batch scans
- **Ghost Tax** — spread ≥10% cuts confidence 50%
- **Tide Check** — below 200-day SMA reduces confidence & Kelly
- **Emergency brake** — locks new trades if open P95 risk &gt; 10% of bankroll
            """
        )
