"""Conviction-scaled position sizing (fractional risk, not raw Kelly)."""

from __future__ import annotations

from dataclasses import dataclass

from analytics.empirical_kelly import get_journal_for_kelly, resolve_kelly_cap
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
        return "High confidence", CONVICTION_TIER1_MULT
    if score >= CONVICTION_TIER2_MIN:
        return "Solid setup", CONVICTION_TIER2_MULT
    if score >= CONVICTION_TIER3_MIN:
        return "Cautious size", CONVICTION_TIER3_MULT
    return "Skip", 0.0


def calculate_position_size(
    bankroll: float,
    base_risk_pct: float,
    conviction_score: float,
    ask: float,
    max_risk_pct: float | None = None,
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
            summary="No size — confidence below 50 or invalid inputs.",
        )

    risk_budget = bankroll * (base_risk_pct / 100.0) * tier_mult
    risk_pct = base_risk_pct * tier_mult
    if max_risk_pct is not None and max_risk_pct > 0:
        risk_pct = min(risk_pct, max_risk_pct)
        risk_budget = bankroll * (risk_pct / 100.0)
    contracts = int(risk_budget // cost_per_contract)
    total_cost = contracts * cost_per_contract

    if contracts < 1:
        summary = (
            f"Budget ${risk_budget:,.0f} ({risk_pct:.2f}% of account) — "
            f"not enough for even 1 contract at ${cost_per_contract:,.0f} total cost."
        )
    else:
        actual_pct = (total_cost / bankroll) * 100
        summary = (
            f"Because confidence is {tier.lower()}, risk {risk_pct:.2f}% of your account "
            f"(${risk_budget:,.0f}) -> buy **{contracts}** contract{'s' if contracts != 1 else ''} "
            f"(${total_cost:,.0f} total, {actual_pct:.2f}% of account)."
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

    import pandas as pd

    journal = get_journal_for_kelly()
    rows = []
    for _, row in picks.iterrows():
        hk = row.get("half_kelly_pct")
        theoretical = (
            float(hk)
            if hk is not None and hk == hk and float(hk) > 0  # NaN-safe
            else 0.0
        )
        kelly_cap = resolve_kelly_cap(theoretical, journal)
        max_risk = kelly_cap.final_pct if kelly_cap.final_pct > 0 else None
        score_val = None
        for key in ("display_confidence", "conviction_score"):
            val = row.get(key)
            if val is not None and not pd.isna(val):
                score_val = float(val)
                break
        size = calculate_position_size(
            bankroll,
            base_risk_pct,
            score_val or 0.0,
            float(row["ask"]),
            max_risk_pct=max_risk,
        )
        updated = row.to_dict()
        updated["size_tier"] = size.tier
        updated["size_contracts"] = size.contracts
        updated["size_total_cost"] = size.total_cost
        updated["size_risk_pct"] = size.risk_pct_of_bankroll
        updated["kelly_theoretical_pct"] = kelly_cap.theoretical_pct
        updated["kelly_empirical_pct"] = kelly_cap.empirical_pct
        updated["kelly_final_cap_pct"] = kelly_cap.final_pct
        if (
            kelly_cap.empirical.sufficient
            and kelly_cap.empirical_pct is not None
            and kelly_cap.final_pct < kelly_cap.theoretical_pct
        ):
            updated["kelly_empirical_note"] = (
                f"Empirical Kelly capped risk at {kelly_cap.final_pct:.1f}% "
                f"(theoretical {kelly_cap.theoretical_pct:.1f}%, "
                f"journal {kelly_cap.empirical_pct:.1f}%)."
            )
        else:
            updated["kelly_empirical_note"] = kelly_cap.empirical.note
        if updated.get("mc_passes_cap") is False and size.contracts > 0:
            updated["size_contracts"] = max(0, size.contracts // 2)
            updated["size_total_cost"] = updated["size_contracts"] * float(row["ask"]) * 100
            updated["size_summary"] = (
                f"{size.summary} Monte Carlo P95 loss exceeded cap — size cut 50%."
            )
        else:
            updated["size_summary"] = size.summary
        rows.append(updated)

    return pd.DataFrame(rows)
