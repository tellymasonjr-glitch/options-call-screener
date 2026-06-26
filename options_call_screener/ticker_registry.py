"""Ticker universe with tier ranking for dropdown sort order (best setups first)."""

from __future__ import annotations

# tier: 1 = best paper-trade liquidity, 5 = leveraged/speculative, 9 = benchmarks

TICKER_REGISTRY: dict[str, dict[str, str | int]] = {
    # Tier 1 — paper-trade core (cheap, liquid options)
    "F": {"tier": 1, "name": "Ford", "group": "Paper-trade core"},
    "SOFI": {"tier": 1, "name": "SoFi", "group": "Paper-trade core"},
    "HOOD": {"tier": 1, "name": "Robinhood", "group": "Paper-trade core"},
    "CCL": {"tier": 1, "name": "Carnival", "group": "Paper-trade core"},
    "SNAP": {"tier": 1, "name": "Snap", "group": "Paper-trade core"},
    "AAL": {"tier": 1, "name": "American Airlines", "group": "Paper-trade core"},
    "PFE": {"tier": 1, "name": "Pfizer", "group": "Paper-trade core"},
    # Tier 2 — solid liquid names (recommended adds)
    "AMD": {"tier": 2, "name": "AMD", "group": "Tech — liquid"},
    "MRVL": {"tier": 2, "name": "Marvell", "group": "Tech — liquid"},
    "HPE": {"tier": 2, "name": "HP Enterprise", "group": "Tech — value"},
    "INTC": {"tier": 2, "name": "Intel", "group": "Tech — value"},
    "KR": {"tier": 2, "name": "Kroger", "group": "Defensive retail"},
    "MU": {"tier": 2, "name": "Micron", "group": "Tech — recommended"},
    "ON": {"tier": 2, "name": "ON Semi", "group": "Tech — recommended"},
    # Tier 3 — higher volatility / thin options
    "MARA": {"tier": 3, "name": "Marathon Digital", "group": "High volatility"},
    "WBD": {"tier": 3, "name": "Warner Bros Discovery", "group": "Beat-down turnaround"},
    "LFVN": {"tier": 3, "name": "LifeVantage", "group": "Small cap — thin options"},
    "XNDU": {"tier": 3, "name": "Xanadu Quantum", "group": "Small cap — verify ticker"},
    # Tier 5 — leveraged (use small size)
    "SOXL": {"tier": 5, "name": "SOXL 3x Semis", "group": "Leveraged ETF — high risk"},
    # Tier 8 — large-cap (pricier contracts)
    "AAPL": {"tier": 8, "name": "Apple", "group": "Large cap"},
    "MSFT": {"tier": 8, "name": "Microsoft", "group": "Large cap"},
    "AMZN": {"tier": 8, "name": "Amazon", "group": "Large cap"},
    "NVDA": {"tier": 8, "name": "NVIDIA", "group": "Large cap"},
    "TSLA": {"tier": 8, "name": "Tesla", "group": "Large cap"},
    # Tier 9 — index ETFs (macro context)
    "SPY": {"tier": 9, "name": "S&P 500 ETF", "group": "Index / macro"},
    "QQQ": {"tier": 9, "name": "Nasdaq ETF", "group": "Index / macro"},
    "IWM": {"tier": 9, "name": "Small-cap ETF", "group": "Index / macro"},
    "XLF": {"tier": 9, "name": "Financials ETF", "group": "Index / macro"},
    # Institutional / high-conviction (formerly M.A.S.K. picks)
    "IBM": {"tier": 2, "name": "IBM", "group": "Institutional Giants"},
    "INTU": {"tier": 2, "name": "Intuit", "group": "Institutional Giants"},
    "BSX": {"tier": 2, "name": "Boston Scientific", "group": "Institutional Giants"},
    "CRM": {"tier": 2, "name": "Salesforce", "group": "Institutional Giants"},
    "CEG": {"tier": 2, "name": "Constellation Energy", "group": "Institutional Giants"},
    "QURE": {"tier": 3, "name": "uniQure", "group": "High-risk wildcard"},
}


def ticker_label(symbol: str) -> str:
    meta = TICKER_REGISTRY.get(symbol.upper())
    if not meta:
        return symbol.upper()
    return f"{symbol.upper()} — {meta['name']} ({meta['group']})"


def sorted_ticker_options() -> list[str]:
    return sorted(
        TICKER_REGISTRY.keys(),
        key=lambda s: (int(TICKER_REGISTRY[s]["tier"]), s),
    )


LOW_BUDGET_TICKERS = [s for s in sorted_ticker_options() if TICKER_REGISTRY[s]["tier"] == 1]
DEFAULT_TICKERS = LOW_BUDGET_TICKERS[:5]
TICKER_OPTIONS = sorted_ticker_options()
