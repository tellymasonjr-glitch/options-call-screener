"""Wheel strategy advisory (manual execution only — no broker API)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WheelAdvisory:
    eligible: bool
    summary: str
    entry_note: str
    exit_note: str
    roll_note: str


def evaluate_wheel_fit(
    *,
    iv_rank: float,
    profile_score: float,
    spot: float,
    hv_30: float,
) -> WheelAdvisory:
    """
    Checks whether the underlying fits classic Wheel criteria (sell puts / covered calls).

    This screener buys calls; Wheel is income via short puts — shown as alternate playbook.
    """
    iv_ok = iv_rank >= 30
    quality_ok = profile_score >= 55
    eligible = iv_ok and quality_ok

    entry = (
        f"IV rank {iv_rank:.0f} — {'adequate' if iv_ok else 'too low'} for cash-secured puts. "
        "Target ~0.30 delta puts, 30–45 DTE when you want to acquire shares."
    )
    exit_rule = (
        "Offensive exit: buy back short option at 50% max profit with 21+ DTE left "
        "(reduces Gamma risk, frees capital)."
    )
    roll_rule = (
        "Defensive roll: if price threatens short put strike, roll down-and-out for a net credit "
        "to lower assignment basis — only if credit is positive."
    )

    if eligible:
        summary = (
            f"**Wheel-compatible underlying** — strong enough trend health ({profile_score:.0f}/100) "
            f"and elevated IV rank for premium selling. Consider Wheel instead of long calls if you "
            f"want income and are willing to own {spot:.0f} area shares."
        )
    else:
        summary = (
            "Long-call mode is preferred here — IV rank or trend health does not meet typical "
            "Wheel entry thresholds (IVR ≥ 30, profile ≥ 55)."
        )

    return WheelAdvisory(
        eligible=eligible,
        summary=summary,
        entry_note=entry,
        exit_note=exit_rule,
        roll_note=roll_rule,
    )
