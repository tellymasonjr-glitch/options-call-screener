"""Per-ticker historical behavior, trend, momentum, and market context."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StockProfile:
    ticker: str
    spot: float

    # Volatility regime (annualized)
    hv_30: float
    hv_60: float
    hv_90: float

    # Moving averages
    sma_20: float
    sma_50: float
    sma_200: float
    above_sma_20: bool
    above_sma_50: bool
    above_sma_200: bool
    golden_cross: bool  # SMA50 > SMA200

    # Momentum
    rsi_14: float
    roc_20: float
    roc_60: float
    macd_bullish: bool

    # Price position
    high_52w: float
    low_52w: float
    pct_52w_range: float
    drawdown_from_high: float

    # Volume
    volume_ratio: float

    # vs market (SPY)
    beta_60: float
    rel_strength_20: float
    rel_strength_60: float

    # Composite scores (0-100)
    trend_score: float
    momentum_score: float
    position_score: float
    relative_strength_score: float
    volume_score: float
    profile_score: float


def _annualized_hv(closes: pd.Series, days: int) -> float:
    tail = closes.astype(float).tail(days + 1)
    if len(tail) < 10:
        return 0.25
    log_ret = np.log(tail / tail.shift(1)).dropna()
    if log_ret.empty:
        return 0.25
    return float(log_ret.std() * math.sqrt(252))


def _sma(closes: pd.Series, window: int) -> float:
    if len(closes) < window:
        return float(closes.iloc[-1])
    return float(closes.astype(float).tail(window).mean())


def _rsi(closes: pd.Series, period: int = 14) -> float:
    delta = closes.astype(float).diff().dropna()
    if len(delta) < period:
        return 50.0
    gain = delta.clip(lower=0).tail(period)
    loss = (-delta.clip(upper=0)).tail(period)
    avg_gain = gain.mean()
    avg_loss = loss.mean()
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _roc(closes: pd.Series, days: int) -> float:
    if len(closes) <= days:
        return 0.0
    c = closes.astype(float)
    old = float(c.iloc[-days - 1])
    if old <= 0:
        return 0.0
    return float((c.iloc[-1] - old) / old)


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.astype(float).ewm(span=span, adjust=False).mean()


def _macd_bullish(closes: pd.Series) -> bool:
    if len(closes) < 35:
        return False
    c = closes.astype(float)
    ema12 = _ema(c, 12)
    ema26 = _ema(c, 26)
    macd = ema12 - ema26
    signal = _ema(macd, 9)
    return bool(macd.iloc[-1] > signal.iloc[-1])


def _beta(stock_closes: pd.Series, spy_closes: pd.Series, days: int = 60) -> float:
    s = stock_closes.astype(float).tail(days + 1)
    m = spy_closes.astype(float).tail(days + 1)
    min_len = min(len(s), len(m))
    if min_len < 20:
        return 1.0
    s, m = s.tail(min_len), m.tail(min_len)
    s_ret = np.log(s / s.shift(1)).dropna()
    m_ret = np.log(m / m.shift(1)).dropna()
    aligned = min(len(s_ret), len(m_ret))
    if aligned < 15:
        return 1.0
    s_ret = s_ret.tail(aligned).values
    m_ret = m_ret.tail(aligned).values
    var_m = np.var(m_ret)
    if var_m <= 0:
        return 1.0
    return float(np.cov(s_ret, m_ret)[0, 1] / var_m)


def _relative_strength(stock_closes: pd.Series, spy_closes: pd.Series, days: int) -> float:
    stock_roc = _roc(stock_closes, days)
    spy_roc = _roc(spy_closes, days)
    return stock_roc - spy_roc


def _clip_score(value: float) -> float:
    return float(np.clip(value, 0.0, 100.0))


def _trend_component(spot: float, sma20: float, sma50: float, sma200: float, golden: bool) -> float:
    score = 50.0
    if spot > sma20:
        score += 15
    if spot > sma50:
        score += 15
    if spot > sma200:
        score += 10
    if golden:
        score += 10
    return _clip_score(score)


def _momentum_component(rsi: float, roc20: float, roc60: float, macd_bull: bool) -> float:
    # Calls: prefer RSI 45-70 (momentum without extreme overbought)
    if rsi < 30:
        rsi_score = 30.0
    elif rsi <= 70:
        rsi_score = 50.0 + (rsi - 45) * 1.5
    else:
        rsi_score = max(20.0, 80.0 - (rsi - 70) * 2.0)

    roc_score = _clip_score(50.0 + roc20 * 400 + roc60 * 200)
    macd_bonus = 10.0 if macd_bull else 0.0
    return _clip_score(rsi_score * 0.5 + roc_score * 0.4 + macd_bonus)


def _position_component(pct_52w: float, drawdown: float) -> float:
    # Room to run: not pinned at 52w low, not buying top with no cushion
    if pct_52w < 20:
        score = 40.0 + pct_52w
    elif pct_52w <= 85:
        score = 55.0 + (pct_52w - 20) * 0.5
    else:
        score = max(30.0, 90.0 - (pct_52w - 85) * 2.0)
    if drawdown > 0.15:
        score += 5.0
    return _clip_score(score)


def _rs_component(rs20: float, rs60: float) -> float:
    return _clip_score(50.0 + rs20 * 500 + rs60 * 300)


def _volume_component(ratio: float) -> float:
    if ratio < 0.5:
        return 30.0
    if ratio <= 1.5:
        return 50.0 + (ratio - 0.5) * 30
    return _clip_score(80.0 + (ratio - 1.5) * 10)


def build_stock_profile(
    ticker: str,
    history: pd.DataFrame,
    spy_history: pd.DataFrame | None = None,
) -> StockProfile:
    closes = history["close"].astype(float)
    volumes = history["volume"].astype(float)
    spot = float(closes.iloc[-1])

    hv_30 = _annualized_hv(closes, 30)
    hv_60 = _annualized_hv(closes, 60)
    hv_90 = _annualized_hv(closes, 90)

    sma_20 = _sma(closes, 20)
    sma_50 = _sma(closes, 50)
    sma_200 = _sma(closes, 200) if len(closes) >= 200 else _sma(closes, min(len(closes), 50))

    above_20 = spot > sma_20
    above_50 = spot > sma_50
    above_200 = spot > sma_200
    golden = sma_50 > sma_200

    rsi = _rsi(closes)
    roc_20 = _roc(closes, 20)
    roc_60 = _roc(closes, 60)
    macd_bull = _macd_bullish(closes)

    window = closes.tail(252) if len(closes) >= 252 else closes
    high_52w = float(window.max())
    low_52w = float(window.min())
    if high_52w > low_52w:
        pct_52w = (spot - low_52w) / (high_52w - low_52w) * 100
    else:
        pct_52w = 50.0
    drawdown = (high_52w - spot) / high_52w if high_52w > 0 else 0.0

    avg_vol = float(volumes.tail(20).mean()) if len(volumes) >= 5 else float(volumes.iloc[-1])
    last_vol = float(volumes.iloc[-1])
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1.0

    spy_closes = spy_history["close"] if spy_history is not None and not spy_history.empty else closes
    beta = _beta(closes, spy_closes)
    rs_20 = _relative_strength(closes, spy_closes, 20)
    rs_60 = _relative_strength(closes, spy_closes, 60)

    trend_score = _trend_component(spot, sma_20, sma_50, sma_200, golden)
    momentum_score = _momentum_component(rsi, roc_20, roc_60, macd_bull)
    position_score = _position_component(pct_52w, drawdown)
    rs_score = _rs_component(rs_20, rs_60)
    volume_score = _volume_component(vol_ratio)

    profile_score = _clip_score(
        trend_score * 0.25
        + momentum_score * 0.25
        + position_score * 0.15
        + rs_score * 0.20
        + volume_score * 0.15
    )

    return StockProfile(
        ticker=ticker,
        spot=spot,
        hv_30=hv_30,
        hv_60=hv_60,
        hv_90=hv_90,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        above_sma_20=above_20,
        above_sma_50=above_50,
        above_sma_200=above_200,
        golden_cross=golden,
        rsi_14=rsi,
        roc_20=roc_20,
        roc_60=roc_60,
        macd_bullish=macd_bull,
        high_52w=high_52w,
        low_52w=low_52w,
        pct_52w_range=pct_52w,
        drawdown_from_high=drawdown,
        volume_ratio=vol_ratio,
        beta_60=beta,
        rel_strength_20=rs_20,
        rel_strength_60=rs_60,
        trend_score=trend_score,
        momentum_score=momentum_score,
        position_score=position_score,
        relative_strength_score=rs_score,
        volume_score=volume_score,
        profile_score=profile_score,
    )
