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


def build_scalper_rationale(
    row: pd.Series,
    spot: float,
    profile: StockProfile | None,
    *,
    target_dte: int | None = None,
) -> str:
    dte = int(target_dte if target_dte is not None else row.get("dte", 0) or 0)
    strike = float(row["strike"])
    ask = float(row.get("ask", 0) or 0)
    cost = ask * 100
    gap = strike - spot

    if dte == 0:
        expiry_line = "You are buying a call that expires **today** (same-day)."
        time_pressure = "there are only **hours left** for the bet to pay off"
    elif dte == 1:
        expiry_line = "You are buying a call that expires **tomorrow** (next session)."
        time_pressure = "you need a move **by tomorrow's close**"
    else:
        expiry_line = f"You are buying a call that expires in **{dte} days** (nearest quick-scalp expiry)."
        time_pressure = f"you need a move within **{dte} days**"

    if gap > 0:
        move_need = (
            f"The stock sits at **${spot:.2f}** and would need to climb about **${gap:.2f}** "
            f"to reach the **${strike:.0f}** strike — and typically a bit more for the option "
            f"to be worth what you paid."
        )
    else:
        move_need = (
            f"The stock is at **${spot:.2f}**, at or above the **${strike:.0f}** strike — "
            f"a helpful start, but {time_pressure}."
        )

    vol_note = ""
    if profile and profile.volume_ratio >= 1.25:
        vol_note = (
            "**Activity:** Trading volume is **higher than usual** — sharper moves, more whipsaw."
        )
    elif profile:
        vol_note = "**Activity:** Volume is about **normal** for this name."

    spread = float(row.get("spread_pct", 0) or 0)
    if spread >= 0.15:
        spread_note = (
            "**Getting in and out:** The gap between buyers and sellers is **wide** "
            f"(~{spread:.0%} of the price)."
        )
    elif spread >= 0.08:
        spread_note = "**Getting in and out:** Bid/ask gap is **moderately wide** — use a limit order."
    else:
        spread_note = "**Getting in and out:** Spreads look **reasonable**."

    score = float(row.get("scalper_score", 0) or 0)
    if score >= 70:
        verdict = "Stronger quick-scalp setup in this scan — still have an exit plan before you enter."
    elif score >= 50:
        verdict = (
            f"Decent quick trade if you accept losing the full ${cost:,.0f} per contract is possible."
        )
    else:
        verdict = "Lower ranked quick-scalp idea — extra caution."

    label = "Quick-scalp" if dte != 0 else "Same-day"
    return (
        f"**{label} trade on {row['ticker']}:** {expiry_line} "
        f"You pay **${ask:.2f}/share** (**${cost:,.0f} per contract**). {move_need}\n\n"
        f"{vol_note}\n\n{spread_note}\n\n"
        f"**Why it ranked here:** Quick-scalp picks favor **active contracts** sensitive to "
        f"near-term price moves — not long-term trend. **Score {score:.0f}/100.** {verdict}"
    )
