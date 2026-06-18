"""Exit signal checker for open paper trades (stateless — you enter the position)."""

from __future__ import annotations

from datetime import date

import streamlit as st

from analytics.exit_signals import check_exit_signals, format_exit_report
from analytics.stock_profile import build_stock_profile
from data.cached_fetch import get_call_quote, get_price_history, get_spot_price
from data.market_data import dte_from_expiration
from data.yf_utils import is_rate_limit_error
from ui.copy import (
    HELP_EXIT_DTE,
    HELP_EXIT_PROFIT,
    HELP_EXIT_RSI,
    HELP_EXIT_SPOT,
)


def render_exit_checker(*, expanded: bool = False) -> None:
    with st.expander("Exit Check — Should I Sell?", expanded=expanded):
        st.caption(
            "Already in a paper trade? Enter your position details. "
            "We'll check profit, momentum (RSI), time left, and target price — "
            "same rules pros use (house money, time decay, resistance)."
        )

        c1, c2, c3 = st.columns(3)
        ticker = c1.text_input("Stock symbol", value="AAPL", key="exit_ticker").upper().strip()
        strike = c2.number_input(
            "Target / strike price ($)",
            min_value=0.01,
            value=295.0,
            step=0.5,
            key="exit_strike",
            help="The strike price on your call contract.",
        )
        exp_date = c3.date_input(
            "Expiration date",
            value=date.today(),
            key="exit_exp",
            help="When the contract expires — drives the time-decay warning.",
        )

        c4, c5, c6 = st.columns(3)
        entry_ask = c4.number_input(
            "Entry price ($ per share)",
            min_value=0.01,
            value=1.50,
            step=0.05,
            key="exit_entry",
            help="What you paid per share when you opened (the ask at entry).",
        )
        contracts = c5.number_input(
            "Contracts held",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            key="exit_contracts",
            help="Used for the house-money rule (sell half at +100% when 2+).",
        )
        use_manual_profit = c6.checkbox(
            "Enter profit % manually",
            value=False,
            key="exit_manual_profit",
            help="Use if Yahoo quote is stale; otherwise we fetch the current ask.",
        )

        manual_profit = 0.0
        if use_manual_profit:
            manual_profit = st.slider(
                "Current profit (%)",
                min_value=-100.0,
                max_value=500.0,
                value=0.0,
                step=5.0,
                key="exit_profit_slider",
            )

        if not st.button("Check exit signals", type="secondary", key="exit_check_btn"):
            return

        if not ticker:
            st.warning("Enter a stock symbol.")
            return

        expiration = exp_date.isoformat()
        try:
            spot = get_spot_price(ticker)
            history = get_price_history(ticker)
            profile = build_stock_profile(ticker, history)
            rsi = profile.rsi_14
            dte = dte_from_expiration(expiration)

            if use_manual_profit:
                profit_pct = manual_profit
                current_ask = entry_ask * (1 + profit_pct / 100.0)
            else:
                quote = get_call_quote(ticker, float(strike), expiration)
                current_ask = quote["ask"] or quote["last"]
                if entry_ask <= 0:
                    st.error("Entry price must be greater than zero.")
                    return
                profit_pct = ((current_ask - entry_ask) / entry_ask) * 100.0

            signals = check_exit_signals(
                profit_pct=profit_pct,
                rsi=rsi,
                dte=dte,
                current_price=spot,
                strike=float(strike),
                contracts=int(contracts),
            )
            report = format_exit_report(
                signals,
                ticker=ticker,
                profit_pct=profit_pct,
                rsi=rsi,
                dte=dte,
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Stock price", f"${spot:.2f}", help=HELP_EXIT_SPOT)
            m2.metric("Your profit", f"{profit_pct:+.0f}%", help=HELP_EXIT_PROFIT)
            m3.metric("Momentum (RSI)", f"{rsi:.0f}", help=HELP_EXIT_RSI)
            m4.metric("Days left", str(dte), help=HELP_EXIT_DTE)
            if not use_manual_profit:
                st.caption(f"Current contract ask: ${current_ask:.2f} (entry was ${entry_ask:.2f})")

            if signals:
                st.warning(report)
            else:
                st.success(report)

        except Exception as exc:
            if is_rate_limit_error(exc):
                st.error("Yahoo rate limit — wait 2–3 minutes and try again.")
            else:
                st.error(f"Could not check exit: {exc}")
