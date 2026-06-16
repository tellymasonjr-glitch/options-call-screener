"""Friendly column labels and tooltips for results tables."""

from __future__ import annotations

import streamlit as st

from ui.copy import HELP_CONVICTION

CONVICTION_COLUMN_CONFIG = {
    "tag": st.column_config.TextColumn(
        "Label",
        help="Why this row stands out (top pick, best value, budget-friendly, etc.).",
    ),
    "expiration": st.column_config.TextColumn("Expiry Date", help="Last day you can hold this contract."),
    "strike": st.column_config.NumberColumn(
        "Target Price",
        format="%.2f",
        help="You're betting the stock goes above this price before expiry.",
    ),
    "ask": st.column_config.NumberColumn(
        "Contract Price",
        format="$%.2f",
        help="Price tag per share. Multiply by 100 for total cost per contract.",
    ),
    "total_cost": st.column_config.NumberColumn(
        "Total Cost ($)",
        format="$%.0f",
        help="What one contract costs (price × 100 shares).",
    ),
    "dte": st.column_config.NumberColumn(
        "Days Left",
        help="Countdown until expiry. Options lose value faster as this hits zero.",
    ),
    "prob_itm": st.column_config.TextColumn(
        "Win Probability",
        help="Math estimate that the stock finishes above the target price. Not a guarantee.",
    ),
    "delta": st.column_config.NumberColumn(
        "Price Sensitivity",
        format="%.2f",
        help="Roughly how much the option price moves when the stock moves $1.",
    ),
    "bs_fair_hv": st.column_config.NumberColumn(
        "Fair Value (Math)",
        format="$%.2f",
        help="What our model says this contract should cost based on normal stock swings.",
    ),
    "edge_pct": st.column_config.TextColumn(
        "Your Discount",
        help="Gap between fair value and price tag. Positive = buying on sale.",
    ),
    "iv_hv_ratio": st.column_config.NumberColumn(
        "Hype vs Normal",
        format="%.2f",
        help="Above 1 = options are pricier than usual (market expects a big move).",
    ),
    "iv_rank": st.column_config.NumberColumn(
        "Volatility Rank",
        format="%.0f",
        help="Where today's option prices sit vs. the last year (0 = cheap, 100 = expensive).",
    ),
    "ev": st.column_config.NumberColumn(
        "Expected Return ($)",
        format="$%.0f",
        help=(
            "Average profit or loss in dollars for one contract at expiry, from the pricing model. "
            "Positive = you are buying below fair value; negative = overpaying vs. normal volatility."
        ),
    ),
    "risk_reward": st.column_config.NumberColumn(
        "Reward vs Risk",
        format="%.2f",
        help="Upside potential compared to premium paid. Higher is better.",
    ),
    "breakeven": st.column_config.NumberColumn(
        "Breakeven Stock Price",
        format="$%.2f",
        help="Stock price needed at expiry for you to break even on this trade.",
    ),
    "open_interest": st.column_config.NumberColumn(
        "Open Interest",
        help="How many contracts exist — higher usually means easier to buy/sell.",
    ),
    "volume": st.column_config.NumberColumn(
        "Today's Volume",
        help="Contracts traded today — shows how active this option is.",
    ),
    "spread_pct": st.column_config.TextColumn(
        "Bid-Ask Spread",
        help="Gap between buy and sell price. Wide spreads = harder to exit cleanly.",
    ),
    "conviction_score": st.column_config.NumberColumn(
        "Confidence Score",
        format="%.1f",
        help=HELP_CONVICTION,
    ),
    "size_tier": st.column_config.TextColumn(
        "Size Tier",
        help="High / solid / cautious based on confidence score.",
    ),
    "size_contracts": st.column_config.NumberColumn(
        "Contracts",
        help="Recommended number of contracts for your bankroll and risk settings.",
    ),
    "size_total_cost": st.column_config.NumberColumn(
        "Total Deployed ($)",
        format="$%.0f",
        help="Dollars at risk if you buy the recommended number of contracts.",
    ),
    "size_risk_pct": st.column_config.NumberColumn(
        "Risk % of Account",
        format="%.2f%%",
        help="Target percent of your bankroll this trade uses.",
    ),
}

SCALPER_COLUMN_CONFIG = {
    "tag": st.column_config.TextColumn("Label"),
    "expiration": st.column_config.TextColumn("Expiry Date"),
    "strike": st.column_config.NumberColumn("Target Price", format="%.2f"),
    "ask": st.column_config.NumberColumn("Contract Price", format="$%.2f"),
    "total_cost": st.column_config.NumberColumn("Total Cost ($)", format="$%.0f"),
    "dte": st.column_config.NumberColumn("Days Left"),
    "delta": st.column_config.NumberColumn("Price Sensitivity", format="%.2f"),
    "gamma": st.column_config.NumberColumn(
        "Gamma",
        help="How quickly price sensitivity changes — matters for same-day scalps.",
    ),
    "volume": st.column_config.NumberColumn("Today's Volume"),
    "open_interest": st.column_config.NumberColumn("Open Interest"),
    "spread_pct": st.column_config.TextColumn("Bid-Ask Spread"),
    "iv_hv_ratio": st.column_config.NumberColumn("Hype vs Normal", format="%.2f"),
    "scalper_score": st.column_config.NumberColumn(
        "Scalp Score",
        format="%.1f",
        help="Quick same-day score based on volume and movement — not long-term confidence.",
    ),
}
