"""Empirical Kelly sizing from closed paper-trade journal outcomes (v5.3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import (
    EMPIRICAL_KELLY_LOOKBACK,
    EMPIRICAL_KELLY_MIN_TRADES,
    JOURNAL_FILENAME,
    KELLY_FRACTION,
    MAX_KELLY_RISK_PCT,
)


@dataclass(frozen=True)
class EmpiricalKellyStats:
    win_rate: float
    avg_win: float
    avg_loss: float
    reward_risk_ratio: float
    full_kelly: float
    quarter_kelly_pct: float
    sample_size: int
    sufficient: bool
    note: str


@dataclass(frozen=True)
class KellyCapResult:
    theoretical_pct: float
    empirical_pct: float | None
    final_pct: float
    empirical: EmpiricalKellyStats


def journal_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / JOURNAL_FILENAME


def load_journal_csv() -> pd.DataFrame:
    path = journal_csv_path()
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def get_journal_for_kelly() -> pd.DataFrame:
    """Prefer Streamlit session journal when the app is running."""
    try:
        import streamlit as st
        from ui.trade_journal import load_journal

        if "paper_journal" in st.session_state or journal_csv_path().is_file():
            return load_journal()
    except Exception:
        pass
    return load_journal_csv()


def _closed_trades(journal: pd.DataFrame) -> pd.DataFrame:
    if journal.empty or "status" not in journal.columns:
        return pd.DataFrame()
    closed = journal[journal["status"].astype(str).str.lower() == "closed"].copy()
    if closed.empty:
        return closed
    closed["actual_pnl"] = pd.to_numeric(closed.get("actual_pnl"), errors="coerce")
    return closed.dropna(subset=["actual_pnl"])


def compute_empirical_kelly(
    journal: pd.DataFrame,
    *,
    lookback: int = EMPIRICAL_KELLY_LOOKBACK,
    min_trades: int = EMPIRICAL_KELLY_MIN_TRADES,
) -> EmpiricalKellyStats:
    """
    Trailing journal Kelly: W - (1-W)/R on closed trades, then quarter-Kelly cap.

    R = average dollar win / average dollar loss (absolute).
    """
    closed = _closed_trades(journal)
    if closed.empty:
        return EmpiricalKellyStats(
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            reward_risk_ratio=0.0,
            full_kelly=0.0,
            quarter_kelly_pct=0.0,
            sample_size=0,
            sufficient=False,
            note="No closed journal trades yet — using theoretical Kelly only.",
        )

    tail = closed.tail(int(lookback))
    n = len(tail)
    wins = tail[tail["actual_pnl"] > 0]["actual_pnl"]
    losses = tail[tail["actual_pnl"] <= 0]["actual_pnl"]

    win_rate = len(wins) / n if n else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(abs(losses.mean())) if len(losses) else 0.0

    if avg_loss > 0 and avg_win > 0:
        rr = avg_win / avg_loss
    elif avg_win > 0 and len(losses) == 0:
        rr = max(avg_win / 1.0, 1.0)
    else:
        rr = 0.0

    if rr > 0:
        full_kelly = win_rate - (1.0 - win_rate) / rr
    else:
        full_kelly = 0.0

    full_kelly = max(0.0, float(full_kelly))
    quarter_pct = min(full_kelly * KELLY_FRACTION * 100.0, MAX_KELLY_RISK_PCT)

    sufficient = n >= min_trades
    if not sufficient:
        note = (
            f"{n}/{min_trades} closed trades logged — need more Autopsy closes "
            "before empirical Kelly caps sizing."
        )
    elif full_kelly <= 0:
        note = (
            f"Negative empirical edge over last {n} trades — "
            "Quarter-Kelly cap forced to 0% until execution improves."
        )
    else:
        note = (
            f"Last {n} closes: {win_rate:.0%} win rate, "
            f"${avg_win:,.0f} avg win / ${avg_loss:,.0f} avg loss (R={rr:.2f})."
        )

    return EmpiricalKellyStats(
        win_rate=round(win_rate, 4),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        reward_risk_ratio=round(rr, 3),
        full_kelly=round(full_kelly, 4),
        quarter_kelly_pct=round(quarter_pct, 2),
        sample_size=n,
        sufficient=sufficient,
        note=note,
    )


def resolve_kelly_cap(
    theoretical_pct: float,
    journal: pd.DataFrame | None = None,
) -> KellyCapResult:
    """
    Final Kelly bankroll cap = min(theoretical, empirical) when journal is ready.

    Theoretical pct should already be quarter-Kelly (e.g. from half_kelly_pct column).
    """
    journal = journal if journal is not None else get_journal_for_kelly()
    empirical = compute_empirical_kelly(journal)
    theoretical = max(0.0, float(theoretical_pct or 0.0))

    if empirical.sufficient:
        final = min(theoretical, empirical.quarter_kelly_pct)
    else:
        final = theoretical

    final = min(final, MAX_KELLY_RISK_PCT)
    return KellyCapResult(
        theoretical_pct=round(theoretical, 2),
        empirical_pct=round(empirical.quarter_kelly_pct, 2) if empirical.sufficient else None,
        final_pct=round(final, 2),
        empirical=empirical,
    )
