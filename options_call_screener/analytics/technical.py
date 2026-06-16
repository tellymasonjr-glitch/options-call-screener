"""Bollinger %B, ATR, breakout confirmation, and Kelly sizing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import KELLY_FRACTION, MAX_KELLY_RISK_PCT


@dataclass(frozen=True)
class TechnicalSignals:
    pct_b: float
    atr_14: float
    atr_stop_2x: float
    midrange_chop: bool
    breakout_zone: bool
    low_volume_breakout: bool
    volume_vs_20d: float
    near_52w_high: bool
    pct_from_52w_high: float
    nearest_round: float
    pct_from_round: float
    new_20d_high: bool
    breakout_confirmed: bool
    momentum_accelerating: bool
    roc_5: float


def _nearest_round_level(price: float) -> float:
    if price <= 0:
        return 0.0
    magnitude = 10 ** max(0, len(str(int(price))) - 1)
    if price < 50:
        step = 5.0
    elif price < 200:
        step = 10.0
    else:
        step = magnitude / 10.0
    return round(price / step) * step


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

    vol_sma20 = (
        float(volumes.rolling(20).mean().iloc[-1])
        if len(volumes) >= 20
        else float(volumes.mean())
    )
    last_vol = float(volumes.iloc[-1])
    vol_ratio = last_vol / vol_sma20 if vol_sma20 > 0 else 1.0

    window = closes.tail(252) if len(closes) >= 252 else closes
    high_52w = float(window.max())
    pct_from_52w = (high_52w - spot) / high_52w if high_52w > 0 else 0.0
    near_52w = pct_from_52w <= 0.03

    round_lvl = _nearest_round_level(spot)
    pct_from_round = abs(spot - round_lvl) / spot if spot > 0 else 0.0

    high_20d = float(highs.tail(20).max()) if len(highs) >= 20 else spot
    new_20d_high = spot >= high_20d * 0.998
    breakout_confirmed = new_20d_high and vol_ratio >= 1.2

    roc_5 = (
        float((closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6])
        if len(closes) > 6 and closes.iloc[-6] > 0
        else 0.0
    )
    roc_20 = (
        float((closes.iloc[-1] - closes.iloc[-21]) / closes.iloc[-21])
        if len(closes) > 21 and closes.iloc[-21] > 0
        else 0.0
    )
    momentum_accel = roc_5 > (roc_20 / 4.0) and roc_5 > 0

    breakout_zone = pct_b >= 0.80 or pct_b <= 0.20
    midrange_chop = 0.30 <= pct_b <= 0.70
    breaking_up = pct_b >= 0.80 or spot >= float(upper.iloc[-1]) * 0.98
    low_volume_breakout = breaking_up and last_vol < vol_sma20

    return TechnicalSignals(
        pct_b=pct_b,
        atr_14=atr,
        atr_stop_2x=round(spot - 2 * atr, 2),
        midrange_chop=midrange_chop,
        breakout_zone=breakout_zone,
        low_volume_breakout=low_volume_breakout,
        volume_vs_20d=vol_ratio,
        near_52w_high=near_52w,
        pct_from_52w_high=pct_from_52w,
        nearest_round=round_lvl,
        pct_from_round=pct_from_round,
        new_20d_high=new_20d_high,
        breakout_confirmed=breakout_confirmed,
        momentum_accelerating=momentum_accel,
        roc_5=roc_5,
    )


def fractional_kelly_risk_pct(
    win_prob: float,
    reward_risk: float,
    fraction: float = KELLY_FRACTION,
    max_pct: float = MAX_KELLY_RISK_PCT,
) -> float:
    """Fractional Kelly bankroll risk cap (default quarter-Kelly, max 3%)."""
    if reward_risk <= 0 or win_prob <= 0:
        return 0.0
    q = 1.0 - win_prob
    b = reward_risk
    full_kelly = (win_prob * b - q) / b
    if full_kelly <= 0:
        return 0.0
    return min(full_kelly * fraction * 100.0, max_pct)


def half_kelly_risk_pct(win_prob: float, reward_risk: float) -> float:
    """Backward-compatible alias — uses configured KELLY_FRACTION."""
    return fractional_kelly_risk_pct(win_prob, reward_risk)


def conviction_technical_multiplier(signals: TechnicalSignals) -> float:
    mult = 1.0
    if signals.midrange_chop:
        mult *= 0.85
    elif signals.breakout_zone:
        mult *= 1.05
    if signals.breakout_confirmed:
        mult *= 1.08
    if signals.near_52w_high and signals.volume_vs_20d >= 1.0:
        mult *= 1.04
    if signals.momentum_accelerating:
        mult *= 1.03
    if signals.pct_from_round <= 0.02 and signals.breakout_zone:
        mult *= 1.02
    if signals.low_volume_breakout:
        mult *= 0.75
    return min(mult, 1.20)
