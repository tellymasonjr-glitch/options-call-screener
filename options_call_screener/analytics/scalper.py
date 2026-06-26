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
    strike = float(row["strike"])
    ask = float(row.get("ask", 0) or 0)
    cost = ask * 100
    gap = strike - spot

    if gap > 0:
        move_need = (
            f"The stock sits at **${spot:.2f}** and would need to climb about **${gap:.2f}** "
            f"to reach the **${strike:.0f}** strike — and typically a bit more for the option "
            f"to be worth what you paid."
        )
    else:
        move_need = (
            f"The stock is at **${spot:.2f}**, at or above the **${strike:.0f}** strike — "
            f"a helpful start, but there are only **hours left** for the bet to pay off."
        )

    vol_note = ""
    if profile and profile.volume_ratio >= 1.25:
        vol_note = (
            "**Activity today:** Trading volume is **higher than usual**. That often means "
            "sharper moves — good if you are right, painful if the stock stalls or reverses."
        )
    elif profile:
        vol_note = (
            "**Activity today:** Volume is about **normal**. Moves may be slower unless "
            "headlines or the broad market heat up."
        )

    spread = float(row.get("spread_pct", 0) or 0)
    if spread >= 0.15:
        spread_note = (
            "**Getting in and out:** The gap between buyers and sellers is **wide** "
            f"(~{spread:.0%} of the price). You may give up meaningful money on entry and exit."
        )
    elif spread >= 0.08:
        spread_note = (
            "**Getting in and out:** The bid/ask gap is **moderately wide** — use a limit order "
            "and do not chase."
        )
    else:
        spread_note = "**Getting in and out:** Spreads look **reasonable** for a same-day contract."

    score = float(row.get("scalper_score", 0) or 0)
    if score >= 70:
        verdict = (
            "This ranks among the **stronger same-day setups** in the scan — but same-day options "
            "are still unforgiving. Have an exit plan before you enter."
        )
    elif score >= 50:
        verdict = (
            "**Decent for a quick trade** if you understand that you can lose the full "
            f"${cost:,.0f} per contract quickly. Not a hold-and-hope idea."
        )
    else:
        verdict = "**Lower ranked** same-day idea — extra caution; consider paper-trading first."

    return (
        f"**Same-day trade on {row['ticker']}:** You are buying a call that expires **today**. "
        f"You pay **${ask:.2f}/share** (**${cost:,.0f} per contract**). {move_need}\n\n"
        f"{vol_note}\n\n{spread_note}\n\n"
        f"**Why it ranked here:** Same-day picks are scored on **how actively the contract "
        f"trades** and **how sensitive it is to price moves today** — not on long-term trend or "
        f"headlines (those barely matter intraday). **Score {score:.0f}/100.** {verdict}"
    )
