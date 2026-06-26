"""0 DTE scalper scoring — volume/gamma focused, not conviction EV."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.stock_profile import StockProfile
from config import SCALPER_WEIGHTS


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    lo, hi = series.min(), series.max()
    if hi <= lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - lo) / (hi - lo) * 100).clip(0, 100)


def score_0dte_contracts(
    contracts: list[dict[str, Any]],
    spot: float,
    profile: StockProfile | None = None,
) -> pd.DataFrame:
    if not contracts:
        return pd.DataFrame()

    hv = profile.hv_30 if profile else 0.25
    vol_spike = profile.volume_ratio if profile else 1.0

    rows = []
    for c in contracts:
        iv = max(float(c.get("iv", 0) or 0), 0.05)
        hv_eff = max(hv, 0.05)
        iv_hv = iv / hv_eff
        gamma = abs(float(c.get("gamma", 0) or 0))
        strike = float(c["strike"])
        atm_dist = abs(spot - strike) / spot if spot > 0 else 1.0
        vol = int(c.get("volume", 0) or 0)
        spread = float(c.get("spread_pct", 0) or 0)

        volume_score = min(vol / 500, 1.0) * 100
        iv_spike_score = min(max(iv_hv - 1.0, 0.0) / 0.5, 1.0) * 100
        gamma_score = min(gamma / 0.08, 1.0) * 100
        liquidity_score = max(0.0, 1.0 - spread / 0.28) * 100
        atm_score = max(0.0, 1.0 - atm_dist / 0.04) * 100

        raw = (
            volume_score * SCALPER_WEIGHTS["volume"]
            + iv_spike_score * SCALPER_WEIGHTS["iv_spike"]
            + gamma_score * SCALPER_WEIGHTS["gamma"]
            + liquidity_score * SCALPER_WEIGHTS["liquidity"]
            + atm_score * SCALPER_WEIGHTS["atm_proximity"]
        )
        if vol_spike >= 1.25:
            raw = min(raw * 1.08, 100.0)

        rows.append(
            {
                **c,
                "iv_hv_ratio": iv_hv,
                "scalper_score": raw,
                "conviction_score": raw,  # for shared sort/display helpers
                "scan_mode": "0dte_scalper",
                "tag": "0dte_scalper",
            }
        )

    df = pd.DataFrame(rows)
    df["volume_score"] = _normalize(df["volume"].astype(float))
    return df.sort_values("scalper_score", ascending=False).reset_index(drop=True)


def tag_scalper_picks(df: pd.DataFrame, picks: int) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.head(picks).copy()
    result["tag"] = ["0dte_best"] + ["0dte_scalper"] * (len(result) - 1)
    return result


def build_scalper_rationale(row: pd.Series, spot: float, profile: StockProfile | None) -> str:
    vol_note = ""
    if profile and profile.volume_ratio >= 1.25:
        vol_note = "Trading volume is higher than usual today — more action, but also more whipsaw. "
    elif profile:
        vol_note = "Trading volume is about normal today. "

    spread = float(row.get("spread_pct", 0) or 0)
    spread_note = ""
    if spread >= 0.15:
        spread_note = "The buy/sell gap is wide — getting in and out may cost you extra. "
    elif spread >= 0.08:
        spread_note = "The buy/sell gap is a bit wide — watch your entry price. "

    score = float(row.get("scalper_score", 0) or 0)
    if score >= 70:
        verdict = "This is one of the stronger same-day setups in the scan."
    elif score >= 50:
        verdict = "Decent for a quick same-day trade, but only if you know how to exit fast."
    else:
        verdict = "Lower ranked same-day idea — extra caution."

    return (
        f"**Same-day trade on {row['ticker']}:** You are betting the stock moves up **before the close today**. "
        f"Stock price now **${spot:.2f}**, target strike **${row['strike']:.0f}**. "
        f"{vol_note}{spread_note}"
        f"**Why it ranked here:** Lots of trading activity and sensitivity to price moves today — "
        f"not a long-term \"investment\" pick. **Score {score:.0f}/100.** {verdict}"
    )
