"""Application constants and scoring weights."""

DATA_SOURCE = "Yahoo Finance (yfinance) — v2.4"

DEFAULT_TICKERS = ["AAPL", "IWM", "QQQ", "XLF"]

MIN_BUDGET = 50
DEFAULT_BUDGET = 500
MAX_BUDGET = 5000

DEFAULT_MIN_DTE = 14
DEFAULT_MAX_DTE = 45
MIN_DTE_LIMIT = 0  # 0 = include same-day (0DTE) scalper picks
CONVICTION_MIN_DTE = 7  # conviction scoring floor when 0 is selected on slider
MAX_DTE_LIMIT = 60

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

CACHE_TTL_SECONDS = 300

DISCLAIMER = (
    "Research tool only — not financial advice. "
    "Options involve substantial risk; max loss on a long call is the premium paid."
)
