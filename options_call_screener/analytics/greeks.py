"""Black-Scholes-Merton Greeks including second-order Vanna and Charm."""

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
    """First- and second-order call Greeks (daily Theta/Charm)."""
    t = max(dte, 1) / 365.0
    sigma = max(iv, 0.05)
    q = max(div_yield, 0.0)

    d1, d2 = _d1d2(spot, strike, t, sigma, rate, q)
    disc_s = math.exp(-q * t)
    disc_k = math.exp(-rate * t)
    pdf_d1 = float(norm.pdf(d1))
    cdf_d1 = float(norm.cdf(d1))
    cdf_d2 = float(norm.cdf(d2))

    delta = float(disc_s * cdf_d1)
    gamma = float(disc_s * pdf_d1 / (spot * sigma * math.sqrt(t)))
    theta = float(
        -(
            spot * disc_s * pdf_d1 * sigma / (2 * math.sqrt(t))
            + rate * strike * disc_k * cdf_d2
            - q * spot * disc_s * cdf_d1
        )
        / 365.0
    )
    vega = float(spot * disc_s * pdf_d1 * math.sqrt(t) / 100.0)
    rho = float(strike * t * disc_k * cdf_d2 / 100.0)

    # ∂Delta/∂σ (per 1 vol point) — Vanna
    vanna = float(-disc_s * pdf_d1 * d2 / sigma)

    # ∂Delta/∂t (annual) → daily Charm
    if t > 0:
        charm_annual = -disc_s * (
            pdf_d1 * (2 * (rate - q) * t - d2 * sigma * math.sqrt(t))
            / (2 * t * sigma * math.sqrt(t))
            + q * cdf_d1
        )
        charm = float(charm_annual / 365.0)
    else:
        charm = 0.0

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho,
        "vanna": vanna,
        "charm": charm,
    }
