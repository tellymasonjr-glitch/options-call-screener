"""Historical volatility, IV rank, and trend metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def historical_volatility_30(df: pd.DataFrame) -> float:
    """Annualized 30-day historical volatility from log returns."""
    closes = df["close"].astype(float)
    if len(closes) >= 31:
        closes = closes.tail(31)

    log_returns = np.log(closes / closes.shift(1)).dropna()
    if log_returns.empty:
        return 0.25
    return float(log_returns.std() * math.sqrt(252))


def sma(df: pd.DataFrame, window: int = 20) -> float:
    if len(df) < window:
        return float(df["close"].iloc[-1])
    return float(df["close"].astype(float).tail(window).mean())


def trend_bullish(spot: float, sma20: float) -> bool:
    return spot >= sma20


def trend_strength(spot: float, sma20: float) -> float:
    """
    Map spot vs 20-day SMA to a 0-100 score.
    +5% above SMA → 100; -5% below → 0; linear in between.
    """
    if sma20 <= 0:
        return 50.0
    pct = (spot - sma20) / sma20
    return float(np.clip(50.0 + pct * 1000.0, 0.0, 100.0))


def iv_rank(current_iv: float, iv_samples: list[float]) -> float:
    """IV Rank = (current - chain low) / (chain high - chain low) × 100."""
    if current_iv <= 0:
        return 50.0

    samples = [v for v in iv_samples if v and v > 0]
    if len(samples) < 5:
        return float(np.clip(current_iv * 100, 0, 100))

    low, high = min(samples), max(samples)
    if high <= low:
        return 50.0
    return float(np.clip((current_iv - low) / (high - low) * 100, 0, 100))


def iv_hv_score(iv_rank_val: float, iv_hv_ratio: float) -> float:
    """
    Volatility value score: reward cheap options (low IV rank, IV ≈ HV).
    IV/HV > 1.3 means overpaying for vol → low score.
    """
    rank_component = max(0.0, 100.0 - iv_rank_val)
    ratio_penalty = max(0.0, (iv_hv_ratio - 1.0) * 80.0)
    return float(np.clip(rank_component - ratio_penalty, 0.0, 100.0))


def collect_iv_samples(contracts: list[dict]) -> list[float]:
    return [float(c.get("iv", 0) or 0) for c in contracts if c.get("iv")]
