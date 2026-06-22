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
    vol_mode: str = "historical"
    daily_vol_used: float = 0.0


def _historical_daily_vol(rets: np.ndarray) -> float:
    if len(rets) < 2:
        return 0.0
    return float(np.std(rets, ddof=1))


def _resolve_daily_vol(
    rets: np.ndarray,
    *,
    effective_hv: float | None,
    garch_vol_annual: float | None,
) -> tuple[float, str]:
    """
    Align MC variance with the pricer's forward vol when GARCH/effective_hv is available.

    Scales bootstrapped historical returns so path variance matches effective_hv.
    """
    hist_daily = _historical_daily_vol(rets)
    if hist_daily <= 0:
        hist_daily = 0.012

    target_annual = None
    mode = "historical"
    if effective_hv is not None and effective_hv > 0:
        target_annual = float(effective_hv)
        mode = "effective_hv"
    elif garch_vol_annual is not None and garch_vol_annual > 0:
        target_annual = float(garch_vol_annual)
        mode = "garch"

    if target_annual is None:
        return hist_daily, mode

    target_daily = target_annual / np.sqrt(252.0)
    scale = target_daily / hist_daily if hist_daily > 0 else 1.0
    scale = float(np.clip(scale, 0.25, 4.0))
    return hist_daily * scale, mode


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
    effective_hv: float | None = None,
    garch_vol_annual: float | None = None,
) -> MonteCarloResult:
    """
    Bootstrap daily log-returns to expiry; measure long-call P&L distribution.

    When effective_hv or garch_vol_annual is supplied, return paths are scaled so
    terminal variance aligns with the GARCH-blended pricer (v5.4.1).
    """
    closes = history["close"].astype(float)
    rets = np.log(closes / closes.shift(1)).dropna().values
    if len(rets) < 30:
        rets = np.array([0.0])

    daily_vol, vol_mode = _resolve_daily_vol(
        rets,
        effective_hv=effective_hv,
        garch_vol_annual=garch_vol_annual,
    )

    cost = ask * 100.0
    cap = bankroll * max_drawdown_pct
    horizon = max(dte, 1)

    rng = np.random.default_rng(42)
    idx = rng.integers(0, len(rets), size=(n_sims, horizon))
    path_rets = rets[idx]

    hist_daily = _historical_daily_vol(rets) or daily_vol
    if hist_daily > 0 and daily_vol > 0:
        path_rets = path_rets * (daily_vol / hist_daily)

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
        vol_mode=vol_mode,
        daily_vol_used=round(daily_vol, 6),
    )
