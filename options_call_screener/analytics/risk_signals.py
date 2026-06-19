"""Contract-level risk flags (IV crush, Vega overpay, Gamma, spread friction)."""

from __future__ import annotations

from dataclasses import dataclass

from config import MIN_OPEN_INTEREST, MIN_VOLUME


@dataclass(frozen=True)
class ContractRiskFlags:
    iv_crush_warning: bool
    vega_overpay_warning: bool
    gamma_acceleration_warning: bool
    spread_friction_dollars: float
    max_loss_dollars: float
    warning_messages: tuple[str, ...]


def evaluate_contract_risks(
    *,
    iv_rank: float,
    dte: int,
    delta: float,
    spread_pct: float,
    ask: float,
    near_earnings: bool,
    open_interest: int = 0,
    volume: int = 0,
    garch_regime: str = "neutral",
) -> ContractRiskFlags:
    """Retail-trap detectors aligned with long-call premium buying."""
    warnings: list[str] = []
    cost = ask * 100

    iv_crush = iv_rank >= 50 and near_earnings
    if iv_crush:
        warnings.append(
            "IV Crush Risk — implied volatility is elevated near an earnings date. "
            "Even a correct directional move can lose money when Vega collapses."
        )

    vega_overpay = iv_rank >= 60 and dte >= 7
    if vega_overpay and not iv_crush:
        warnings.append(
            "Vega Overpay Warning — you may be buying inflated premium (high IV rank). "
            "Retail studies show systematic overpayment before volatility events."
        )
    elif vega_overpay:
        pass  # iv_crush message covers earnings case

    gamma_warn = dte <= 7 and delta >= 0.40
    if gamma_warn:
        warnings.append(
            "Gamma Acceleration — less than a week to expiry with a sensitive delta. "
            "Small price moves can swing the option sharply (good and bad)."
        )

    if dte == 0:
        warnings.append(
            "0DTE Lottery Ticket — extrinsic value goes to zero at the close. "
            "Wide spreads and max Gamma make this a high-friction scalp, not investing."
        )

    spread_friction = (spread_pct * ask * 100) / 2.0 if spread_pct > 0 else 0.0
    if garch_regime == "compress":
        warnings.append(
            "GARCH Vol Compression — forward vol forecast is below 30-day HV. "
            "Calm may lie ahead; you may be overpaying Vega if IV is still elevated."
        )
    elif garch_regime == "expand":
        warnings.append(
            "GARCH Vol Expansion — forward vol forecast exceeds 30-day HV. "
            "Volatility clustering suggests bigger moves ahead; fair-value uses blended forward vol."
        )

    if open_interest < MIN_OPEN_INTEREST or volume < MIN_VOLUME:
        warnings.append(
            f"Empty Room — OI {open_interest} / volume {volume}. "
            "Nobody is trading this strike; confidence is zero regardless of BSM math."
        )
    elif spread_pct >= 0.10:
        warnings.append(
            f"Ghost Tax — spread is {spread_pct:.0%} of mid price (~${spread_friction:.0f} slippage per round trip). "
            "Confidence is cut in half above 10% spread."
        )
    elif spread_pct >= 0.08:
        warnings.append(
            f"High slippage warning — {spread_pct:.0%} bid/ask gap (~${spread_friction:.0f} friction)."
        )

    return ContractRiskFlags(
        iv_crush_warning=iv_crush,
        vega_overpay_warning=vega_overpay,
        gamma_acceleration_warning=gamma_warn,
        spread_friction_dollars=round(spread_friction, 2),
        max_loss_dollars=round(cost, 2),
        warning_messages=tuple(warnings),
    )


def risk_penalty_multiplier(flags: ContractRiskFlags) -> float:
    """Small conviction penalty for structural retail traps."""
    mult = 1.0
    if flags.iv_crush_warning:
        mult *= 0.82
    elif flags.vega_overpay_warning:
        mult *= 0.90
    if flags.gamma_acceleration_warning and not flags.iv_crush_warning:
        mult *= 0.95
    if flags.spread_friction_dollars > 15:
        mult *= 0.92
    return mult
