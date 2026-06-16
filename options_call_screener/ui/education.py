"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v3.8 math)", expanded=False):
        st.markdown(
            """
**Modules active in this build:**
1. **BSM engine** — dividend-adjusted pricing; Delta, Gamma, Theta, Vega, Rho, **Vanna**, **Charm**
2. **Portfolio stress grid** — ±15% spot × ±20% IV shocks; flags trades breaching 5% EPR loss cap
3. **IML monitor** — advisory kill switch in Risk Manager sandbox (no broker API)
4. **Quarter-Kelly + Monte Carlo** — max 3% risk; P95 drawdown gate before sizing
5. **Wheel advisory** — tells you when premium-selling may beat long calls (manual execution only)

**Not automated:** live order routing, box spreads, portfolio margin at broker, unusual flow.
            """
        )
