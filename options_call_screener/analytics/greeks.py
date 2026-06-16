"""Black-Scholes-Merton Greeks (continuous dividend yield q)."""

from __future__ import annotations

import math

from scipy.stats import norm

RISK_FREE_RATE = 0.045


def _d1d2(
    spot: float,
    strike: float,
    t_years: float,
    sigma: float,
    rate: float = RISK_FREE_RATE,
    div_yield: float = 0.0,
) -> tuple[float, float]:
    if t_years <= 0 or sigma <= 0 or spot <= 0 or strike <= 0:
        return 0.0, 0.0
    q = max(div_yield, 0.0)
    d1 = (
        math.log(spot / strike) + (rate - q + 0.5 * sigma**2) * t_years
    ) / (sigma * math.sqrt(t_years))
    d2 = d1 - sigma * math.sqrt(t_years)
    return d1, d2


def call_greeks(
    spot: float,
    strike: float,
    dte: int,
    iv: float,
    rate: float = RISK_FREE_RATE,
    div_yield: float = 0.0,
) -> dict[str, float]:
    """Call delta, gamma, theta (per day), vega (per 1% IV), rho (per 1% rate)."""
    t = max(dte, 1) / 365.0
    sigma = max(iv, 0.05)
    q = max(div_yield, 0.0)

    d1, d2 = _d1d2(spot, strike, t, sigma, rate, q)
    disc_s = math.exp(-q * t)
    disc_k = math.exp(-rate * t)

    delta = float(disc_s * norm.cdf(d1))
    gamma = float(disc_s * norm.pdf(d1) / (spot * sigma * math.sqrt(t)))
    theta = float(
        -(
            spot * disc_s * norm.pdf(d1) * sigma / (2 * math.sqrt(t))
            + rate * strike * disc_k * norm.cdf(d2)
            - q * spot * disc_s * norm.cdf(d1)
        )
        / 365.0
    )
    vega = float(spot * disc_s * norm.pdf(d1) * math.sqrt(t) / 100.0)
    rho = float(strike * t * disc_k * norm.cdf(d2) / 100.0)

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho,
    }
