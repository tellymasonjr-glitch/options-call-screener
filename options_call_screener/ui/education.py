"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v5.3 — empirical Kelly)", expanded=False):
        st.markdown(
            """
**Execution reality (v5.3):**
- **Empirical Kelly** — trailing journal win rate + avg win/loss caps Quarter-Kelly sizing
- **Final cap** — min(theoretical BS Kelly, empirical Kelly, 3% bankroll)

**Predictive vol (v5.0):**
- **GARCH(1,1)** — 5-day forward vol blended into BSM fair value · expand/compress regimes

**System management (v4.0):**
- Empty Room · Mirror Check · Autopsy Engine · Payoff X-Ray · Emergency brake
            """
        )
