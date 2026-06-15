"""Beginner-friendly labels and tooltip copy for the entire GUI."""

from __future__ import annotations

APP_TITLE = "Smart Trade Idea Scanner"
APP_SUBTITLE = (
    "This tool finds mathematical discounts in the stock market. It scans options contracts, "
    "checks company health, reads market fear levels, and ranks the best opportunities for you. "
    "No brokerage login required."
)

DISCLAIMER_FRIENDLY = (
    "Research and education only — not financial advice. "
    "Options are risky: you can lose 100% of what you pay for a contract. "
    "Never risk money you need for bills."
)

# --- Sidebar ---
SIDEBAR_SETUP = "Your Trade Setup"
SIDEBAR_RISK = "Risk Manager & Budget Calculator"

HELP_TICKERS = (
    "Enter the stock symbols of companies you want to investigate today "
    "(for example AAPL for Apple)."
)
HELP_CUSTOM_TICKER = "Type one extra symbol and it will be added to today's scan."
HELP_MAX_COST = (
    "The absolute most you are willing to spend (and risk losing) on a single contract. "
    "Why it matters: options can go to zero. This cap keeps one bad idea from draining your account."
)
HELP_DTE = (
    "How many days until the contract expires — your countdown timer. "
    "Why it matters: options are like melting ice cubes. Short time limits are cheaper but "
    "lose value fast if the stock doesn't move. Set the left handle to 0 for same-day trades "
    "(scored separately as quick scalps)."
)
HELP_RISK_PROFILE = (
    "How aggressive the strike selection should be. Careful picks safer, farther-from-price strikes. "
    "Bold picks closer strikes that need a bigger move but pay off more."
)
HELP_SKIP_EARNINGS = (
    "Companies report profits four times a year. Those days act like coin flips and can cause "
    "wild, unpredictable price swings. Checking this keeps you out of that casino."
)
HELP_TOP_IDEAS = "How many different trade ideas you want to see for each company."
HELP_SIZING_TOGGLE = (
    "Automatically calculates how many contracts to buy based on your account size and confidence score. "
    "Why it matters: pros rarely risk more than 1–2% per idea so a losing streak doesn't wipe them out."
)
HELP_BANKROLL = (
    "Your total trading account balance. Used only to calculate recommended position sizes — "
    "this app never connects to your broker."
)
HELP_BASE_RISK = (
    "Baseline percent of your account you're willing to risk on one trade (usually 1–2%). "
    "High confidence (85+): 1.25× this amount · Solid (70–84): 1.0× · "
    "Mediocre (50–69): 0.5× · Below 50: skip."
)

# --- Macro ---
MACRO_TITLE = "Overall Market Weather"
MACRO_INTRO = (
    "Roughly 75% of stocks follow the broader market. If the overall market is falling, "
    "it acts like gravity on even great companies. We check the weather before putting boats in the water."
)
HELP_VIX = (
    "The market's fear gauge. Under 18 = calm seas. 18–25 = choppy. Over 25 = panic — "
    "we block new swing-call picks because stocks swing too wildly."
)
HELP_SPY = (
    "Tracks the S&P 500 — a snapshot of overall US stock market health."
)
HELP_SPY_SMA = (
    "The market's average price over the last 20 days. "
    "Why it matters: when price is below this line, the short-term trend is down and "
    "even good stocks get dragged lower."
)
HELP_MACRO_MULT = (
    "Safety haircut applied to every confidence score when conditions are rough. "
    "Example: 0.70 means all scores are reduced 30% to protect your capital."
)

# --- Stock profile ---
STOCK_HEALTH_TITLE = "Company Health Check"
STOCK_HEALTH_INTRO = (
    "Cheap doesn't always mean good — falling stocks can keep falling. "
    "We grade recent momentum so buyers are stepping in before you risk money."
)
HELP_TREND_SCORE = (
    "0–100 grade for how healthy the stock's price trend is. "
    "80+ = strong upward momentum · 50–79 = mixed · under 50 = struggling."
)
HELP_RSI = (
    "Rubber-band effect. Under 30 = sold too hard, might bounce. "
    "Over 70 = running hot, might need a rest. 30–70 = neutral."
)
HELP_VS_SPY = (
    "How this stock is performing vs. the whole market over the last 20 days. "
    "Positive = outperforming · negative = lagging."
)
HELP_BETA = (
    "Price swing risk. If the market drops 1%, how much might this stock drop? "
    "1.0 ≈ moves with market · above 1 = wilder · below 1 = steadier."
)
HELP_HV = "How wildly this stock's price has swung recently (30/60/90 day windows)."
HELP_SMA_STACK = (
    "Short / medium / long trend arrows. All up = healthy uptrend. "
    "Mixed or all down = trend is fighting you."
)
HELP_MACD = "Who's winning right now — buyers (bullish) or sellers (bearish)."
HELP_ROC = "Recent report card: percent gain or loss over the last 20 and 60 days."
HELP_52W = "Where today's price sits inside the last year's high–low range (0% = at lows, 100% = at highs)."
HELP_DRAWDOWN = "How far the stock has fallen from its recent peak."
HELP_VOLUME = "Today's trading volume compared to the 20-day average. Spikes often mean big moves."

# --- Results ---
HELP_CONVICTION = (
    "Final confidence rating (0–100) blending four pillars: "
    "(1) Math discount — is the contract cheap vs. fair value? "
    "(2) Stock health — is momentum on your side? "
    "(3) News hype — are headlines positive or negative? "
    "(4) Market weather — is the broad market helping or hurting? "
    "85+ = all pillars align · 50–69 = mixed · below 50 = skip or tiny size."
)

# --- Sandbox ---
SANDBOX_TITLE = "Risk Manager & Budget Calculator"
SANDBOX_CAPTION = (
    "Practice your risk settings before scanning. Same math the scanner uses — "
    "slide confidence and premium to see how many contracts the system recommends."
)
HELP_SANDBOX_CONVICTION = HELP_CONVICTION
HELP_SANDBOX_ASK = (
    "The price tag on one contract (per share). Multiply by 100 for total cost "
    "(e.g. $2.50 ask = $250 per contract)."
)
