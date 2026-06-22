"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v5.4.2 — snapshot hotfix)", expanded=False):
        st.markdown(
            """
**Data preservation (v5.4.1):**
- **Journal CSV backup/restore** — download after sessions; upload to recover Empirical Kelly on Cloud
- **Scan snapshot JSON** — top 3 picks + GARCH + macro indices per scan
- **Ex-dividend gate** — confidence haircut when ex-date falls before expiry
- **GARCH-aligned Monte Carlo** — tail risk uses the same forward vol as BSM pricing

**Sidebar playlists (v5.4):**
- **6 ticker playlists** — stack into Companies to Scan

**Execution reality (v5.3):**
- **Empirical Kelly** — journal win rate caps sizing after **5 closed Autopsy trades** (guardrail: no calibration loops before N≥5)

**Predictive vol (v5.0):**
- **GARCH(1,1)** — forward vol blended into BSM fair value

**Roadmap (not active yet):** v5.5 skew/VRP · v5.6 calibration curve · HMM regimes (requires journal data)
            """
        )
