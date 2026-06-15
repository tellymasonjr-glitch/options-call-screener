"""Plain-English trade explanations with educational 'why' for each pillar."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.stock_profile import StockProfile


def _edge_narrative(edge_pct: float, ask: float, bs_fair: float) -> str:
    pct = edge_pct * 100
    if edge_pct >= 0.10:
        return (
            f"Our pricing model uses how wildly this stock normally moves and estimates "
            f"this contract *should* cost about ${bs_fair:.2f}. The market is selling it for "
            f"${ask:.2f} — roughly a **{pct:.0f}% discount**. That puts the math on your side, "
            f"like buying something on sale below its typical price."
        )
    if edge_pct >= 0:
        return (
            f"The contract is priced near fair value (${bs_fair:.2f} model vs ${ask:.2f} ask, "
            f"about **{pct:.0f}% edge**). The math is slightly favorable but not a deep discount — "
            f"we need stock health and market weather to carry more of the bet."
        )
    return (
        f"The contract costs **${ask:.2f}**, but our model says fair value is only "
        f"**${bs_fair:.2f}** — you're paying **{abs(pct):.0f}% above** what the math supports. "
        f"This is a weaker math setup unless momentum and news are very strong."
    )


def _health_narrative(profile: StockProfile | None, profile_score: float) -> str:
    if profile is None:
        if profile_score >= 65:
            return (
                f"**Stock health ({profile_score:.0f}/100):** Trend looks supportive. "
                f"Price is holding above its short-term average, which usually means buyers are in control."
            )
        return (
            f"**Stock health ({profile_score:.0f}/100):** Limited trend data — "
            f"treat momentum as uncertain and lean more on the math discount and market weather."
        )

    sma_bits = []
    if profile.above_sma_20:
        sma_bits.append("short-term trend is up")
    else:
        sma_bits.append("short-term trend is down")
    if profile.above_sma_50:
        sma_bits.append("medium-term trend is up")
    else:
        sma_bits.append("medium-term trend is slipping")
    sma_text = "; ".join(sma_bits)

    rsi_note = ""
    if profile.rsi_14 <= 30:
        rsi_note = " RSI is oversold — the stock may be due for a bounce (rubber-band effect)."
    elif profile.rsi_14 >= 70:
        rsi_note = " RSI is stretched — the move may be getting tired."
    macd = "Buyers are in control" if profile.macd_bullish else "Sellers have momentum"

    if profile_score >= 65:
        return (
            f"**Stock health ({profile_score:.0f}/100):** Strong setup. {sma_text.capitalize()}. "
            f"{macd}.{rsi_note} The stock is holding up vs. the market "
            f"({profile.rel_strength_20:+.0%} vs. S&P over 20 days)."
        )
    if profile_score >= 45:
        return (
            f"**Stock health ({profile_score:.0f}/100):** Average — chopping sideways or pausing. "
            f"{sma_text.capitalize()}. {macd}.{rsi_note} We're leaning more on the math discount "
            f"than pure momentum here."
        )
    return (
        f"**Stock health ({profile_score:.0f}/100):** Weak — recent trend is against us. "
        f"{sma_text.capitalize()}. {macd}.{rsi_note} This is a riskier, contrarian bet "
        f"(trying to catch a falling knife)."
    )


def _sentiment_narrative(compound: float) -> str:
    if compound >= 0.15:
        return (
            f"**News tone ({compound:+.2f}):** Headlines are noticeably positive — "
            f"that can draw buyers and support the trade."
        )
    if compound <= -0.15:
        return (
            f"**News tone ({compound:+.2f}):** Headlines are negative — "
            f"bad news can override good math and drag the stock down."
        )
    return (
        f"**News tone ({compound:+.2f}):** Neutral headlines — "
        f"the trade will live or die on price action and market weather, not hype."
    )


def _weather_narrative(macro_mult: float, vix_hint: float | None = None) -> str:
    if macro_mult >= 1.0:
        return (
            "**Market weather:** Calm and supportive. The broad S&P 500 trend is healthy and "
            "fear is low — a rising tide helps most stocks. No safety haircut on your score."
        )
    penalty = int(round((1.0 - macro_mult) * 100))
    reasons: list[str] = []
    if vix_hint and vix_hint >= 18:
        reasons.append(f"fear is elevated (VIX ~{vix_hint:.0f})")
    if macro_mult < 0.85:
        reasons.append("the overall market is in a short-term downtrend")
    reason_text = " and ".join(reasons) if reasons else "conditions are choppy"
    return (
        f"**Market weather (caution):** {reason_text.capitalize()}. "
        f"Because bad markets drag even good stocks down, your score was reduced **{penalty}%** "
        f"to protect capital."
    )


def _verdict_narrative(final_score: float, size_summary: str | None) -> str:
    base = (
        f"**Final confidence score ({final_score:.1f}/100):** "
        f"This blends math discount, stock health, news tone, and market weather. "
    )
    if final_score >= 85:
        verdict = (
            "All four pillars are aligning — this is a top-tier setup. "
            "The risk manager recommends **increasing** your standard bet size (Tier 1)."
        )
    elif final_score >= 70:
        verdict = "Solid, mathematically sound setup — standard bet size is appropriate (Tier 2)."
    elif final_score >= 50:
        verdict = (
            "Mediocre — math may be okay but trend or weather is fighting you. "
            "The risk manager recommends **half** your normal size (Tier 3) or skipping."
        )
    else:
        verdict = "Below our minimum threshold — skip this one or paper-trade only for learning."

    if size_summary:
        verdict += f" **Sizing:** {size_summary}"
    return base + verdict


def generate_plain_english_rationale(
    row: pd.Series | dict[str, Any],
    sentiment: dict[str, float],
    profile: StockProfile | None = None,
    *,
    vix_hint: float | None = None,
) -> str:
    """Build a dynamic, educational paragraph explaining why this pick scored as it did."""
    if isinstance(row, pd.Series):
        data = row.to_dict()
    else:
        data = row

    ticker = data.get("ticker", "This stock")
    strike = float(data["strike"])
    dte = int(data["dte"])
    ask = float(data["ask"])
    bs_fair = float(data.get("bs_fair_hv") or data.get("bs_fair_iv") or ask)
    edge_pct = float(data.get("edge_pct", 0))
    final_score = float(data.get("conviction_score", 0))
    macro_mult = float(data.get("macro_multiplier", 1.0) or 1.0)
    profile_score = float(profile.profile_score) if profile else 50.0
    compound = sentiment.get("mean_compound", 0.0)
    size_summary = data.get("size_summary") or None

    parts = [
        f"**The bet:** We're betting **{ticker}** rises toward or past **${strike:g}** "
        f"within the next **{dte} days** (you lose if it doesn't move enough before time runs out).",
        f"**The math:** {_edge_narrative(edge_pct, ask, bs_fair)}",
        _health_narrative(profile, profile_score),
        _sentiment_narrative(compound),
        _weather_narrative(macro_mult, vix_hint),
        _verdict_narrative(final_score, size_summary),
    ]
    return "\n\n".join(parts)
