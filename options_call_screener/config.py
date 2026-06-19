"""Application constants and scoring weights."""

DATA_SOURCE = "Yahoo Finance (yfinance) — v2.4"

from ticker_registry import (  # noqa: E402
    DEFAULT_TICKERS,
    LOW_BUDGET_TICKERS,
    TICKER_OPTIONS,
    ticker_label,
)

MIN_BUDGET = 50
DEFAULT_BUDGET = 500
MAX_BUDGET = 5000

DEFAULT_MIN_DTE = 14
DEFAULT_MAX_DTE = 45
MIN_DTE_LIMIT = 0  # 0 = include same-day (0DTE) scalper picks
CONVICTION_MIN_DTE = 7  # conviction scoring floor when 0 is selected on slider
MAX_DTE_LIMIT = 90

# 0 DTE scalper mode — separate from conviction pipeline
MIN_OPEN_INTEREST_0DTE = 20
MIN_VOLUME_0DTE = 50
MAX_SPREAD_PCT_0DTE = 0.28
DELTA_BOUNDS_0DTE = (0.20, 0.75)

SCALPER_WEIGHTS = {
    "volume": 0.35,
    "iv_spike": 0.25,
    "gamma": 0.20,
    "liquidity": 0.10,
    "atm_proximity": 0.10,
}

DEFAULT_PICKS_PER_TICKER = 3
MAX_PICKS_PER_TICKER = 5

MIN_OPEN_INTEREST = 50
MIN_VOLUME = 10
MAX_SPREAD_PCT = 0.15
MAX_IV_RANK_HARD = 70

SENTIMENT_BULLISH = 0.15
SENTIMENT_BEARISH = -0.15
SENTIMENT_MULT_BULLISH = 1.15
SENTIMENT_MULT_BEARISH = 0.60
SENTIMENT_MULT_NEUTRAL = 1.0

EARNINGS_AVOID_DAYS = 3
EARNINGS_HARD_BLOCK = True

# Ghost Tax — bid/ask slippage
HIGH_SPREAD_WARNING_PCT = 0.08
SPREAD_CONFIDENCE_HALVE_PCT = 0.10

# Echo Chamber — sector diversification in batch scans
SECTOR_PENALTY_MULT = 0.92

# Tide Check — 200-day SMA macro filter
SMA200_CONFIDENCE_MULT = 0.85
SMA200_KELLY_MULT = 0.75

# Emergency brake — cumulative open-trade P95 exposure
ACCOUNT_RISK_LOCK_PCT = 0.10
JOURNAL_FILENAME = "my_trades.csv"

# Mirror Check — beta-weighted SPY exposure warning
SPY_EXPOSURE_WARN_SHARES = 100

# GARCH(1,1) forward vol forecast (v5.0)
GARCH_FORECAST_HORIZON = 5
GARCH_MIN_OBS = 120
GARCH_HV_BLEND = 0.50
GARCH_EXPAND_RATIO = 1.08
GARCH_COMPRESS_RATIO = 0.92
GARCH_COMPRESS_CONFIDENCE_MULT = 0.94

# Macro environment (VIX + SPY trend) — conviction scoring only
VIX_CALM_MAX = 18
VIX_ELEVATED_MAX = 25
SPY_TREND_MULT = 0.7

# Position sizing (v3.3) — conviction-scaled fractional risk
DEFAULT_BANKROLL = 10_000
MIN_BANKROLL = 1_000
MAX_BANKROLL = 1_000_000
DEFAULT_BASE_RISK_PCT = 1.5
MIN_BASE_RISK_PCT = 0.5
MAX_BASE_RISK_PCT = 5.0
CONVICTION_TIER1_MIN = 85
CONVICTION_TIER1_MULT = 1.25
CONVICTION_TIER2_MIN = 70
CONVICTION_TIER2_MULT = 1.0
CONVICTION_TIER3_MIN = 50
CONVICTION_TIER3_MULT = 0.5

# Fractional Kelly — doc recommends quarter-Kelly with 1–3% per-trade cap
KELLY_FRACTION = 0.25
MAX_KELLY_RISK_PCT = 3.0

# Empirical Kelly — journal-driven sizing cap (v5.3)
EMPIRICAL_KELLY_LOOKBACK = 30
EMPIRICAL_KELLY_MIN_TRADES = 5

# Portfolio stress grid (Module 2)
STRESS_SPOT_SHOCKS = [-0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15]
STRESS_VOL_SHOCKS = [-0.20, 0.0, 0.20]
EPR_LOSS_PCT = 0.05

# Monte Carlo sizing gate (Module 4)
MC_SIMULATIONS = 1200
MC_MAX_DRAWDOWN_PCT = 0.05

SCORE_WEIGHTS = {
    "ev_hv": 0.24,          # BS fair value at blended HV minus premium
    "prob_itm": 0.14,       # N(d2)
    "vol_value": 0.13,      # IV rank + IV/HV
    "liquidity": 0.10,
    "stock_profile": 0.20,  # trend, momentum, 52w, RS vs SPY, volume
    "sentiment": 0.07,
    "efficiency": 0.05,
    "theta": 0.07,
}

DELTA_BOUNDS = {
    "conservative": (0.30, 0.45),
    "moderate": (0.25, 0.55),
    "aggressive": (0.20, 0.65),
}

CACHE_TTL_SECONDS = 600  # 10 min — reuse quotes between scans on Streamlit Cloud
SCAN_TICKER_DELAY_SEC = 0.6  # pause between tickers to avoid Yahoo burst limits
SCAN_WARN_TICKERS = 6  # sidebar heads-up above this count

DISCLAIMER = (
    "Research tool only — not financial advice. "
    "Options involve substantial risk; max loss on a long call is the premium paid."
)
