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
    if profile:
        vol_note = f"Stock volume {profile.volume_ratio:.1f}x 20d avg. "
    return (
        f"0 DTE scalper: {row['ticker']} ${row['strike']:.0f} call exp {row['expiration']}. "
        f"Spot ${spot:.2f}, Δ {row.get('delta', 0):.2f}, Γ {row.get('gamma', 0):.3f}. "
        f"Volume {int(row.get('volume', 0))}, spread {row.get('spread_pct', 0):.1%}, "
        f"IV/HV {row.get('iv_hv_ratio', 1):.2f}. {vol_note}"
        f"Scalper score {row.get('scalper_score', 0):.1f}/100 — "
        f"not ranked by conviction EV (SMA/sentiment have little effect intraday)."
    )
