"""Expected value and conviction scoring (Black-Scholes-Merton + risk filters)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.calendar import calendar_multiplier
from analytics.portfolio_stress import long_call_stress_test
from analytics.pricing import compute_trade_metrics
from analytics.risk_signals import evaluate_contract_risks, risk_penalty_multiplier
from analytics.stock_profile import StockProfile
from analytics.volatility import iv_rank, iv_hv_score
from analytics.plain_rationale import generate_plain_english_rationale
from analytics.technical import conviction_technical_multiplier, fractional_kelly_risk_pct
from config import (
    EPR_LOSS_PCT,
    HIGH_SPREAD_WARNING_PCT,
    MIN_OPEN_INTEREST,
    MIN_VOLUME,
    SCORE_WEIGHTS,
    SMA200_CONFIDENCE_MULT,
    SMA200_KELLY_MULT,
    SPREAD_CONFIDENCE_HALVE_PCT,
)
from data.earnings import earnings_hard_block


def _normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    lo, hi = series.min(), series.max()
    if hi <= lo:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - lo) / (hi - lo) * 100).clip(0, 100)


def _liquidity_score(row: pd.Series) -> float:
    oi_score = min(row["open_interest"] / 500, 1.0) * 50
    vol_score = min(row["volume"] / 200, 1.0) * 30
    spread_score = max(0.0, 1.0 - row["spread_pct"] / 0.15) * 20
    return oi_score + vol_score + spread_score


def _blended_hv(profile: StockProfile | None, fallback: float) -> float:
    if profile is None:
        return fallback
    return profile.hv_30 * 0.5 + profile.hv_60 * 0.3 + profile.hv_90 * 0.2


def _contract_near_earnings(expiration: str, earnings_dates: list) -> bool:
    if not earnings_dates:
        return False
    try:
        exp = pd.to_datetime(expiration).date()
    except Exception:
        return False
    for earn in earnings_dates:
        if abs((exp - earn).days) <= 14:
            return True
    return False


def _spread_confidence_mult(spread_pct: float) -> float:
    """Ghost Tax — wide bid/ask erodes edge before the trade starts."""
    if spread_pct >= SPREAD_CONFIDENCE_HALVE_PCT:
        return 0.5
    if spread_pct >= HIGH_SPREAD_WARNING_PCT:
        return 0.75
    return 1.0


def score_contracts(
    contracts: list[dict[str, Any]],
    spot: float,
    hv_30: float,
    trend_up: bool,
    sentiment: dict[str, float],
    iv_samples: list[float],
    profile: StockProfile | None = None,
    sma20: float | None = None,
    macro_multiplier: float = 1.0,
    div_yield: float = 0.0,
    earnings_dates: list | None = None,
    bankroll: float = 10_000.0,
) -> pd.DataFrame:
    if not contracts:
        return pd.DataFrame()

    hv = _blended_hv(profile, hv_30)
    compound = sentiment.get("mean_compound", 0.0)
    sentiment_score_base = max(0.0, min(100.0, (compound + 1) * 50))
    profile_score_base = profile.profile_score if profile else (70.0 if trend_up else 35.0)
    cal_mult, cal_note = calendar_multiplier()
    earnings_dates = earnings_dates or []

    rows = []
    for c in contracts:
        iv = float(c.get("iv", 0) or 0)
        ask = float(c["ask"])
        dte = int(c["dte"])
        strike = float(c["strike"])
        theta = float(c.get("theta", 0) or 0)
        delta = float(c.get("delta", 0) or 0)
        spread_pct = float(c.get("spread_pct", 0) or 0)
        oi = int(c.get("open_interest", 0) or 0)
        vol = int(c.get("volume", 0) or 0)
        empty_room = oi < MIN_OPEN_INTEREST or vol < MIN_VOLUME

        rank = iv_rank(iv, iv_samples + [iv])
        near_earn = _contract_near_earnings(str(c.get("expiration", "")), earnings_dates)
        earn_nogo = earnings_hard_block(str(c.get("expiration", "")), earnings_dates)
        metrics = compute_trade_metrics(
            spot, strike, ask, dte, iv, hv, theta, div_yield=div_yield
        )
        flags = evaluate_contract_risks(
            iv_rank=rank,
            dte=dte,
            delta=delta,
            spread_pct=spread_pct,
            ask=ask,
            near_earnings=near_earn,
            open_interest=oi,
            volume=vol,
        )
        stress = long_call_stress_test(
            spot,
            strike,
            ask,
            dte,
            iv,
            div_yield=div_yield,
            epr_limit_pct=EPR_LOSS_PCT,
            bankroll=bankroll,
        )

        rows.append(
            {
                **c,
                "iv_rank": rank,
                "bs_fair_iv": metrics.bs_fair_iv,
                "bs_fair_hv": metrics.bs_fair_hv,
                "prob_itm": metrics.prob_itm,
                "ev": metrics.ev_hv,
                "edge_pct": metrics.edge_pct,
                "iv_hv_ratio": metrics.iv_hv_ratio,
                "breakeven": metrics.breakeven,
                "expected_move": metrics.expected_move,
                "payoff_1sigma": metrics.payoff_1sigma,
                "risk_reward": metrics.risk_reward,
                "theta_pct_daily": metrics.theta_pct_daily,
                "moneyness_pct": metrics.moneyness_pct,
                "vega_dollars": metrics.vega_per_contract,
                "rho": metrics.rho,
                "vanna": metrics.vanna,
                "charm": metrics.charm,
                "sentiment": compound,
                "risk_warnings": "|".join(flags.warning_messages),
                "iv_crush_warning": flags.iv_crush_warning,
                "vega_overpay_warning": flags.vega_overpay_warning,
                "gamma_warning": flags.gamma_acceleration_warning,
                "spread_friction": flags.spread_friction_dollars,
                "max_loss_dollars": flags.max_loss_dollars,
                "risk_penalty_mult": risk_penalty_multiplier(flags),
                "calendar_note": cal_note,
                "stress_max_loss": stress.max_loss_dollars,
                "stress_passes_epr": stress.passes_epr,
                "stress_worst_spot": stress.worst_spot_shock,
                "stress_worst_vol": stress.worst_vol_shock,
                "earnings_nogo": earn_nogo,
                "empty_room": empty_room,
            }
        )

    df = pd.DataFrame(rows)

    df["ev_score"] = _normalize(df["ev"])
    df["prob_score"] = (df["prob_itm"] * 100).clip(0, 100)
    df["vol_value_score"] = df.apply(
        lambda r: iv_hv_score(r["iv_rank"], r["iv_hv_ratio"]), axis=1
    )
    df["liquidity_score"] = df.apply(_liquidity_score, axis=1)
    df["stock_profile_score"] = profile_score_base
    df["sentiment_score"] = sentiment_score_base
    df["efficiency_score"] = _normalize(df["edge_pct"] * 100)
    df["theta_score"] = df["theta_pct_daily"].apply(
        lambda t: max(0.0, 100.0 - t * 10.0)
    )

    df["raw_conviction"] = (
        df["ev_score"] * SCORE_WEIGHTS["ev_hv"]
        + df["prob_score"] * SCORE_WEIGHTS["prob_itm"]
        + df["vol_value_score"] * SCORE_WEIGHTS["vol_value"]
        + df["liquidity_score"] * SCORE_WEIGHTS["liquidity"]
        + df["stock_profile_score"] * SCORE_WEIGHTS["stock_profile"]
        + df["sentiment_score"] * SCORE_WEIGHTS["sentiment"]
        + df["efficiency_score"] * SCORE_WEIGHTS["efficiency"]
        + df["theta_score"] * SCORE_WEIGHTS["theta"]
    )

    sentiment_mult = sentiment.get("multiplier", 1.0)
    tech_mult = (
        conviction_technical_multiplier(profile.tech) if profile is not None else 1.0
    )
    df["macro_multiplier"] = macro_multiplier
    df["calendar_multiplier"] = cal_mult
    df["technical_multiplier"] = tech_mult
    df["half_kelly_pct"] = df.apply(
        lambda r: fractional_kelly_risk_pct(float(r["prob_itm"]), float(r["risk_reward"])),
        axis=1,
    )

    spread_mult = df["spread_pct"].apply(_spread_confidence_mult)
    tide_mult = SMA200_CONFIDENCE_MULT if (profile is not None and not profile.above_sma_200) else 1.0
    if profile is not None and not profile.above_sma_200:
        df["half_kelly_pct"] = df["half_kelly_pct"] * SMA200_KELLY_MULT

    base = (
        df["raw_conviction"]
        * sentiment_mult
        * macro_multiplier
        * cal_mult
        * tech_mult
        * df["risk_penalty_mult"]
        * spread_mult
        * tide_mult
    )
    df["display_confidence"] = base.clip(0, 100)
    df["spread_mult"] = spread_mult
    df["tide_mult"] = tide_mult
    df["conviction_score"] = df["display_confidence"].copy()

    if "earnings_nogo" in df.columns:
        nogo = df["earnings_nogo"].fillna(False).astype(bool)
        df.loc[nogo, "display_confidence"] = 0.0
        df.loc[nogo, "conviction_score"] = 0.0

    if "empty_room" in df.columns:
        ghost = df["empty_room"].fillna(False).astype(bool)
        df.loc[ghost, "display_confidence"] = 0.0
        df.loc[ghost, "conviction_score"] = 0.0

    df["kelly_edge_ok"] = df["half_kelly_pct"] > 0
    weak_kelly = ~df["kelly_edge_ok"]
    if weak_kelly.any():
        df.loc[weak_kelly, "conviction_score"] = (
            df.loc[weak_kelly, "display_confidence"] * 0.85
        ).clip(0, 100)

    if "stress_passes_epr" in df.columns:
        stress_fail = ~df["stress_passes_epr"].fillna(True).astype(bool)
        if stress_fail.any():
            df.loc[stress_fail, "conviction_score"] = (
                df.loc[stress_fail, "conviction_score"] * 0.88
            ).clip(0, 100)

    return df.sort_values("conviction_score", ascending=False).reset_index(drop=True)


def tag_picks(df: pd.DataFrame, max_budget: float, picks: int) -> pd.DataFrame:
    if df.empty:
        return df

    ranked = df.sort_values("conviction_score", ascending=False)
    result = ranked.head(picks).copy()
    result["tag"] = ["best_overall"] + [""] * (len(result) - 1)

    value_candidates = ranked[ranked["ev"] > 0].sort_values("iv_rank")
    if not value_candidates.empty:
        best_value = value_candidates.iloc[0]
        if best_value.name not in result.index and len(result) < picks:
            row = best_value.to_frame().T
            row["tag"] = "best_value"
            result = pd.concat([result, row], ignore_index=True)

    budget_cap = max_budget * 0.7
    budget_candidates = ranked[ranked["total_cost"] <= budget_cap]
    if not budget_candidates.empty:
        best_budget = budget_candidates.iloc[0]
        if best_budget.name not in result.index and len(result) < picks + 2:
            row = best_budget.to_frame().T
            row["tag"] = "best_budget"
            result = pd.concat([result, row], ignore_index=True)

    result = result.head(picks + 2)

    numeric_cols = [
        "strike", "ask", "total_cost", "dte", "delta", "theta", "iv", "iv_rank",
        "open_interest", "volume", "spread_pct", "ev", "conviction_score",
        "display_confidence", "raw_conviction", "half_kelly_pct",
        "bs_fair_iv", "bs_fair_hv", "prob_itm", "edge_pct", "iv_hv_ratio",
        "breakeven", "expected_move", "payoff_1sigma", "risk_reward",
        "theta_pct_daily", "moneyness_pct", "vega_dollars", "rho",
        "spread_friction", "max_loss_dollars", "risk_penalty_mult",
        "calendar_multiplier", "technical_multiplier", "macro_multiplier",
    ]
    clean_rows = []
    for _, row in result.iterrows():
        clean = row.to_dict()
        for col in numeric_cols:
            if col in clean:
                val = pd.to_numeric(clean[col], errors="coerce")
                if pd.isna(val):
                    continue
                clean[col] = float(val)
        clean_rows.append(clean)

    return pd.DataFrame(clean_rows)


def build_rationale(
    row: pd.Series,
    spot: float,
    sentiment: dict,
    profile: StockProfile | None = None,
    vix_hint: float | None = None,
) -> str:
    return generate_plain_english_rationale(
        row, sentiment, profile, vix_hint=vix_hint
    )
