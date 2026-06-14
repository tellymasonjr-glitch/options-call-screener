"""Macro market context: VIX fear gauge and SPY trend gate."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import SPY_TREND_MULT, VIX_CALM_MAX, VIX_ELEVATED_MAX
from data.market_data import get_spot_price


@dataclass(frozen=True)
class MacroEnvironment:
    vix: float
    spy_spot: float
    spy_sma_20: float
    spy_above_sma_20: bool
    vix_multiplier: float
    spy_multiplier: float
    macro_multiplier: float
    hard_block: bool
    traffic_light: str
    headline: str
    detail: str


def _vix_multiplier(vix: float) -> tuple[float, bool]:
    if vix > VIX_ELEVATED_MAX:
        return 0.0, True
    if vix >= VIX_CALM_MAX:
        return 0.8, False
    return 1.0, False


def build_macro_environment(spy_history: pd.DataFrame) -> MacroEnvironment:
    """Fetch VIX once and derive SPY trend from history already loaded for the scan."""
    vix = get_spot_price("^VIX")
    spy_spot = float(spy_history["close"].iloc[-1])
    spy_sma_20 = float(spy_history["close"].tail(20).mean())
    spy_above = spy_spot >= spy_sma_20

    vix_mult, hard_block = _vix_multiplier(vix)
    spy_mult = 1.0 if spy_above else SPY_TREND_MULT
    macro_mult = vix_mult * spy_mult

    if hard_block:
        traffic = "red"
    elif macro_mult < 1.0:
        traffic = "yellow"
    else:
        traffic = "green"

    spy_trend = "above" if spy_above else "below"
    headline, detail = _macro_messages(
        vix, spy_spot, spy_sma_20, spy_trend, macro_mult, hard_block
    )

    return MacroEnvironment(
        vix=vix,
        spy_spot=spy_spot,
        spy_sma_20=spy_sma_20,
        spy_above_sma_20=spy_above,
        vix_multiplier=vix_mult,
        spy_multiplier=spy_mult,
        macro_multiplier=macro_mult,
        hard_block=hard_block,
        traffic_light=traffic,
        headline=headline,
        detail=detail,
    )


def _macro_messages(
    vix: float,
    spy_spot: float,
    spy_sma_20: float,
    spy_trend: str,
    macro_mult: float,
    hard_block: bool,
) -> tuple[str, str]:
    if hard_block:
        return (
            f"Macro Alert: VIX at {vix:.1f} (> {VIX_ELEVATED_MAX}). "
            "Long-call conviction picks blocked.",
            f"SPY ${spy_spot:.2f} is {spy_trend} the 20-day SMA (${spy_sma_20:.2f}). "
            "Market conditions hostile for new swing calls.",
        )

    if macro_mult < 1.0:
        parts = []
        if vix >= VIX_CALM_MAX:
            parts.append(f"VIX elevated at {vix:.1f}")
        if spy_trend == "below":
            parts.append(f"SPY below 20-day SMA (${spy_sma_20:.2f})")
        return (
            f"Caution: {' · '.join(parts)}. Conviction scores scaled ×{macro_mult:.2f}.",
            f"SPY ${spy_spot:.2f} · VIX {vix:.1f} · macro multiplier {macro_mult:.2f}.",
        )

    return (
        f"Macro OK: VIX {vix:.1f}, SPY ${spy_spot:.2f} above 20-day SMA (${spy_sma_20:.2f}).",
        "Calm volatility and supportive broad-market trend for swing calls.",
    )
