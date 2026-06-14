"""Conviction-scaled position sizing (fractional risk, not raw Kelly)."""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    CONVICTION_TIER1_MIN,
    CONVICTION_TIER1_MULT,
    CONVICTION_TIER2_MIN,
    CONVICTION_TIER2_MULT,
    CONVICTION_TIER3_MIN,
    CONVICTION_TIER3_MULT,
)


@dataclass(frozen=True)
class PositionSize:
    tier: str
    tier_multiplier: float
    risk_budget: float
    risk_pct_of_bankroll: float
    contracts: int
    total_cost: float
    summary: str


def conviction_tier_multiplier(score: float) -> tuple[str, float]:
    if score >= CONVICTION_TIER1_MIN:
        return "Tier 1", CONVICTION_TIER1_MULT
    if score >= CONVICTION_TIER2_MIN:
        return "Tier 2", CONVICTION_TIER2_MULT
    if score >= CONVICTION_TIER3_MIN:
        return "Tier 3", CONVICTION_TIER3_MULT
    return "Below 50", 0.0


def calculate_position_size(
    bankroll: float,
    base_risk_pct: float,
    conviction_score: float,
    ask: float,
) -> PositionSize:
    tier, tier_mult = conviction_tier_multiplier(conviction_score)
    cost_per_contract = ask * 100

    if tier_mult <= 0 or bankroll <= 0 or base_risk_pct <= 0 or cost_per_contract <= 0:
        return PositionSize(
            tier=tier,
            tier_multiplier=tier_mult,
            risk_budget=0.0,
            risk_pct_of_bankroll=0.0,
            contracts=0,
            total_cost=0.0,
            summary="No size — conviction below 50 or invalid inputs.",
        )

    risk_budget = bankroll * (base_risk_pct / 100.0) * tier_mult
    risk_pct = (base_risk_pct * tier_mult)
    contracts = int(risk_budget // cost_per_contract)
    total_cost = contracts * cost_per_contract

    if contracts < 1:
        summary = (
            f"Risk budget ${risk_budget:,.0f} ({risk_pct:.2f}% of bankroll) — "
            f"too small for 1 contract at ${cost_per_contract:,.0f} premium."
        )
    else:
        actual_pct = (total_cost / bankroll) * 100
        summary = (
            f"Recommended: risk ${risk_budget:,.0f} ({risk_pct:.2f}% target) -> "
            f"buy {contracts} contract{'s' if contracts != 1 else ''} "
            f"(${total_cost:,.0f} deployed, {actual_pct:.2f}% of bankroll)."
        )

    return PositionSize(
        tier=tier,
        tier_multiplier=tier_mult,
        risk_budget=risk_budget,
        risk_pct_of_bankroll=risk_pct,
        contracts=contracts,
        total_cost=total_cost,
        summary=summary,
    )


def apply_sizing_to_picks(picks, bankroll: float, base_risk_pct: float):
    """Add sizing columns to a picks DataFrame."""
    if picks.empty or bankroll <= 0:
        return picks

    rows = []
    for _, row in picks.iterrows():
        size = calculate_position_size(
            bankroll,
            base_risk_pct,
            float(row["conviction_score"]),
            float(row["ask"]),
        )
        updated = row.to_dict()
        updated["size_tier"] = size.tier
        updated["size_contracts"] = size.contracts
        updated["size_total_cost"] = size.total_cost
        updated["size_risk_pct"] = size.risk_pct_of_bankroll
        updated["size_summary"] = size.summary
        rows.append(updated)

    import pandas as pd

    return pd.DataFrame(rows)
