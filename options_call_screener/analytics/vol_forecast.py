"""GARCH(1,1) forward volatility forecast — anticipates vol clustering."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import (
    GARCH_COMPRESS_RATIO,
    GARCH_EXPAND_RATIO,
    GARCH_FORECAST_HORIZON,
    GARCH_MIN_OBS,
)


@dataclass(frozen=True)
class VolForecast:
    """Forward-looking vol estimate from GARCH(1,1) on daily returns."""

    garch_vol_annual: float
    hv_30: float
    garch_hv_ratio: float
    regime: str  # expand | compress | neutral
    horizon_days: int
    available: bool
    note: str = ""

    @property
    def expansion_expected(self) -> bool:
        return self.regime == "expand"

    @property
    def compression_expected(self) -> bool:
        return self.regime == "compress"


def _classify_regime(ratio: float) -> str:
    if ratio >= GARCH_EXPAND_RATIO:
        return "expand"
    if ratio <= GARCH_COMPRESS_RATIO:
        return "compress"
    return "neutral"


def _regime_note(regime: str, garch: float, hv: float) -> str:
    if regime == "expand":
        return (
            f"GARCH forecasts {garch:.0%} vol vs {hv:.0%} (30d HV) — "
            "volatility clustering suggests expansion; HV may understate fair value."
        )
    if regime == "compress":
        return (
            f"GARCH forecasts {garch:.0%} vol vs {hv:.0%} (30d HV) — "
            "calm ahead expected; watch for overpaying Vega on inflated premiums."
        )
    return f"GARCH {garch:.0%} aligned with 30d HV {hv:.0%}."


def forecast_garch_vol(
    closes: pd.Series,
    *,
    hv_30: float | None = None,
    horizon: int = GARCH_FORECAST_HORIZON,
    min_obs: int = GARCH_MIN_OBS,
) -> VolForecast:
    """
    Fit GARCH(1,1) on daily log returns and forecast mean conditional vol.

    Returns annualized decimal volatility (e.g. 0.35 = 35%).
    Falls back gracefully when data or fit is insufficient.
    """
    series = closes.astype(float).dropna()
    ref_hv = float(hv_30) if hv_30 and hv_30 > 0 else 0.25

    if len(series) < min_obs:
        return VolForecast(
            garch_vol_annual=ref_hv,
            hv_30=ref_hv,
            garch_hv_ratio=1.0,
            regime="neutral",
            horizon_days=horizon,
            available=False,
            note="Insufficient history for GARCH — using historical vol.",
        )

    log_ret = np.log(series / series.shift(1)).dropna()
    if len(log_ret) < min_obs - 5:
        return VolForecast(
            garch_vol_annual=ref_hv,
            hv_30=ref_hv,
            garch_hv_ratio=1.0,
            regime="neutral",
            horizon_days=horizon,
            available=False,
            note="Insufficient return history for GARCH.",
        )

    try:
        from arch import arch_model

        # Scale to percent for numerical stability (arch convention)
        pct_returns = log_ret * 100.0
        model = arch_model(
            pct_returns,
            mean="Zero",
            vol="Garch",
            p=1,
            q=1,
            rescale=False,
        )
        result = model.fit(disp="off", show_warning=False)
        variance_fc = result.forecast(horizon=horizon, reindex=False).variance
        # Mean variance over forecast horizon (percent^2)
        mean_var = float(variance_fc.iloc[-1].mean())
        if mean_var <= 0 or math.isnan(mean_var):
            raise ValueError("invalid GARCH variance forecast")

        daily_vol = math.sqrt(mean_var) / 100.0
        garch_annual = daily_vol * math.sqrt(252)
        garch_annual = float(np.clip(garch_annual, 0.05, 2.0))

        ratio = garch_annual / ref_hv if ref_hv > 0 else 1.0
        regime = _classify_regime(ratio)

        return VolForecast(
            garch_vol_annual=garch_annual,
            hv_30=ref_hv,
            garch_hv_ratio=round(ratio, 3),
            regime=regime,
            horizon_days=horizon,
            available=True,
            note=_regime_note(regime, garch_annual, ref_hv),
        )
    except Exception:
        return VolForecast(
            garch_vol_annual=ref_hv,
            hv_30=ref_hv,
            garch_hv_ratio=1.0,
            regime="neutral",
            horizon_days=horizon,
            available=False,
            note="GARCH fit failed — using historical vol only.",
        )


def blended_forecast_hv(
    hv_blended: float,
    forecast: VolForecast | None,
    *,
    garch_weight: float | None = None,
) -> float:
    """Blend backward-looking HV with forward GARCH when available."""
    from config import GARCH_HV_BLEND

    w = GARCH_HV_BLEND if garch_weight is None else garch_weight
    if forecast is None or not forecast.available:
        return hv_blended
    w = float(np.clip(w, 0.0, 1.0))
    return float(w * forecast.garch_vol_annual + (1.0 - w) * hv_blended)
