"""Visual payoff / P&L mapping at expiry (X-Ray Vision chart)."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go


def build_payoff_chart(
    spot: float,
    strike: float,
    ask: float,
    ticker: str = "",
) -> go.Figure:
    """Long-call P&L at expiry across a range of underlying prices."""
    lo = max(spot * 0.65, strike * 0.5, 0.01)
    hi = spot * 1.35
    prices = np.linspace(lo, hi, 100)
    premium = ask * 100.0
    pnl = np.maximum(prices - strike, 0.0) * 100.0 - premium
    breakeven = strike + ask

    colors = np.where(pnl >= 0, "rgba(46, 204, 113, 0.35)", "rgba(231, 76, 60, 0.35)")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl,
            mode="lines",
            line=dict(color="#3498db", width=3),
            fill="tozeroy",
            fillcolor="rgba(52, 152, 219, 0.15)",
            name="P&L at expiry",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#888", line_width=1)
    fig.add_vline(
        x=breakeven,
        line_dash="dot",
        line_color="#2ecc71",
        annotation_text=f"Breakeven ${breakeven:.2f}",
        annotation_position="top",
    )
    fig.add_vline(
        x=spot,
        line_dash="dot",
        line_color="#f39c12",
        annotation_text=f"Now ${spot:.2f}",
        annotation_position="bottom",
    )
    fig.add_vline(
        x=strike,
        line_dash="dash",
        line_color="#95a5a6",
        annotation_text=f"Strike ${strike:g}",
        annotation_position="top left",
    )

    title = f"{ticker} — Payoff X-Ray (1 contract)" if ticker else "Payoff X-Ray (1 contract)"
    fig.update_layout(
        title=title,
        xaxis_title="Stock price at expiry ($)",
        yaxis_title="Profit / loss ($)",
        height=360,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig
