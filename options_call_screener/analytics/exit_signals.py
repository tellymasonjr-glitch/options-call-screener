"""Plain-English exit signals for open call positions (paper-trade helper)."""

from __future__ import annotations


def check_exit_signals(
    profit_pct: float,
    rsi: float,
    dte: int,
    current_price: float,
    strike: float,
    contracts: int = 1,
) -> list[str]:
    """Evaluate an open trade and return plain-English exit warnings."""
    signals: list[str] = []

    if profit_pct >= 100:
        if contracts >= 2:
            signals.append(
                "**+100% profit — house money rule:** You doubled your money. "
                "Sell **half** your contracts to recover your original cost. "
                "What's left is house money — you can't lose your own capital on those."
            )
        else:
            signals.append(
                "**+100% profit:** You doubled your money on a single contract. "
                "Strong exit zone — consider selling all or most of the position."
            )
    elif profit_pct >= 50:
        signals.append(
            "**+50% profit:** Solid gain. Consider mentally moving your stop to "
            "break-even (entry price) so this trade can't turn red from here."
        )

    if rsi >= 70:
        signals.append(
            "**Momentum exhaustion (RSI over 70):** The stock is running hot — "
            "the rubber band is stretched. Momentum often pauses or reverses here. "
            "Good time to secure profits if you're already up."
        )
    elif rsi <= 30 and profit_pct > 0:
        signals.append(
            "**Oversold (RSI under 30):** Stock was beaten down — your call may still "
            "have room, but watch for a bounce fading if profit is already large."
        )

    if dte <= 0:
        signals.append(
            "**Expires today:** Same-day expiry — time decay is extreme. "
            "Take profits or exit now unless you have a deliberate scalp plan."
        )
    elif dte <= 2:
        signals.append(
            f"**Time decay warning ({dte} day(s) left):** The clock is almost out. "
            "Options lose value fast near expiry — a flat stock can wipe gains overnight."
        )
    elif dte <= 7 and profit_pct >= 30:
        signals.append(
            f"**One week or less ({dte} days):** With a healthy profit already on the table, "
            "decide if the remaining upside is worth the melting-ice-cube risk."
        )

    if strike > 0 and current_price >= strike * 0.995:
        signals.append(
            f"**Target zone:** Stock is at or above your ${strike:g} strike (${current_price:.2f} now). "
            "Premiums often swell near round-number targets — a textbook zone to cash out."
        )
    elif strike > 0 and current_price >= strike * 0.97:
        signals.append(
            f"**Approaching target:** Stock is within ~3% of your ${strike:g} strike. "
            "Watch for premium expansion as it nears psychological resistance."
        )

    return signals


def format_exit_report(
    signals: list[str],
    *,
    ticker: str,
    profit_pct: float,
    rsi: float,
    dte: int,
) -> str:
    header = (
        f"**{ticker} exit check** — profit **{profit_pct:+.0f}%**, "
        f"momentum (RSI) **{rsi:.0f}**, **{dte} days** until expiry.\n\n"
    )
    if not signals:
        return (
            header
            + "No critical exit signals right now. Let the trend work, "
            "but keep watching market weather and your paper-trade log."
        )
    return header + "\n\n".join(f"- {s}" for s in signals)
