"""Expected value and conviction scoring (Black-Scholes + stock behavior)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.pricing import compute_trade_metrics
from analytics.stock_profile import StockProfile
from analytics.volatility import iv_rank, iv_hv_score
from analytics.plain_rationale import generate_plain_english_rationale
from analytics.technical import conviction_technical_multiplier, half_kelly_risk_pct
from config import SCORE_WEIGHTS


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
) -> pd.DataFrame:
    if not contracts:
        return pd.DataFrame()

    hv = _blended_hv(profile, hv_30)
    compound = sentiment.get("mean_compound", 0.0)
    sentiment_score_base = max(0.0, min(100.0, (compound + 1) * 50))
    profile_score_base = profile.profile_score if profile else (70.0 if trend_up else 35.0)

    rows = []
    for c in contracts:
        iv = float(c.get("iv", 0) or 0)
        ask = float(c["ask"])
        dte = int(c["dte"])
        strike = float(c["strike"])
        theta = float(c.get("theta", 0) or 0)

        rank = iv_rank(iv, iv_samples + [iv])
        metrics = compute_trade_metrics(spot, strike, ask, dte, iv, hv, theta)

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
                "sentiment": compound,
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

    multiplier = sentiment.get("multiplier", 1.0)
    tech_mult = (
        conviction_technical_multiplier(profile.tech) if profile is not None else 1.0
    )
    df["macro_multiplier"] = macro_multiplier
    df["technical_multiplier"] = tech_mult
    df["half_kelly_pct"] = df.apply(
        lambda r: half_kelly_risk_pct(float(r["prob_itm"]), float(r["risk_reward"])),
        axis=1,
    )
    base = df["raw_conviction"] * multiplier * macro_multiplier * tech_mult
    df["display_confidence"] = base.clip(0, 100)
    df["kelly_edge_ok"] = df["half_kelly_pct"] > 0
    df["conviction_score"] = df["display_confidence"].copy()
    weak_kelly = ~df["kelly_edge_ok"]
    if weak_kelly.any():
        df.loc[weak_kelly, "conviction_score"] = (
            df.loc[weak_kelly, "display_confidence"] * 0.85
        ).clip(0, 100)
    return df.sort_values("conviction_score", ascending=False).reset_index(drop=True)


def tag_picks(df: pd.DataFrame, max_budget: float, picks: int) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.head(picks).copy()
    result["tag"] = ["best_overall"] + [""] * (len(result) - 1)

    value_candidates = df[df["ev"] > 0].sort_values("iv_rank")
    if not value_candidates.empty:
        best_value = value_candidates.iloc[0]
        if best_value.name not in result.index and len(result) < picks:
            row = best_value.to_frame().T
            row["tag"] = "best_value"
            result = pd.concat([result, row], ignore_index=True)

    budget_cap = max_budget * 0.7
    budget_candidates = df[df["total_cost"] <= budget_cap].sort_values(
        "conviction_score", ascending=False
    )
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
        "theta_pct_daily", "moneyness_pct",
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
