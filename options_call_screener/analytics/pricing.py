"""Black-Scholes-Merton pricing, probabilities, and trade metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.stats import norm

from analytics.greeks import RISK_FREE_RATE, _d1d2, call_greeks


@dataclass(frozen=True)
class TradeMetrics:
    """Quantitative metrics for a single long-call candidate."""

    bs_fair_iv: float
    bs_fair_hv: float
    prob_itm: float
    ev_hv: float
    edge_pct: float
    iv_hv_ratio: float
    breakeven: float
    expected_move: float
    payoff_1sigma: float
    risk_reward: float
    theta_pct_daily: float
    moneyness_pct: float
    vega_per_contract: float
    rho: float


def bs_call_price(
    spot: float,
    strike: float,
    t_years: float,
    sigma: float,
    rate: float = RISK_FREE_RATE,
    div_yield: float = 0.0,
) -> float:
    """Black-Scholes-Merton European call price per share."""
    if spot <= 0 or strike <= 0:
        return 0.0
    if t_years <= 0:
        return max(spot - strike, 0.0)

    sigma = max(sigma, 1e-4)
    q = max(div_yield, 0.0)
    d1, d2 = _d1d2(spot, strike, t_years, sigma, rate, q)
    return float(
        spot * math.exp(-q * t_years) * norm.cdf(d1)
        - strike * math.exp(-rate * t_years) * norm.cdf(d2)
    )


def prob_itm_call(
    spot: float,
    strike: float,
    t_years: float,
    sigma: float,
    rate: float = RISK_FREE_RATE,
    div_yield: float = 0.0,
) -> float:
    """Risk-neutral P(S_T > K) = N(d2) under BSM."""
    if t_years <= 0:
        return 1.0 if spot > strike else 0.0
    sigma = max(sigma, 1e-4)
    _, d2 = _d1d2(spot, strike, t_years, sigma, rate, div_yield)
    return float(norm.cdf(d2))


def compute_trade_metrics(
    spot: float,
    strike: float,
    ask: float,
    dte: int,
    iv: float,
    hv: float,
    theta: float = 0.0,
    div_yield: float = 0.0,
) -> TradeMetrics:
    """
    Core metrics for ranking long calls.

    EV = BS fair value at blended HV minus premium paid (per contract).
    """
    t = max(dte, 1) / 365.0
    iv = max(iv, 0.05)
    hv = max(hv, 0.05)
    ask = max(ask, 0.0)
    cost = ask * 100
    q = max(div_yield, 0.0)

    fair_iv = bs_call_price(spot, strike, t, iv, div_yield=q)
    fair_hv = bs_call_price(spot, strike, t, hv, div_yield=q)
    prob = prob_itm_call(spot, strike, t, iv, div_yield=q)

    greeks = call_greeks(spot, strike, dte, iv, div_yield=q)
    if theta == 0.0:
        theta = greeks["theta"]

    ev_hv = fair_hv * 100 - cost
    edge_pct = (fair_hv - ask) / ask if ask > 0 else 0.0
    iv_hv_ratio = iv / hv

    expected_move = spot * (math.exp(hv * math.sqrt(t)) - 1.0)
    spot_up = spot + expected_move
    payoff_1sigma = max(0.0, spot_up - strike) * 100 - cost
    risk_reward = payoff_1sigma / cost if cost > 0 else 0.0

    theta_pct = (abs(theta) / ask * 100.0) if ask > 0 and theta else 0.0
    moneyness_pct = (spot - strike) / spot if spot > 0 else 0.0
    vega_per_contract = greeks["vega"] * 100.0

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
        vega_per_contract=vega_per_contract,
        rho=greeks["rho"],
    )
