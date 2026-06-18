"""Mirror Check — beta-weighted SPY-equivalent exposure for open paper trades."""

from __future__ import annotations

import pandas as pd

from config import SPY_EXPOSURE_WARN_SHARES


def open_journal_trades(journal: pd.DataFrame) -> pd.DataFrame:
    if journal.empty or "status" not in journal.columns:
        return pd.DataFrame()
    return journal[journal["status"].astype(str).str.lower() == "open"].copy()


def beta_weighted_spy_shares(
    open_trades: pd.DataFrame,
    spy_price: float,
    *,
    live_spots: dict[str, float] | None = None,
) -> tuple[float, list[dict[str, float | str]]]:
    """
    Translate long-call deltas into SPY-equivalent share exposure.

    Per leg: delta × contracts × 100 × spot × beta / SPY_price
    """
    if open_trades.empty or spy_price <= 0:
        return 0.0, []

    live_spots = live_spots or {}
    total = 0.0
    legs: list[dict[str, float | str]] = []

    for _, row in open_trades.iterrows():
        ticker = str(row.get("ticker", "")).upper()
        delta = float(row.get("delta") or 0)
        beta = float(row.get("beta") or 1.0)
        contracts = max(1, int(float(row.get("contracts") or 1)))
        spot = float(live_spots.get(ticker) or row.get("spot_at_entry") or 0)
        if delta <= 0 or spot <= 0:
            continue

        spy_equiv = delta * contracts * 100.0 * spot * beta / spy_price
        total += spy_equiv
        legs.append(
            {
                "ticker": ticker,
                "spy_equiv_shares": round(spy_equiv, 1),
                "delta": delta,
                "beta": beta,
                "contracts": contracts,
            }
        )

    return total, legs


def exposure_warning(spy_equiv_shares: float) -> str | None:
    if spy_equiv_shares >= SPY_EXPOSURE_WARN_SHARES:
        return (
            f"Mirror Check — you hold the equivalent of **{spy_equiv_shares:,.0f} SPY shares** "
            f"(warn threshold: {SPY_EXPOSURE_WARN_SHARES:,.0f}). "
            "Multiple tech calls can collapse into one leveraged Nasdaq bet."
        )
    return None
