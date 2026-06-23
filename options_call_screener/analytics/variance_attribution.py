"""Variance attribution — realized vs implied volatility over an option's hold.

Read-only telemetry for the Autopsy Engine (v5.4.5). Does not touch scoring,
risk gates, or sizing. Answers: "Did the stock actually move as much as the
premium priced in?" — separating direction calls from volatility overpay.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from data.cached_fetch import get_price_history

MIN_HOLD_DAYS = 3
MIN_HOLD_OBS = 3
TRADING_DAYS = 252


@dataclass(frozen=True)
class VarianceAttribution:
    implied_vol: float
    realized_vol: float
    vol_spread_pct: float
    days_held: int
    sufficient: bool
    verdict: str


def _to_naive(ts: object) -> pd.Timestamp | None:
    t = pd.to_datetime(ts, errors="coerce")
    if t is None or pd.isna(t):
        return None
    if getattr(t, "tzinfo", None) is not None:
        t = t.tz_localize(None)
    return t


def _annualized_realized_vol(closes: pd.Series) -> float:
    closes = closes.astype(float)
    log_ret = np.log(closes / closes.shift(1)).dropna()
    if len(log_ret) < 2:
        return 0.0
    return float(log_ret.std(ddof=1) * np.sqrt(TRADING_DAYS))


def _insufficient(implied_vol: float, days_held: int, reason: str) -> VarianceAttribution:
    return VarianceAttribution(
        implied_vol=implied_vol,
        realized_vol=0.0,
        vol_spread_pct=0.0,
        days_held=days_held,
        sufficient=False,
        verdict=reason,
    )


def compute_variance_attribution(
    ticker: str,
    entry_date: object,
    exit_date: object,
    iv_at_entry: float,
) -> VarianceAttribution:
    """
    Compare implied vol paid at entry against realized vol over the hold.

    Uses the cached 1y daily history (rate-limit safe). Returns a graceful
    ``sufficient=False`` result for short holds or thin data rather than raising.
    """
    implied_vol = float(iv_at_entry or 0.0)
    entry_ts = _to_naive(entry_date)
    exit_ts = _to_naive(exit_date)

    if entry_ts is None or exit_ts is None:
        return _insufficient(implied_vol, 0, "Missing entry/exit timestamps for variance calc.")

    days_held = max(0, (exit_ts - entry_ts).days)
    if days_held < MIN_HOLD_DAYS:
        return _insufficient(
            implied_vol, days_held, "Hold too short to measure realized variance (<3 days)."
        )

    hist = get_price_history(ticker)
    if hist is None or hist.empty or "date" not in hist.columns or "close" not in hist.columns:
        return _insufficient(implied_vol, days_held, "No price history available for variance calc.")

    dates = pd.to_datetime(hist["date"]).dt.date
    mask = (dates >= entry_ts.date()) & (dates <= exit_ts.date())
    window = hist.loc[mask]

    if len(window) < MIN_HOLD_OBS:
        return _insufficient(
            implied_vol, days_held, "Insufficient trading days inside the hold period."
        )

    realized_vol = _annualized_realized_vol(window["close"])
    if realized_vol <= 0:
        return _insufficient(implied_vol, days_held, "Could not compute realized volatility.")

    if implied_vol > 0:
        vol_spread_pct = (realized_vol - implied_vol) / implied_vol
    else:
        vol_spread_pct = 0.0

    if realized_vol < implied_vol:
        verdict = (
            f"Vega drag — you paid for {implied_vol:.0%} vol but the stock only realized "
            f"{realized_vol:.0%}. Premium overpaid for movement that didn't show up."
        )
    else:
        verdict = (
            f"Vega tailwind — vol was underpriced: paid for {implied_vol:.0%} but the stock "
            f"realized {realized_vol:.0%}. The move was bigger than the premium assumed."
        )

    return VarianceAttribution(
        implied_vol=implied_vol,
        realized_vol=realized_vol,
        vol_spread_pct=vol_spread_pct,
        days_held=days_held,
        sufficient=True,
        verdict=verdict,
    )
