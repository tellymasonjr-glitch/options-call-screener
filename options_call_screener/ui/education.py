"""Plain-English summary of what the engine does (and deliberately skips)."""

from __future__ import annotations

import streamlit as st


def render_engine_guide() -> None:
    with st.expander("How confidence is built (v3.7 math)", expanded=False):
        st.markdown(
            """
**Automated in this app (Yahoo data only):**
- **Black-Scholes-Merton** fair value with dividend yield, implied vol, and historical vol
- **Greeks** — Delta, Gamma, Theta, Vega, Rho; warnings for IV crush, Vega overpay, and Gamma near expiry
- **Breakout stack** — Bollinger %B, 20-day high + volume, 52-week high proximity, round-number levels
- **OPEX calendar** — small seasonal tilt during options expiration week
- **Quarter-Kelly sizing** — max **3%** of bankroll risk per idea (professional fractional Kelly)
- **Spread friction** — penalizes wide bid/ask gaps that fake a “discount”

**Manual only (not in script — 30-second Google check):**
- Wheel / covered-call income, collars, box spreads
- Unusual options flow, dark pools, Fed headline trading
- Broker margin tiers (Reg T vs portfolio margin)

**Reality check:** Options cannot be “zero risk.” This tool ranks **defined-risk long calls**
where the math, liquidity, and trend align — it does not predict exact price targets like $30 on HOOD.
            """
        )
