"""Black-Scholes Greeks for contracts missing exchange-reported values."""

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
) -> tuple[float, float]:
    if t_years <= 0 or sigma <= 0 or spot <= 0 or strike <= 0:
        return 0.0, 0.0
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma**2) * t_years) / (
        sigma * math.sqrt(t_years)
    )
    d2 = d1 - sigma * math.sqrt(t_years)
    return d1, d2


def call_greeks(
    spot: float,
    strike: float,
    dte: int,
    iv: float,
    rate: float = RISK_FREE_RATE,
) -> dict[str, float]:
    """Compute call delta, gamma, theta, vega from implied vol."""
    t = max(dte, 1) / 365.0
    sigma = max(iv, 0.05)

    d1, d2 = _d1d2(spot, strike, t, sigma, rate)
    delta = float(norm.cdf(d1))
    gamma = float(norm.pdf(d1) / (spot * sigma * math.sqrt(t)))
    theta = float(
        -(
            spot * norm.pdf(d1) * sigma / (2 * math.sqrt(t))
            + rate * strike * math.exp(-rate * t) * norm.cdf(d2)
        )
        / 365.0
    )
    vega = float(spot * norm.pdf(d1) * math.sqrt(t) / 100.0)

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}
