"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v5.4 — smart playlists)", expanded=False):
        st.markdown(
            """
**Sidebar playlists (v5.4):**
- **6 ticker playlists** — Institutional Giants, Budget Momentum, Semis & Tech, Defensive, Index Macro, High-Risk Wildcards
- Stack multiple playlists → loads into Companies to Scan (manual edits still allowed)

**Execution reality (v5.3):**
- **Empirical Kelly** — journal win rate caps Quarter-Kelly sizing after 5 closed trades

**Predictive vol (v5.0):**
- **GARCH(1,1)** — forward vol blended into BSM fair value

**Capital preservation:** Ghost Tax · Landmine Sweeper · Mirror Check · Emergency brake · Payoff X-Ray
            """
        )
