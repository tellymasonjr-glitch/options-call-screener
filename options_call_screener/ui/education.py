"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v5.0 — predictive vol)", expanded=False):
        st.markdown(
            """
**Predictive upgrade (v5.0):**
- **GARCH(1,1) vol forecast** — 5-day forward vol replaces part of backward HV in fair-value pricing
- **Vol regime** — expand (GARCH > HV) vs compress (GARCH < HV) flags Vega overpay risk

**System management (v4.0):**
- **Empty Room** — OI &lt; 50 or volume &lt; 10 → 0% confidence
- **Mirror Check** — beta-weighted SPY-equivalent shares
- **Autopsy Engine** — close journal trades → Delta / Theta / Vega P&amp;L split

**Capital preservation (v3.9):**
- Payoff X-Ray · Landmine Sweeper · Echo Chamber Guard · Ghost Tax · Tide Check · Emergency brake
            """
        )
