"""Autopsy Engine — decompose closed option P&L into Delta, Theta, and Vega buckets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PnLAttribution:
    actual_pnl: float
    delta_pnl: float
    theta_pnl: float
    vega_pnl: float
    residual_pnl: float
    days_held: int

    def summary_line(self) -> str:
        return (
            f"Direction (Delta): ${self.delta_pnl:+,.0f} · "
            f"Time (Theta): ${self.theta_pnl:+,.0f} · "
            f"Volatility (Vega): ${self.vega_pnl:+,.0f} · "
            f"Other: ${self.residual_pnl:+,.0f}"
        )


def _days_held(logged_at: str) -> int:
    try:
        opened = datetime.strptime(str(logged_at)[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            opened = datetime.strptime(str(logged_at)[:10], "%Y-%m-%d")
        except ValueError:
            return 1
    return max(1, (datetime.now() - opened).days)


def attribute_long_call_pnl(
    *,
    entry_ask: float,
    exit_bid: float,
    spot_entry: float,
    spot_exit: float,
    iv_entry: float,
    iv_exit: float,
    delta_entry: float,
    theta_entry: float,
    vega_entry: float,
    contracts: int = 1,
    logged_at: str = "",
    days_held: int | None = None,
) -> PnLAttribution:
    """
    First-order Greek attribution for a closed long call.

    Theta is daily per share; Vega is per 1 vol point (1%) per share.
    """
    mult = max(1, contracts) * 100.0
    held = days_held if days_held is not None else _days_held(logged_at)

    d_spot = spot_exit - spot_entry
    vol_points = (iv_exit - iv_entry) * 100.0

    delta_pnl = delta_entry * d_spot * mult
    theta_pnl = theta_entry * held * mult
    vega_pnl = vega_entry * vol_points * mult
    actual_pnl = (exit_bid - entry_ask) * mult
    residual = actual_pnl - delta_pnl - theta_pnl - vega_pnl

    return PnLAttribution(
        actual_pnl=round(actual_pnl, 2),
        delta_pnl=round(delta_pnl, 2),
        theta_pnl=round(theta_pnl, 2),
        vega_pnl=round(vega_pnl, 2),
        residual_pnl=round(residual, 2),
        days_held=held,
    )
