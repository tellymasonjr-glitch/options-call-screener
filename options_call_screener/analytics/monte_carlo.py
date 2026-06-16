"""Monte Carlo expiry payoff distribution for position sizing validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MonteCarloResult:
    p95_loss_dollars: float
    median_pnl_dollars: float
    prob_profit: float
    passes_drawdown_cap: bool
    drawdown_cap_dollars: float
    simulations: int


def monte_carlo_long_call(
    history: pd.DataFrame,
    spot: float,
    strike: float,
    ask: float,
    dte: int,
    *,
    bankroll: float = 10_000.0,
    max_drawdown_pct: float = 0.05,
    n_sims: int = 1500,
) -> MonteCarloResult:
    """
    Bootstrap daily log-returns to expiry; measure long-call P&L distribution.

    p95_loss = 95th percentile of worst outcomes (loss magnitude).
    """
    closes = history["close"].astype(float)
    rets = np.log(closes / closes.shift(1)).dropna().values
    if len(rets) < 30:
        rets = np.array([0.0])

    cost = ask * 100.0
    cap = bankroll * max_drawdown_pct
    horizon = max(dte, 1)

    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(rets), size=(n_sims, horizon))
    path_rets = rets[idx]
    terminal = spot * np.exp(path_rets.sum(axis=1))
    payoffs = np.maximum(terminal - strike, 0.0) * 100.0
    pnls = payoffs - cost

    p95_loss = float(-np.percentile(pnls, 5))
    median_pnl = float(np.median(pnls))
    prob_profit = float((pnls > 0).mean())

    return MonteCarloResult(
        p95_loss_dollars=round(p95_loss, 2),
        median_pnl_dollars=round(median_pnl, 2),
        prob_profit=prob_profit,
        passes_drawdown_cap=p95_loss <= cap,
        drawdown_cap_dollars=round(cap, 2),
        simulations=n_sims,
    )
