"""Plain-English trade explanations — written for people new to options."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.stock_profile import StockProfile


def _edge_narrative(edge_pct: float, ask: float, bs_fair: float) -> str:
    pct = edge_pct * 100
    if edge_pct >= 0.10:
        return (
            f"We think this option *should* cost about ${bs_fair:.2f}, but the market is asking "
            f"${ask:.2f} — roughly **{pct:.0f}% cheaper than our estimate**. "
            f"That is like finding the same item on sale."
        )
    if edge_pct >= 0:
        return (
            f"The price looks **fair** (our estimate ${bs_fair:.2f} vs market ${ask:.2f}). "
            f"There is a small edge, but we are not getting a big discount — "
            f"the stock still needs to cooperate."
        )
    return (
        f"The market wants **${ask:.2f}**, but our estimate is only **${bs_fair:.2f}** — "
        f"you may be paying about **{abs(pct):.0f}% more** than our model thinks it is worth. "
        f"That makes this a weaker deal unless the stock moves hard in your favor."
    )


def _health_narrative(profile: StockProfile | None, profile_score: float) -> str:
    if profile is None:
        if profile_score >= 65:
            return (
                f"**How the stock is doing ({profile_score:.0f}/100):** "
                f"Recent price action looks okay — buyers seem to be holding the line."
            )
        return (
            f"**How the stock is doing ({profile_score:.0f}/100):** "
            f"Not much trend data — treat direction as a guess and rely more on price vs. our estimate."
        )

    if profile.above_sma_20 and profile.above_sma_50:
        trend = "Price is above its recent averages — that usually means the stock is in an uptrend."
    elif not profile.above_sma_20 and not profile.above_sma_50:
        trend = "Price is below its recent averages — the stock has been drifting down."
    else:
        trend = "The trend is mixed — up in some time frames, down in others."

    mood = "More buyers than sellers lately." if profile.macd_bullish else "Sellers have had the upper hand lately."

    rsi_note = ""
    if profile.rsi_14 <= 30:
        rsi_note = " The stock has fallen a lot recently — sometimes that leads to a bounce, but not always."
    elif profile.rsi_14 >= 70:
        rsi_note = " The stock has run up a lot — the easy gains may already be behind it."

    if profile_score >= 65:
        return (
            f"**How the stock is doing ({profile_score:.0f}/100):** Looking healthy. "
            f"{trend} {mood}{rsi_note}"
        )
    if profile_score >= 45:
        return (
            f"**How the stock is doing ({profile_score:.0f}/100):** Middle of the road — "
            f"not terrible, not exciting. {trend} {mood}{rsi_note}"
        )
    return (
        f"**How the stock is doing ({profile_score:.0f}/100):** Weak lately. "
        f"{trend} {mood}{rsi_note} This is a higher-risk bet on a turnaround."
    )


def _sentiment_narrative(compound: float) -> str:
    if compound >= 0.15:
        return (
            "**Headlines:** Mostly positive news lately — that can help push the stock up."
        )
    if compound <= -0.15:
        return (
            "**Headlines:** Mostly negative news lately — bad headlines can sink a stock "
            "even when the option price looks okay."
        )
    return (
        "**Headlines:** Nothing dramatic in the news — the stock will move on price action, not hype."
    )


def _weather_narrative(macro_mult: float, vix_hint: float | None = None) -> str:
    if macro_mult >= 1.0:
        return (
            "**Overall market:** Calm. The broad market is steady and fear is low — "
            "that usually helps most stocks."
        )
    penalty = int(round((1.0 - macro_mult) * 100))
    reasons: list[str] = []
    if vix_hint and vix_hint >= 18:
        reasons.append("investors are nervous")
    if macro_mult < 0.85:
        reasons.append("the overall market has been sliding")
    reason_text = " and ".join(reasons) if reasons else "conditions are choppy"
    return (
        f"**Overall market (caution):** {reason_text.capitalize()}. "
        f"We lowered your score about **{penalty}%** because when the whole market struggles, "
        f"individual stocks often struggle too."
    )


def _gates_narrative(data: dict[str, Any]) -> str:
    notes: list[str] = []
    ex = data.get("ex_div_note")
    if ex and str(ex).strip():
        notes.append(
            "**Dividend warning:** A dividend date falls before this option expires. "
            "Stocks often dip on dividend days, which can hurt call options."
        )
    regime = data.get("garch_regime")
    if regime == "compress":
        notes.append(
            "**Volatility outlook:** We expect calmer days ahead — be careful you are not "
            "overpaying for a \"fear premium\" that may fade."
        )
    elif regime == "expand":
        notes.append(
            "**Volatility outlook:** We expect bumpier days ahead — big moves are more likely, "
            "for better or worse."
        )
    warnings = data.get("risk_warnings")
    if warnings and str(warnings).strip():
        for msg in str(warnings).split("|"):
            msg = msg.strip()
            if not msg:
                continue
            if "IV Crush" in msg or "iv crush" in msg.lower():
                notes.append(
                    "**Earnings nearby:** Option prices often drop after earnings even if you "
                    "guessed direction right — extra risk."
                )
            elif "Vega" in msg or "vega" in msg.lower():
                notes.append(
                    "**Pricey options:** You may be paying a lot for \"insurance\" against big moves."
                )
            elif "Gamma" in msg or "gamma" in msg.lower():
                notes.append(
                    "**Expires very soon:** With little time left, small price moves can swing "
                    "your profit or loss sharply."
                )
            elif "Empty Room" in msg or "liquidity" in msg.lower():
                notes.append(
                    "**Thin trading:** Not many buyers and sellers — harder to get out at a fair price."
                )
    mc = data.get("mc_p95_loss")
    if mc is not None and not (isinstance(mc, float) and pd.isna(mc)):
        mc_f = float(mc)
        if data.get("mc_passes_cap") is False:
            notes.append(
                f"**Stress test:** In a bad-but-realistic scenario, you could lose about "
                f"${mc_f:,.0f} — more than we like for your account size."
            )
        elif mc_f > 0:
            notes.append(
                f"**Stress test:** In a rough scenario, a loss around ${mc_f:,.0f} is plausible — "
                f"plan for that before you buy."
            )
    if not notes:
        return ""
    return "\n\n".join(notes)


def _verdict_narrative(final_score: float, size_summary: str | None) -> str:
    base = (
        f"**Bottom line ({final_score:.0f}/100):** "
        f"We mixed price, stock trend, headlines, and market conditions into one score. "
    )
    if final_score >= 85:
        verdict = "Strong setup — one of the better ideas in this scan."
    elif final_score >= 70:
        verdict = "Solid setup — reasonable idea if it fits your budget and risk comfort."
    elif final_score >= 50:
        verdict = "Mixed bag — okay on paper, but trend or market conditions are working against you. Consider a smaller size or skip."
    else:
        verdict = "Weak setup — we would skip this or paper-trade it only to learn, not to chase profit."

    if size_summary:
        verdict += f" {size_summary}"
    return base + verdict


def build_quick_list_tooltip(data: dict[str, Any] | pd.Series) -> str:
    """Short hover text for quick lists — no trading jargon."""
    if isinstance(data, pd.Series):
        data = data.to_dict()

    bits: list[str] = []
    score = data.get("display_confidence") or data.get("conviction_score") or data.get("scalper_score")
    if score is not None and not (isinstance(score, float) and pd.isna(score)):
        bits.append(f"Score {float(score):.0f}/100.")

    ev = data.get("ev")
    if ev is not None and not (isinstance(ev, float) and pd.isna(ev)):
        ev_f = float(ev)
        if ev_f >= 0:
            bits.append(f"On average our model thinks you could come out ahead by about ${ev_f:,.0f} per contract.")
        else:
            bits.append(
                f"On average our model thinks you may overpay by about ${abs(ev_f):,.0f} per contract."
            )

    regime = data.get("garch_regime")
    if regime == "compress":
        bits.append("We expect quieter days ahead.")
    elif regime == "expand":
        bits.append("We expect choppier days ahead.")

    if data.get("ex_div_crossing") or data.get("ex_div_note"):
        bits.append("A dividend date falls before expiry — extra caution.")

    mc = data.get("mc_p95_loss")
    if mc is not None and not (isinstance(mc, float) and pd.isna(mc)):
        bits.append(f"In a bad scenario, plan for up to ${float(mc):,.0f} loss.")

    tag = str(data.get("tag") or "")
    if tag.startswith("0dte"):
        bits.append("Same-day trade — ranked on volume and movement, not long-term outlook.")

    if not bits:
        return "Tap 'Why this pick?' below for the full plain-English breakdown."
    return " ".join(bits)


def generate_plain_english_rationale(
    row: pd.Series | dict[str, Any],
    sentiment: dict[str, float],
    profile: StockProfile | None = None,
    *,
    vix_hint: float | None = None,
) -> str:
    """Build a readable explanation of why this pick scored as it did."""
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

    if dte == 0:
        time_line = "**What you are buying:** A bet that the stock moves up **today** before the market closes."
    elif dte == 1:
        time_line = "**What you are buying:** A bet that the stock moves up **by tomorrow**."
    else:
        time_line = (
            f"**What you are buying:** A bet that **{ticker}** rises toward **${strike:g}** "
            f"within the next **{dte} days**. If it does not move enough in time, the option can expire worthless."
        )

    parts = [
        time_line,
        f"**Price check:** {_edge_narrative(edge_pct, ask, bs_fair)}",
        _health_narrative(profile, profile_score),
        _sentiment_narrative(compound),
        _weather_narrative(macro_mult, vix_hint),
    ]
    gates = _gates_narrative(data)
    if gates:
        parts.append(gates)
    parts.append(_verdict_narrative(final_score, size_summary))
    return "\n\n".join(parts)
