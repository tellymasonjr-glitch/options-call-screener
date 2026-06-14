"""Hard filters for options contracts."""

from __future__ import annotations

from config import (
    MAX_IV_RANK_HARD,
    MAX_SPREAD_PCT,
    MAX_SPREAD_PCT_0DTE,
    MIN_OPEN_INTEREST,
    MIN_OPEN_INTEREST_0DTE,
    MIN_VOLUME,
    MIN_VOLUME_0DTE,
)


def bid_ask_spread_pct(bid: float, ask: float) -> float | None:
    if bid <= 0 or ask <= 0:
        return None
    mid = (bid + ask) / 2
    if mid <= 0:
        return None
    return (ask - bid) / mid


def passes_hard_filters(
    contract: dict,
    max_budget: float,
    delta_min: float,
    delta_max: float,
    iv_rank: float,
) -> tuple[bool, str]:
    ask = float(contract.get("ask", 0) or 0)
    total_cost = ask * 100

    if total_cost <= 0:
        return False, "missing ask price"
    if total_cost > max_budget:
        return False, "over budget"

    oi = int(contract.get("open_interest", 0) or 0)
    vol = int(contract.get("volume", 0) or 0)
    if oi < MIN_OPEN_INTEREST:
        return False, f"open interest {oi} < {MIN_OPEN_INTEREST}"
    if vol < MIN_VOLUME:
        return False, f"volume {vol} < {MIN_VOLUME}"

    spread = bid_ask_spread_pct(
        float(contract.get("bid", 0) or 0),
        ask,
    )
    if spread is None:
        return False, "invalid bid/ask"
    if spread > MAX_SPREAD_PCT:
        return False, f"spread {spread:.1%} too wide"

    delta = float(contract.get("delta", 0) or 0)
    if delta < delta_min or delta > delta_max:
        return False, f"delta {delta:.2f} outside {delta_min}-{delta_max}"

    if iv_rank > MAX_IV_RANK_HARD:
        return False, f"IV rank {iv_rank:.0f} too high"

    contract["total_cost"] = total_cost
    contract["spread_pct"] = spread
    return True, "ok"


def passes_0dte_filters(
    contract: dict,
    max_budget: float,
    delta_min: float,
    delta_max: float,
) -> tuple[bool, str]:
    """Relaxed liquidity filters for same-day (0 DTE) scalper mode."""
    ask = float(contract.get("ask", 0) or 0)
    total_cost = ask * 100

    if total_cost <= 0:
        return False, "missing ask price"
    if total_cost > max_budget:
        return False, "over budget"

    oi = int(contract.get("open_interest", 0) or 0)
    vol = int(contract.get("volume", 0) or 0)
    if oi < MIN_OPEN_INTEREST_0DTE:
        return False, f"open interest {oi} < {MIN_OPEN_INTEREST_0DTE}"
    if vol < MIN_VOLUME_0DTE:
        return False, f"volume {vol} < {MIN_VOLUME_0DTE}"

    spread = bid_ask_spread_pct(
        float(contract.get("bid", 0) or 0),
        ask,
    )
    if spread is None:
        return False, "invalid bid/ask"
    if spread > MAX_SPREAD_PCT_0DTE:
        return False, f"spread {spread:.1%} too wide for 0 DTE"

    delta = float(contract.get("delta", 0) or 0)
    if delta < delta_min or delta > delta_max:
        return False, f"delta {delta:.2f} outside {delta_min}-{delta_max}"

    contract["total_cost"] = total_cost
    contract["spread_pct"] = spread
    return True, "ok"
