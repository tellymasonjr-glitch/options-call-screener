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

RATE_LIMIT_TITLE = "Yahoo Finance rate limit (temporary)"
RATE_LIMIT_BODY = (
    "Streamlit Cloud shares Yahoo's data pipe with many users. When you see "
    "**Too Many Requests**, nothing is broken with your tickers — Yahoo paused us for a few minutes.\n\n"
    "**What to do:**\n"
    "1. Wait **2–3 minutes** (do not hammer Scan).\n"
    "2. Scan **1–3 tickers** at a time (Budget Momentum batch: F, SOFI, SNAP).\n"
    "3. Tap **Clear cache & reload**, then scan again — successful runs cache for **10 minutes**.\n"
    "4. Large-cap names (AAPL, MSFT, IBM) need extra option-chain calls; start with cheaper tickers if limits persist.\n\n"
    "The *AAPL: No earnings dates found* log line is a harmless Yahoo quirk — AAPL is not delisted."
)

# --- Sidebar ---
SIDEBAR_SETUP = "Your Trade Setup"
SIDEBAR_RISK = "Risk Manager & Budget Calculator"

HELP_TICKERS = (
    "Pick stocks to scan. The low-budget preset (F, SOFI, HOOD, etc.) uses cheap, "
    "liquid options so position sizing can recommend 1–5 contracts. "
    "SPY/QQQ/IWM are useful for macro context but have pricier contracts. "
    "Why it matters: illiquid tickers fail the Empty Room filter — scanning liquid names "
    "keeps you out of contracts nobody can exit."
)
HELP_STOCK_PRESETS = (
    "Load a curated ticker playlist into Companies to Scan. Select multiple playlists "
    "to stack them (e.g. Institutional Giants + Index Macro). "
    "Why it matters: picks the pond you fish in — GARCH, Kelly, and all gates still decide each trade."
)
HELP_JOURNAL_BACKUP = (
    "Streamlit Cloud wipes local files on redeploy. Download your journal after every session "
    "so Empirical Kelly keeps your closed-trade history."
)
HELP_JOURNAL_RESTORE = (
    "Upload a previously downloaded my_trades.csv to restore journal state after a redeploy."
)
HELP_SCAN_SNAPSHOT = (
    "Save this JSON after each scan — top picks, GARCH by ticker, and SPY/QQQ/IWM context "
    "for later calibration (v5.6)."
)
HELP_CUSTOM_TICKER = (
    "Type one extra symbol and it will be added to today's scan. "
    "Why it matters: stick to names with active options volume so Ghost Tax and spread gates stay honest."
)
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
    "Bold picks closer strikes that need a bigger move but pay off more. "
    "Why it matters: closer strikes have higher Delta (more market exposure per dollar) — "
    "they move your Mirror Check and drawdown faster."
)
HELP_SKIP_EARNINGS = (
    "Companies report profits four times a year. Those days act like coin flips and can cause "
    "wild, unpredictable price swings. Checking this keeps you out of that casino."
)
HELP_TOP_IDEAS = (
    "How many different trade ideas you want to see for each company. "
    "Why it matters: more ideas gives options, but your best edge is usually in the top 1–2 — "
    "logging too many spreads focus and dilutes the Mirror Check."
)
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
    "we block new swing-call picks because stocks swing too wildly. "
    "Why it matters: when fear is elevated, option premiums are inflated and directional "
    "guesses get punished — pros reduce size or sit out."
)
HELP_SPY = (
    "Tracks the S&P 500 — a snapshot of overall US stock market health. "
    "Why it matters: roughly 75% of stocks follow the broad market. If SPY is weak, "
    "even a great single-stock setup fights gravity."
)
HELP_SPY_SMA = (
    "The market's average price over the last 20 days. "
    "Why it matters: when SPY is below this line, the short-term trend is down and "
    "even good stocks get dragged lower — we apply a safety haircut to confidence scores."
)
HELP_MACRO_MULT = (
    "Safety haircut applied to every confidence score when conditions are rough. "
    "Example: 0.70 means all scores are reduced 30% to protect your capital. "
    "Why it matters: this stops the scanner from yelling 'buy' during a market storm "
    "when math alone looks cheap but reality is hostile."
)
HELP_MACRO_DETAIL = (
    "Why we show this: macro filters exist because options are leveraged bets on stocks "
    "that mostly move with the index. Ignoring market weather is how retail traders "
    "buy 'perfect' setups that still lose."
)

# --- Stock profile ---
STOCK_HEALTH_TITLE = "Company Health Check"
STOCK_HEALTH_INTRO = (
    "Cheap doesn't always mean good — falling stocks can keep falling. "
    "We grade recent momentum so buyers are stepping in before you risk money."
)
HELP_TREND_SCORE = (
    "0–100 grade for how healthy the stock's price trend is. "
    "80+ = strong upward momentum · 50–79 = mixed · under 50 = struggling. "
    "Why it matters: buying calls against a weak trend is fighting the stock's current "
    "direction — the math may look cheap but momentum rarely cooperates."
)
HELP_RSI = (
    "Rubber-band effect. Under 30 = sold too hard, might bounce. "
    "Over 70 = running hot, might need a rest. 30–70 = neutral. "
    "Why it matters: extreme RSI helps you know if you're chasing a exhausted move "
    "or catching a genuine reversal."
)
HELP_VS_SPY = (
    "How this stock is performing vs. the whole market over the last 20 days. "
    "Positive = outperforming · negative = lagging. "
    "Why it matters: leaders in a up market tend to keep working; laggards often "
    "stay laggards even when you buy calls."
)
HELP_BETA = (
    "Price swing risk. If the market drops 1%, how much might this stock drop? "
    "1.0 ≈ moves with market · above 1 = wilder · below 1 = steadier. "
    "Why it matters: feeds the Mirror Check — high-beta calls stack into one "
    "hidden Nasdaq-sized bet faster than you think."
)
HELP_HV = (
    "How wildly this stock's price has swung recently (30/60/90 day windows). "
    "Why it matters: fair-value math uses this to judge if the option premium is "
    "cheap or expensive vs. how the stock actually behaves."
)
HELP_GARCH_VOL = (
    "5-day GARCH(1,1) forward volatility forecast — anticipates vol clustering after shocks. "
    "Why it matters: replaces purely backward-looking HV when pricing fair value; "
    "expand regime = bigger moves expected, compress = possible Vega overpay."
)
HELP_EFFECTIVE_HV = (
    "50/50 blend of GARCH forecast and historical vol used in Black-Scholes fair value. "
    "Why it matters: this is the predictive input to expected return — not the flat 30-day average alone."
)
HELP_SMA_STACK = (
    "Short / medium / long trend arrows. All up = healthy uptrend. "
    "Mixed or all down = trend is fighting you."
)
HELP_MACD = "Who's winning right now — buyers (bullish) or sellers (bearish)."
HELP_ROC = "Recent report card: percent gain or loss over the last 20 and 60 days."
HELP_52W = "Where today's price sits inside the last year's high–low range (0% = at lows, 100% = at highs)."
HELP_DRAWDOWN = "How far the stock has fallen from its recent peak."
HELP_VOLUME = (
    "Today's trading volume compared to the 20-day average. Spikes often mean big moves. "
    "Why it matters: breakouts on low volume often fail — we warn when price rises without "
    "real participation."
)

# --- Risk dashboard & journal ---
RISK_DASHBOARD_TITLE = "Account Risk Monitor"
RISK_DASHBOARD_INTRO = (
    "Why we track this: individual trades can look safe while your **combined** worst-case "
    "loss breaches account limits. This panel aggregates open paper trades before you add another."
)
HELP_OPEN_TRADES = (
    "Number of paper positions still marked open in your journal. "
    "Why it matters: each open leg adds Delta exposure and P95 risk — stacking too many "
    "is how traders accidentally go all-in on one market direction."
)
HELP_P95_RISK = (
    "Sum of Monte Carlo 95th-percentile worst-case losses on all open trades. "
    "Why it matters: this is the stress-test tail risk — if the market gaps against you, "
    "this is the neighborhood of pain you planned for."
)
HELP_RISK_CAP = (
    "Maximum combined P95 risk allowed before the Emergency Brake locks new trades (10% of bankroll). "
    "Why it matters: caps total simultaneous exposure so one bad day cannot wipe more "
    "than a fraction of your account."
)
MIRROR_CHECK_INTRO = (
    "Why we show this: five different tech calls feels diversified, but beta-weighting "
    "reveals you may be holding hundreds of SPY-equivalent shares — one index dip hits all at once."
)
HELP_MIRROR_SPY = (
    "Total market exposure of open calls translated into equivalent SPY shares "
    "(delta × contracts × 100 × spot × beta ÷ SPY price). "
    "Why it matters: if this number is high, you are not diversified — you are leveraged long "
    "the broad market and should stop adding calls."
)

# --- Top-pick analytics ---
WHY_KELLY = (
    "Quarter-Kelly caps how much of your bankroll this contract deserves based on edge and odds. "
    "Why it matters: even a great setup should not get 10% of your account — Kelly keeps "
    "winners from becoming account-killers through oversizing."
)
WHY_EV = (
    "Model estimate of average profit or loss per contract at expiry vs. normal stock swings. "
    "Why it matters: positive EV means the premium looks cheap on paper; negative EV means "
    "you are paying for hype, not edge."
)
WHY_STRESS = (
    "Worst-case loss from a grid of spot and IV shocks (±15% price, ±20% volatility). "
    "Why it matters: shows the cliff beyond breakeven — where a 'small' market move "
    "still destroys the position."
)
WHY_MC = (
    "95th-percentile loss from thousands of simulated price paths using this stock's history. "
    "Why it matters: catches fat-tail risk the stress grid might miss — used by the "
    "Emergency Brake to lock new trades when cumulative tail risk is too high."
)
WHY_VANNA = (
    "Second-order Greeks: how Delta changes when IV (Vanna) or time (Charm) moves. "
    "Why it matters: near earnings or OPEX, Delta can shift violently without the stock "
    "moving — early warning for gamma/vega traps."
)
WHY_PAYOFF_XRAY = (
    "Visual profit and loss at expiry across stock prices. "
    "Why it matters: numbers alone force mental math — this chart shows breakeven, "
    "the profit zone, and the cliff where you lose 100% of premium."
)
WHY_SCATTER = (
    "Each dot is a candidate contract — higher = more confidence, right = higher strike. "
    "Why it matters: lets you see trade-offs at a glance instead of reading a wall of columns."
)
HELP_TICKER_SPOT = (
    "Current stock price and recent news tone from headlines. "
    "Why it matters: price is your anchor for moneyness; news tone feeds sentiment "
    "into the confidence score (positive headlines get a small boost, negative a haircut)."
)
WHY_QUICK_LIST_EV = (
    "Expected return is the model's average profit or loss in dollars per contract. "
    "Why it matters: confidence tells you quality; expected return tells you magnitude — "
    "a 90-score on a $5 contract beats a 95-score that only pays $0.50."
)
WHY_LIST_RATIONALE = (
    "In-depth plain-English walkthrough — what you are buying, whether the price looks fair, "
    "how the stock and market look, and any caution flags. Hover ℹ️ for a shorter summary."
)
SCAN_SUMMARY_TITLE = "Scan Summary — All Tickers"
SCAN_SUMMARY_INTRO = (
    "Why we show this: one sortable table replaces squished metric columns. "
    "Click any column header to rank by confidence, momentum, or news tone — "
    "then pick one ticker below for the full deep dive."
)
DEEP_DIVE_TITLE = "Deep Dive — One Ticker at a Time"
DEEP_DIVE_INTRO = (
    "Why one at a time: scanning 30 tabs at once encourages machine-gunner overtrading. "
    "Select a single symbol and use the full screen width for Health Check, Payoff X-Ray, and ideas."
)
WHY_SCALPER = (
    "Quick-scalp contracts scored on **volume, spread tightness, gamma, and how close to the money** — "
    "not the full swing conviction model (trend, news, macro). "
    "**70+ is a strong scalp score** in this list; seeing nothing above 75 is normal because no contract "
    "maxes every intraday pillar at once. This is a different game than 14–45 day swing picks."
)

WHY_AUTOPSY = (
    "When you close a paper trade, we fetch live bid/spot/IV and split your P&L into "
    "Direction (Delta), Time (Theta), and Volatility (Vega). "
    "Why it matters: a losing streak is only useful feedback if you know *why* you lost — "
    "random Delta vs. managed Theta tells you whether the system or the wave failed."
)

# --- Exit checker ---
HELP_EXIT_SPOT = (
    "Live stock price from Yahoo Finance. "
    "Why it matters: compares where the stock is vs. your strike for exit timing rules."
)
HELP_EXIT_PROFIT = (
    "Your gain or loss on the contract vs. entry. "
    "Why it matters: house-money and profit-taking rules trigger at key thresholds (+100%, etc.)."
)
HELP_EXIT_RSI = (
    "14-day momentum oscillator for the stock. "
    "Why it matters: overbought RSI suggests taking profits; weak RSI warns the trend may be fading."
)
HELP_EXIT_DTE = (
    "Days until the contract expires. "
    "Why it matters: Theta accelerates in the final week — holding losers too close to expiry "
    "often means watching premium go to zero."
)

# --- Sandbox ---
HELP_TIER_BAND = (
    "High / solid / cautious band based on confidence score. "
    "Why it matters: not every idea deserves full size — weak scores get cut to protect the bankroll."
)
HELP_SIZE_MULT = (
    "Multiplier applied to your base risk percent for this confidence level. "
    "Why it matters: scales position up only when the model is strongly aligned."
)
HELP_DOLLAR_BUDGET = (
    "Maximum dollars the system recommends putting on this idea. "
    "Why it matters: converts abstract 'risk %' into real dollars before you click buy."
)
HELP_CONTRACTS = (
    "Whole contracts your budget can afford at this premium. "
    "Why it matters: options trade in 100-share lots — this is the actionable number for your broker."
)
HELP_OPEN_RISK = (
    "Total premium already tied up in open option positions. "
    "Why it matters: IML tracks whether you still have enough equity cushion if positions move against you."
)
HELP_IML = (
    "Intraday Margin Level — equity cushion after maintenance on open premium risk. "
    "Why it matters: simulates broker margin stress; when this gets thin, adding more trades is dangerous."
)
HELP_MAINTENANCE = (
    "Estimated maintenance requirement on your open option premium. "
    "Why it matters: brokers reserve buying power against open risk even before you lose money."
)
HELP_KILL_SWITCH = (
    "Advisory flag when IML drops below safe levels. "
    "Why it matters: mimics a prop-desk rule — stop adding risk when the account is already stressed."
)
HELP_EMPIRICAL_KELLY = (
    "Quarter-Kelly cap from your last closed paper trades (win rate + avg win/loss). "
    "Why it matters: if your actual execution lags the model, this cuts size before the account pays for slippage and emotion."
)
HELP_THEORETICAL_KELLY = (
    "Quarter-Kelly from Black-Scholes prob ITM and model risk/reward. "
    "Why it matters: what a perfect robot would size — capped by empirical reality when journal data exists."
)
HELP_KELLY_FINAL = (
    "min(theoretical Kelly, empirical Kelly, 3% bankroll cap). "
    "Why it matters: the brakes — you size to the weaker of math and your proven track record."
)
HELP_PAPER_LOG = (
    "CSV template for tracking 20–30 paper trades. "
    "Why it matters: the journal inside the app is faster, but a spreadsheet backup "
    "helps you review patterns over weeks."
)

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
