"""Portfolio-margin-style stress grid for a long call (advisory, not broker margin)."""

from __future__ import annotations

from dataclasses import dataclass

from analytics.pricing import bs_call_price
from config import STRESS_SPOT_SHOCKS, STRESS_VOL_SHOCKS


@dataclass(frozen=True)
class StressTestResult:
    max_loss_dollars: float
    worst_spot_shock: float
    worst_vol_shock: float
    passes_epr: bool
    epr_limit_dollars: float


def long_call_stress_test(
    spot: float,
    strike: float,
    ask: float,
    dte: int,
    iv: float,
    *,
    div_yield: float = 0.0,
    epr_limit_pct: float = 0.05,
    bankroll: float = 10_000.0,
) -> StressTestResult:
    """
    Simulate price (-15%..+15%) and IV shocks on a single long call.

    Returns worst P&L across the grid vs. an Expected Price Range (EPR) loss cap.
    """
    t = max(dte, 1) / 365.0
    cost = ask * 100.0
    epr_limit = bankroll * epr_limit_pct
    q = max(div_yield, 0.0)

    worst_loss = 0.0
    worst_ds = 0.0
    worst_dv = 0.0

    for ds in STRESS_SPOT_SHOCKS:
        new_spot = spot * (1.0 + ds)
        for dv in STRESS_VOL_SHOCKS:
            new_iv = max(iv * (1.0 + dv), 0.05)
            new_val = bs_call_price(new_spot, strike, t, new_iv, div_yield=q) * 100.0
            pnl = new_val - cost
            if pnl < worst_loss:
                worst_loss = pnl
                worst_ds = ds
                worst_dv = dv

    return StressTestResult(
        max_loss_dollars=round(worst_loss, 2),
        worst_spot_shock=worst_ds,
        worst_vol_shock=worst_dv,
        passes_epr=abs(worst_loss) <= epr_limit,
        epr_limit_dollars=round(epr_limit, 2),
    )
