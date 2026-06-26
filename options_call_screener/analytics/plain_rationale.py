"""Plain-English trade explanations — written for people new to options."""

from __future__ import annotations

from typing import Any

import pandas as pd

from analytics.stock_profile import StockProfile


def _what_you_are_buying(
    ticker: str,
    strike: float,
    dte: int,
    ask: float,
    spot: float | None = None,
) -> str:
    cost = ask * 100
    spot_line = ""
    if spot is not None and spot > 0:
        gap = strike - spot
        if gap > 0:
            spot_line = (
                f" The stock is at **${spot:.2f}** today, so it would need to rise about "
                f"**${gap:.2f}** just to reach the strike — and usually a bit more than that "
                f"for the option to be worth what you paid."
            )
        else:
            spot_line = (
                f" The stock is already at **${spot:.2f}**, which is at or above the "
                f"**${strike:g}** strike — a good start, but the option still needs to stay "
                f"valuable through expiry."
            )

    if dte == 0:
        time_part = (
            "This is a **same-day** bet: the stock must move in your favor **before the market "
            "closes today**. There is no tomorrow to recover if the move does not happen."
        )
    elif dte == 1:
        time_part = (
            "This is a **very short-term** bet: you need a meaningful move **by tomorrow**. "
            "One quiet day can erase most of the value."
        )
    else:
        time_part = (
            f"You have **{dte} days** for **{ticker}** to move toward **${strike:g}**. "
            f"Options lose value as time passes — even if the stock goes sideways — so the "
            f"clock is working against you."
        )

    return (
        f"**What you are buying:** A **call option** on **{ticker}** at the **${strike:g}** "
        f"strike. You are paying **${ask:.2f} per share** (${cost:,.0f} per contract, since "
        f"each contract covers 100 shares). You profit if the stock rises enough **before "
        f"expiry** to cover what you paid; if it does not, you can lose the entire amount."
        f"{spot_line} {time_part}"
    )


def _edge_narrative(edge_pct: float, ask: float, bs_fair: float) -> str:
    pct = edge_pct * 100
    savings = max(bs_fair - ask, 0) * 100

    if edge_pct >= 0.10:
        return (
            f"We estimate this option *should* cost about **${bs_fair:.2f}** based on how "
            f"this stock has moved in the past and how much time is left. The market is asking "
            f"**${ask:.2f}** — roughly **{pct:.0f}% below** our estimate, or about "
            f"**${savings:,.0f} less per contract** than we think is fair. "
            f"That does not guarantee a win (the stock still has to move), but you are starting "
            f"from a better price — like buying something on sale rather than at full retail."
        )
    if edge_pct >= 0:
        return (
            f"Our fair-value estimate is **${bs_fair:.2f}** and the market wants **${ask:.2f}** "
            f"(about **{pct:.0f}% edge**). The price is **reasonable**, not a deep discount. "
            f"In this zone, the stock's direction, headlines, and overall market mood matter "
            f"more — a fair price alone is not enough; you need the setup to actually play out."
        )
    overpay = (ask - bs_fair) * 100
    return (
        f"The market is asking **${ask:.2f}**, but our model says fair value is only "
        f"**${bs_fair:.2f}** — roughly **{abs(pct):.0f}% above** what the math supports, "
        f"or about **${overpay:,.0f} more per contract** than we would like to pay. "
        f"You can still win if the stock surges, but you are starting behind: you need a "
        f"bigger move just to break even on an already-expensive ticket."
    )


def _expected_return_narrative(ev: float | None) -> str:
    if ev is None or (isinstance(ev, float) and pd.isna(ev)):
        return ""
    ev_f = float(ev)
    if ev_f >= 50:
        return (
            f"**Expected payoff (model):** If you repeated this exact setup many times, our "
            f"model suggests you would come out ahead by about **${ev_f:,.0f} per contract** "
            f"on average — before fees and slippage. That is one of the stronger math profiles "
            f"in this scan."
        )
    if ev_f >= 0:
        return (
            f"**Expected payoff (model):** On average, our model puts you slightly ahead by "
            f"about **${ev_f:,.0f} per contract** — a modest edge, not a home run. Treat this "
            f"as a small advantage that still depends on the stock cooperating."
        )
    return (
        f"**Expected payoff (model):** On average, our model suggests you may be **overpaying "
        f"by about ${abs(ev_f):,.0f} per contract** relative to fair value. The pick can "
        f"still work if momentum or news is strong, but the starting math is not in your favor."
    )


def _health_narrative(profile: StockProfile | None, profile_score: float) -> str:
    if profile is None:
        if profile_score >= 65:
            return (
                f"**How the stock is doing ({profile_score:.0f}/100):** Recent price action "
                f"looks supportive — buyers seem to be holding the line. We have limited detail "
                f"on this ticker, so lean more on the price check and overall market sections "
                f"below than on trend alone."
            )
        return (
            f"**How the stock is doing ({profile_score:.0f}/100):** We do not have a rich trend "
            f"picture here. Direction is uncertain, so this pick lives or dies mostly on whether "
            f"the option price is a good deal and whether the broad market is calm."
        )

    if profile.above_sma_20 and profile.above_sma_50:
        trend = (
            "Price is **above its recent averages** (roughly the last month and two months). "
            "That usually means the stock is in an **uptrend** — each dip has been bought rather "
            "than sold off hard."
        )
    elif not profile.above_sma_20 and not profile.above_sma_50:
        trend = (
            "Price is **below its recent averages**. The stock has been **drifting down** or "
            "stuck in a weak pattern — call options are harder to win when the chart looks like "
            "this unless you are betting on a sharp reversal."
        )
    else:
        trend = (
            "The trend is **mixed**: strong in one time frame, weak in another. That often means "
            "the stock is **chopping sideways** or changing character — direction is less clear."
        )

    mood = (
        "Recent sessions show **more buying than selling** — a tailwind for call options."
        if profile.macd_bullish
        else "Recent sessions show **sellers in control** — the stock has struggled to hold gains."
    )

    rsi_note = ""
    if profile.rsi_14 <= 30:
        rsi_note = (
            " The stock has **sold off heavily** lately. Sometimes that sets up a bounce, but "
            "sometimes the weakness continues — this is a turnaround bet, not a sure thing."
        )
    elif profile.rsi_14 >= 70:
        rsi_note = (
            " The stock has **run up a lot** recently. The easy part of the move may be done, "
            "and pullbacks become more likely from stretched levels."
        )

    rs_20 = profile.rel_strength_20
    if rs_20 >= 0.05:
        vs_market = (
            f"It has **outperformed the broad market** over the last ~20 days "
            f"(about {rs_20:+.0%} vs. the S&P), which is a positive sign for a bullish bet."
        )
    elif rs_20 <= -0.05:
        vs_market = (
            f"It has **lagged the broad market** over the last ~20 days "
            f"(about {rs_20:+.0%} vs. the S&P) — you are betting on a laggard to catch up."
        )
    else:
        vs_market = "It has moved **roughly in line with the broad market** recently."

    vol_note = ""
    if profile.volume_ratio >= 1.5:
        vol_note = " Trading volume is **well above normal**, which can mean bigger moves — good for upside, but also more whipsaw."
    elif profile.volume_ratio <= 0.7:
        vol_note = " Trading volume is **below normal**, which sometimes means moves lack follow-through."

    if profile_score >= 65:
        lead = f"**How the stock is doing ({profile_score:.0f}/100):** The chart looks **healthy** for a bullish bet."
    elif profile_score >= 45:
        lead = f"**How the stock is doing ({profile_score:.0f}/100):** **Average** — not a clear winner or loser on trend alone."
    else:
        lead = f"**How the stock is doing ({profile_score:.0f}/100):** **Weak** on trend — this is a higher-risk turnaround idea."

    return f"{lead} {trend} {mood}{rsi_note} {vs_market}{vol_note}"


def _sentiment_narrative(compound: float) -> str:
    if compound >= 0.15:
        return (
            "**Headlines:** Recent news skews **positive**. Good headlines can bring in new "
            "buyers, support the stock on dips, and help call options gain value even before "
            "a big price move shows up on the chart. This is a modest tailwind — not a guarantee."
        )
    if compound <= -0.15:
        return (
            "**Headlines:** Recent news skews **negative**. Bad headlines can override a "
            "good-looking option price — lawsuits, downgrades, missed targets, or sector fear "
            "can drop the stock fast. If you take this trade, know that **headline risk** is "
            "working against you."
        )
    return (
        "**Headlines:** Nothing strongly positive or negative in recent news. That means this "
        "trade will likely be decided by **price action and the overall market**, not by a "
        "headline catalyst. You are not getting a news tailwind, but you are not fighting "
        "obvious bad press either."
    )


def _weather_narrative(macro_mult: float, vix_hint: float | None = None) -> str:
    if macro_mult >= 1.0:
        vix_extra = ""
        if vix_hint is not None and vix_hint < 16:
            vix_extra = " Fear gauges are low, which often helps stocks grind higher."
        return (
            "**Overall market:** **Calm and supportive.** The broad market is steady, and "
            f"individual stocks tend to do better when the tide is rising.{vix_extra} "
            "We did not reduce your score for macro stress — conditions are favorable for "
            "taking reasonable risk."
        )
    penalty = int(round((1.0 - macro_mult) * 100))
    reasons: list[str] = []
    if vix_hint and vix_hint >= 22:
        reasons.append(
            f"investor fear is elevated (our fear gauge reads around {vix_hint:.0f})"
        )
    elif vix_hint and vix_hint >= 18:
        reasons.append("investors are somewhat nervous")
    if macro_mult < 0.85:
        reasons.append("the overall market has been sliding in the short term")
    reason_text = " and ".join(reasons) if reasons else "conditions are choppy and uncertain"
    return (
        f"**Overall market (caution):** {reason_text.capitalize()}. When the whole market "
        f"struggles, even good individual stocks often get dragged down. We **lowered your score "
        f"about {penalty}%** to reflect that headwind — not because this pick is automatically "
        f"bad, but because the environment is harder than usual."
    )


def _gates_narrative(data: dict[str, Any]) -> str:
    notes: list[str] = []
    ex = data.get("ex_div_note")
    if ex and str(ex).strip():
        notes.append(
            "**Dividend warning:** An **ex-dividend date** falls before this option expires. "
            "On that day, the stock price often **drops by roughly the dividend amount** — "
            "which can hurt call options even if nothing else changed. If you are new to options, "
            "treat this as an extra reason to size small or wait for a cleaner setup."
        )
    regime = data.get("garch_regime")
    if regime == "compress":
        notes.append(
            "**Volatility outlook (calmer days ahead):** We expect **quieter price swings** "
            "than recently. That sounds peaceful, but call buyers sometimes **overpay when "
            "fear was high** — if calm returns, option prices can **deflate** even if the stock "
            "barely moves. Make sure you are not paying for panic that may fade."
        )
    elif regime == "expand":
        notes.append(
            "**Volatility outlook (bumpier days ahead):** We expect **larger price swings** "
            "than recently. That cuts both ways: bigger moves can help calls pay off fast, but "
            "losses can also accelerate. This environment rewards disciplined sizing more than "
            "hero bets."
        )
    warnings = data.get("risk_warnings")
    seen: set[str] = set()
    if warnings and str(warnings).strip():
        for msg in str(warnings).split("|"):
            msg = msg.strip()
            if not msg:
                continue
            if ("IV Crush" in msg or "iv crush" in msg.lower()) and "earnings" not in seen:
                seen.add("earnings")
                notes.append(
                    "**Earnings nearby:** Options often carry extra \"event premium\" before "
                    "earnings. After the report, that premium can **vanish overnight** — even if "
                    "you guessed direction correctly. This is one of the most common ways new "
                    "option traders lose despite being \"right.\""
                )
            elif ("Vega" in msg or "vega" in msg.lower()) and "vega" not in seen:
                seen.add("vega")
                notes.append(
                    "**Rich option prices:** You may be paying a lot for **big-move insurance**. "
                    "If the stock moves only a little, that expensive premium can melt away and "
                    "leave you with a loss."
                )
            elif ("Gamma" in msg or "gamma" in msg.lower()) and "gamma" not in seen:
                seen.add("gamma")
                notes.append(
                    "**Very little time left:** With expiry close, **small stock moves cause "
                    "large swings** in option value — up or down. This is exciting but unforgiving; "
                    "mistakes are costly and there is little room to wait for a recovery."
                )
            elif ("Empty Room" in msg or "liquidity" in msg.lower()) and "liquidity" not in seen:
                seen.add("liquidity")
                notes.append(
                    "**Thin trading:** This contract does not trade heavily. The gap between "
                    "what sellers want and buyers offer can be wide, so **getting in or out at a "
                    "fair price is harder** — plan for slippage."
                )
    mc = data.get("mc_p95_loss")
    if mc is not None and not (isinstance(mc, float) and pd.isna(mc)):
        mc_f = float(mc)
        if data.get("mc_passes_cap") is False:
            notes.append(
                f"**Stress test (failed size cap):** We ran thousands of simulated paths for "
                f"this stock. In a **bad-but-realistic** outcome (roughly the worst 5% of cases), "
                f"you could lose about **${mc_f:,.0f}** — more than we want relative to your "
                f"account size. The risk manager would **cut suggested size** for this reason."
            )
        elif mc_f > 0:
            notes.append(
                f"**Stress test:** In a rough scenario (about the worst 5% of simulated paths), "
                f"a loss around **${mc_f:,.0f}** is plausible. That does not mean it will "
                f"happen — but you should be **emotionally and financially okay** with that "
                f"outcome before buying."
            )
    if not notes:
        return ""
    return "\n\n".join(notes)


def _verdict_narrative(final_score: float, size_summary: str | None) -> str:
    base = (
        f"**Bottom line ({final_score:.0f}/100):** We combined **four ideas** into one score: "
        f"(1) whether the option price looks like a good deal, (2) whether the stock chart "
        f"supports a bullish bet, (3) whether headlines help or hurt, and (4) whether the "
        f"overall market is calm or fighting you. "
    )
    if final_score >= 85:
        verdict = (
            "This is a **top-tier setup for this scan** — multiple pillars line up. That still "
            "does not mean certainty; it means the odds look better than average **if** you size "
            "appropriately and accept that any single trade can lose."
        )
    elif final_score >= 70:
        verdict = (
            "This is a **solid, reasonable idea** — good enough to consider if it fits your "
            "budget and risk comfort. Watch the caution flags above; none of them automatically "
            "veto the trade, but they tell you where the risks live."
        )
    elif final_score >= 50:
        verdict = (
            "This is a **mixed bag** — some factors okay, others working against you. Many "
            "experienced traders would **size down hard or skip**. If you take it, treat it as "
            "a learning trade with money you can afford to lose."
        )
    else:
        verdict = (
            "This **scores below our comfort zone**. We would **skip for real money** or "
            "paper-trade only to learn how the mechanics work — not to chase profit."
        )

    if size_summary:
        verdict += f"\n\n**Suggested sizing:** {size_summary}"
    return base + verdict


def build_quick_list_tooltip(data: dict[str, Any] | pd.Series) -> str:
    """Medium-length hover summary — plain English, more context than a one-liner."""
    if isinstance(data, pd.Series):
        data = data.to_dict()

    parts: list[str] = []
    ticker = str(data.get("ticker") or "This stock")
    score = data.get("display_confidence") or data.get("conviction_score") or data.get("scalper_score")
    if score is not None and not (isinstance(score, float) and pd.isna(score)):
        parts.append(f"Overall score **{float(score):.0f}/100** for this contract.")

    ask = data.get("ask")
    bs_fair = data.get("bs_fair_hv") or data.get("bs_fair_iv")
    edge = data.get("edge_pct")
    if ask is not None and bs_fair is not None and edge is not None:
        if not any(pd.isna(x) for x in (ask, bs_fair, edge)):
            edge_f = float(edge)
            if edge_f >= 0.05:
                parts.append(
                    f"Price looks **cheaper than our estimate** (${float(ask):.2f} ask vs "
                    f"~${float(bs_fair):.2f} fair value) — a helpful starting point."
                )
            elif edge_f >= 0:
                parts.append(
                    f"Price is **roughly fair** (${float(ask):.2f} vs ~${float(bs_fair):.2f} "
                    f"estimate) — the stock still needs to move your way."
                )
            else:
                parts.append(
                    f"Price may be **above fair value** (${float(ask):.2f} vs "
                    f"~${float(bs_fair):.2f}) — you need a stronger move to win."
                )

    ev = data.get("ev")
    if ev is not None and not (isinstance(ev, float) and pd.isna(ev)):
        ev_f = float(ev)
        if ev_f >= 0:
            parts.append(f"Model expected payoff about **+${ev_f:,.0f}/contract** on average.")
        else:
            parts.append(f"Model expected payoff about **−${abs(ev_f):,.0f}/contract** on average.")

    regime = data.get("garch_regime")
    if regime == "compress":
        parts.append("We expect **calmer** days ahead — watch for deflating option prices.")
    elif regime == "expand":
        parts.append("We expect **choppier** days ahead — bigger swings, higher risk.")

    macro = data.get("macro_multiplier")
    if macro is not None and not (isinstance(macro, float) and pd.isna(macro)) and float(macro) < 0.95:
        parts.append("**Market conditions** are cautious — broad market headwind applied.")

    if data.get("ex_div_crossing") or data.get("ex_div_note"):
        parts.append("**Dividend date** before expiry — extra caution on calls.")

    mc = data.get("mc_p95_loss")
    if mc is not None and not (isinstance(mc, float) and pd.isna(mc)):
        mc_f = float(mc)
        if data.get("mc_passes_cap") is False:
            parts.append(f"Stress test: bad-case loss ~**${mc_f:,.0f}** — size may be trimmed.")
        elif mc_f > 0:
            parts.append(f"Stress test: plan for up to ~**${mc_f:,.0f}** loss in a rough scenario.")

    tag = str(data.get("tag") or "")
    if tag.startswith("0dte"):
        parts.append(
            f"**Same-day** {ticker} idea — ranked on activity and movement, not long-term outlook."
        )

    if not parts:
        return "Open 'Why this pick?' below for the full plain-English breakdown."
    parts.append("Open 'Why this pick?' for the full story.")
    return " ".join(parts).replace("**", "")


def generate_plain_english_rationale(
    row: pd.Series | dict[str, Any],
    sentiment: dict[str, float],
    profile: StockProfile | None = None,
    *,
    vix_hint: float | None = None,
) -> str:
    """Build a readable, in-depth explanation of why this pick scored as it did."""
    if isinstance(row, pd.Series):
        data = row.to_dict()
    else:
        data = row

    ticker = data.get("ticker", "This stock")
    strike = float(data["strike"])
    dte = int(data["dte"])
    ask = float(data["ask"])
    spot = float(data["spot"]) if data.get("spot") is not None else (profile.spot if profile else None)
    bs_fair = float(data.get("bs_fair_hv") or data.get("bs_fair_iv") or ask)
    edge_pct = float(data.get("edge_pct", 0))
    final_score = float(data.get("conviction_score", 0))
    macro_mult = float(data.get("macro_multiplier", 1.0) or 1.0)
    profile_score = float(profile.profile_score) if profile else 50.0
    compound = sentiment.get("mean_compound", 0.0)
    size_summary = data.get("size_summary") or None
    ev = data.get("ev")
    ev_val = float(ev) if ev is not None and not (isinstance(ev, float) and pd.isna(ev)) else None

    parts = [
        _what_you_are_buying(ticker, strike, dte, ask, spot),
        f"**Price check:** {_edge_narrative(edge_pct, ask, bs_fair)}",
    ]
    ev_block = _expected_return_narrative(ev_val)
    if ev_block:
        parts.append(ev_block)
    parts.extend([
        _health_narrative(profile, profile_score),
        _sentiment_narrative(compound),
        _weather_narrative(macro_mult, vix_hint),
    ])
    gates = _gates_narrative(data)
    if gates:
        parts.append(gates)
    parts.append(_verdict_narrative(final_score, size_summary))
    return "\n\n".join(parts)
