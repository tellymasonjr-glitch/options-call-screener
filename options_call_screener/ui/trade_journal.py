"""Rearview Mirror — paper trade journal + account risk aggregator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config import ACCOUNT_RISK_LOCK_PCT, JOURNAL_FILENAME

JOURNAL_COLUMNS = [
    "logged_at",
    "ticker",
    "sector",
    "strike",
    "expiration",
    "entry_ask",
    "spot_at_entry",
    "total_cost",
    "confidence",
    "expected_return",
    "mc_p95_loss",
    "status",
]


def journal_path() -> Path:
    return Path(__file__).resolve().parents[1] / JOURNAL_FILENAME


def _empty_journal() -> pd.DataFrame:
    return pd.DataFrame(columns=JOURNAL_COLUMNS)


def load_journal() -> pd.DataFrame:
    if "paper_journal" not in st.session_state:
        path = journal_path()
        if path.is_file():
            try:
                st.session_state.paper_journal = pd.read_csv(path)
            except Exception:
                st.session_state.paper_journal = _empty_journal()
        else:
            st.session_state.paper_journal = _empty_journal()
    return st.session_state.paper_journal


def save_journal(df: pd.DataFrame) -> None:
    st.session_state.paper_journal = df
    try:
        df.to_csv(journal_path(), index=False)
    except OSError:
        pass


def append_paper_trade(row: pd.Series, spot: float, sector: str = "") -> None:
    df = load_journal()
    cost = float(row.get("size_total_cost") or row.get("total_cost") or 0)
    if cost <= 0:
        cost = float(row.get("ask", 0)) * 100

    entry = {
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ticker": str(row.get("ticker", "")),
        "sector": sector or str(row.get("sector", "")),
        "strike": float(row["strike"]),
        "expiration": str(row["expiration"]),
        "entry_ask": float(row["ask"]),
        "spot_at_entry": spot,
        "total_cost": cost,
        "confidence": float(row.get("conviction_score") or row.get("display_confidence") or 0),
        "expected_return": float(row.get("ev") or 0),
        "mc_p95_loss": float(row.get("mc_p95_loss") or row.get("max_loss_dollars") or cost),
        "status": "open",
    }
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    save_journal(df)


def open_trades_risk_total() -> float:
    df = load_journal()
    if df.empty:
        return 0.0
    open_df = df[df["status"].astype(str).str.lower() == "open"]
    if open_df.empty:
        return 0.0
    losses = pd.to_numeric(open_df["mc_p95_loss"], errors="coerce").fillna(0)
    return float(losses.sum())


def is_execution_locked(bankroll: float) -> tuple[bool, str]:
    if bankroll <= 0:
        return False, ""
    total = open_trades_risk_total()
    cap = bankroll * ACCOUNT_RISK_LOCK_PCT
    if total > cap:
        return True, (
            f"Emergency brake ON — open paper trades P95 worst-case (${total:,.0f}) "
            f"exceeds {ACCOUNT_RISK_LOCK_PCT:.0%} of bankroll (${cap:,.0f}). "
            "Close or journal-exit trades before adding new ones."
        )
    return False, ""


def render_risk_dashboard(bankroll: float) -> bool:
    """Show cumulative exposure; return True if new trades are locked."""
    total = open_trades_risk_total()
    cap = bankroll * ACCOUNT_RISK_LOCK_PCT if bankroll > 0 else 0
    df = load_journal()
    open_count = len(df[df["status"].astype(str).str.lower() == "open"]) if not df.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Open paper trades", str(open_count))
    c2.metric("Combined P95 risk", f"${total:,.0f}")
    c3.metric("Account risk cap", f"${cap:,.0f}" if cap else "—")

    locked, msg = is_execution_locked(bankroll)
    if locked:
        st.error(msg)
    elif total > 0 and cap > 0:
        pct = total / cap * 100
        st.caption(f"Cumulative worst-case exposure at **{pct:.0f}%** of the 10% lock threshold.")

    if not df.empty:
        with st.expander("Paper trade journal", expanded=False):
            st.dataframe(df.tail(20), use_container_width=True, hide_index=True)
            st.download_button(
                "Download journal (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name=JOURNAL_FILENAME,
                mime="text/csv",
                key="download_journal",
            )
    return locked


def render_execute_button(
    row: pd.Series,
    spot: float,
    *,
    sector: str = "",
    button_key: str,
    locked: bool,
) -> None:
    if locked:
        st.button("Execute Paper Trade (locked)", key=button_key, disabled=True)
        return
    if st.button("Execute Paper Trade", key=button_key, type="secondary"):
        append_paper_trade(row, spot, sector=sector)
        st.success(f"Logged {row.get('ticker')} ${row['strike']} call to journal.")
        st.rerun()
