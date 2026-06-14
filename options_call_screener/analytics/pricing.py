"""Black-Scholes pricing, risk-neutral probabilities, and trade metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm

from analytics.greeks import RISK_FREE_RATE, _d1d2


@dataclass(frozen=True)
class TradeMetrics:
    """Quantitative metrics for a single long-call candidate."""

    bs_fair_iv: float          # BS fair value per share using market IV
    bs_fair_hv: float          # BS fair value per share using historical vol
    prob_itm: float            # Risk-neutral P(S_T > K) = N(d2)
    ev_hv: float               # E[payoff|σ=HV] - premium (dollars per contract)
    edge_pct: float            # (bs_fair_hv - ask) / ask
    iv_hv_ratio: float         # IV / HV variance risk premium proxy
    breakeven: float           # Strike + premium
    expected_move: float       # 1σ log-normal move in dollars
    payoff_1sigma: float       # P&L at spot + 1σ move
    risk_reward: float         # payoff_1sigma / max_loss
    theta_pct_daily: float     # |theta| / ask as % per day
    moneyness_pct: float       # (spot - strike) / spot


def bs_call_price(
    spot: float,
    strike: float,
    t_years: float,
    sigma: float,
    rate: float = RISK_FREE_RATE,
) -> float:
    """Black-Scholes European call price per share."""
    if spot <= 0 or strike <= 0:
        return 0.0
    if t_years <= 0:
        return max(spot - strike, 0.0)

    sigma = max(sigma, 1e-4)
    d1, d2 = _d1d2(spot, strike, t_years, sigma, rate)
    return float(
        spot * norm.cdf(d1) - strike * math.exp(-rate * t_years) * norm.cdf(d2)
    )


def prob_itm_call(
    spot: float,
    strike: float,
    t_years: float,
    sigma: float,
    rate: float = RISK_FREE_RATE,
) -> float:
    """Risk-neutral probability call expires in-the-money: N(d2)."""
    if t_years <= 0:
        return 1.0 if spot > strike else 0.0
    sigma = max(sigma, 1e-4)
    _, d2 = _d1d2(spot, strike, t_years, sigma, rate)
    return float(norm.cdf(d2))


def compute_trade_metrics(
    spot: float,
    strike: float,
    ask: float,
    dte: int,
    iv: float,
    hv: float,
    theta: float = 0.0,
) -> TradeMetrics:
    """
    Core quantitative metrics for ranking long calls.

    EV uses BS fair value with historical vol as a forward-vol estimate,
    minus the ask paid — positive EV means HV-implied value exceeds premium.
    """
    t = max(dte, 1) / 365.0
    iv = max(iv, 0.05)
    hv = max(hv, 0.05)
    ask = max(ask, 0.0)
    cost = ask * 100

    fair_iv = bs_call_price(spot, strike, t, iv)
    fair_hv = bs_call_price(spot, strike, t, hv)
    prob = prob_itm_call(spot, strike, t, iv)

    ev_hv = fair_hv * 100 - cost
    edge_pct = (fair_hv - ask) / ask if ask > 0 else 0.0
    iv_hv_ratio = iv / hv

    # 1σ log-normal upward move (consistent with BS lognormal dynamics)
    expected_move = spot * (math.exp(hv * math.sqrt(t)) - 1.0)
    spot_up = spot + expected_move
    payoff_1sigma = max(0.0, spot_up - strike) * 100 - cost
    risk_reward = payoff_1sigma / cost if cost > 0 else 0.0

    theta_pct = (abs(theta) / ask * 100.0) if ask > 0 and theta else 0.0
    moneyness_pct = (spot - strike) / spot if spot > 0 else 0.0

    return TradeMetrics(
        bs_fair_iv=fair_iv,
        bs_fair_hv=fair_hv,
        prob_itm=prob,
        ev_hv=ev_hv,
        edge_pct=edge_pct,
        iv_hv_ratio=iv_hv_ratio,
        breakeven=strike + ask,
        expected_move=expected_move,
        payoff_1sigma=payoff_1sigma,
        risk_reward=risk_reward,
        theta_pct_daily=theta_pct,
        moneyness_pct=moneyness_pct,
    )
