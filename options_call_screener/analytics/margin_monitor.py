"""FINRA-style intraday margin level (IML) advisory — no broker connection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarginSnapshot:
    equity: float
    maintenance_required: float
    iml: float
    imd: bool
    kill_switch: bool
    message: str


def compute_iml(
    equity: float,
    open_premium_at_risk: float,
    *,
    maintenance_pct: float = 1.0,
) -> MarginSnapshot:
    """
    Long-option simplified maintenance: premium at risk treated as maintenance base.

    IML = equity - maintenance. Negative IML => Intraday Margin Deficit (advisory kill switch).
    """
    maintenance = open_premium_at_risk * maintenance_pct
    iml = equity - maintenance
    imd = iml < 0

    if imd:
        msg = (
            "KILL SWITCH — Intraday Margin Deficit. Do not open new positions until equity "
            "covers premium at risk. Repeated IMDs can trigger broker restrictions."
        )
    elif iml < equity * 0.05:
        msg = "IML tight — little cushion above maintenance; size down on new trades."
    else:
        msg = "IML healthy — equity comfortably above maintenance requirement."

    return MarginSnapshot(
        equity=equity,
        maintenance_required=round(maintenance, 2),
        iml=round(iml, 2),
        imd=imd,
        kill_switch=imd,
        message=msg,
    )
