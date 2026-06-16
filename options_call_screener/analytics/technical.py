"""Bollinger %B, ATR stop-loss, and volume breakout checks (local OHLCV math only)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TechnicalSignals:
    pct_b: float
    atr_14: float
    atr_stop_2x: float
    midrange_chop: bool
    breakout_zone: bool
    low_volume_breakout: bool
    volume_vs_20d: float


def compute_technical_signals(history: pd.DataFrame) -> TechnicalSignals:
    closes = history["close"].astype(float)
    highs = history["high"].astype(float)
    lows = history["low"].astype(float)
    volumes = history["volume"].astype(float)
    spot = float(closes.iloc[-1])

    sma20 = closes.rolling(20).mean()
    std20 = closes.rolling(20).std()
    upper = sma20 + 2 * std20
    lower = sma20 - 2 * std20

    band_width = float(upper.iloc[-1] - lower.iloc[-1])
    if band_width > 0:
        pct_b = float((closes.iloc[-1] - lower.iloc[-1]) / band_width)
    else:
        pct_b = 0.5

    h_l = highs - lows
    h_pc = (highs - closes.shift(1)).abs()
    l_pc = (lows - closes.shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().iloc[-1])

    vol_sma20 = float(volumes.rolling(20).mean().iloc[-1]) if len(volumes) >= 20 else float(volumes.mean())
    last_vol = float(volumes.iloc[-1])
    vol_ratio = last_vol / vol_sma20 if vol_sma20 > 0 else 1.0

    breakout_zone = pct_b >= 0.80 or pct_b <= 0.20
    midrange_chop = 0.30 <= pct_b <= 0.70
    breaking_up = pct_b >= 0.80 or float(closes.iloc[-1]) >= float(upper.iloc[-1]) * 0.98
    low_volume_breakout = breaking_up and last_vol < vol_sma20

    return TechnicalSignals(
        pct_b=pct_b,
        atr_14=atr,
        atr_stop_2x=round(spot - 2 * atr, 2),
        midrange_chop=midrange_chop,
        breakout_zone=breakout_zone,
        low_volume_breakout=low_volume_breakout,
        volume_vs_20d=vol_ratio,
    )


def half_kelly_risk_pct(win_prob: float, reward_risk: float) -> float:
    """Half-Kelly max bankroll risk % (0 if no edge)."""
    if reward_risk <= 0 or win_prob <= 0:
        return 0.0
    q = 1.0 - win_prob
    b = reward_risk
    full_kelly = (win_prob * b - q) / b
    if full_kelly <= 0:
        return 0.0
    return min(full_kelly / 2.0 * 100.0, 25.0)


def conviction_technical_multiplier(signals: TechnicalSignals) -> float:
    mult = 1.0
    if signals.midrange_chop:
        mult *= 0.85
    elif signals.breakout_zone:
        mult *= 1.05
    if signals.low_volume_breakout:
        mult *= 0.75
    return mult
