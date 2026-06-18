"""Rearview Mirror — paper trade journal, exposure mirror, and autopsy engine."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from analytics.pnl_attribution import attribute_long_call_pnl
from analytics.portfolio_exposure import (
    beta_weighted_spy_shares,
    exposure_warning,
    open_journal_trades,
)
from config import ACCOUNT_RISK_LOCK_PCT, JOURNAL_FILENAME
from data.cached_fetch import get_call_quote, get_spot_price
from data.yf_utils import is_rate_limit_error

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
    "contracts",
    "delta",
    "theta",
    "vega",
    "iv_at_entry",
    "beta",
    "entry_dte",
    "closed_at",
    "exit_bid",
    "exit_spot",
    "exit_iv",
    "actual_pnl",
    "attr_delta",
    "attr_theta",
    "attr_vega",
    "attr_residual",
    "autopsy_note",
]

_JOURNAL_DEFAULTS: dict[str, object] = {
    "contracts": 1,
    "delta": 0.0,
    "theta": 0.0,
    "vega": 0.0,
    "iv_at_entry": 0.0,
    "beta": 1.0,
    "entry_dte": 0,
    "closed_at": "",
    "exit_bid": 0.0,
    "exit_spot": 0.0,
    "exit_iv": 0.0,
    "actual_pnl": 0.0,
    "attr_delta": 0.0,
    "attr_theta": 0.0,
    "attr_vega": 0.0,
    "attr_residual": 0.0,
    "autopsy_note": "",
}


def journal_path():
    from pathlib import Path

    return Path(__file__).resolve().parents[1] / JOURNAL_FILENAME


def _empty_journal() -> pd.DataFrame:
    return pd.DataFrame(columns=JOURNAL_COLUMNS)


def _normalize_journal(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in JOURNAL_COLUMNS:
        if col not in out.columns:
            out[col] = _JOURNAL_DEFAULTS.get(col, "")
    return out[JOURNAL_COLUMNS]


def load_journal() -> pd.DataFrame:
    if "paper_journal" not in st.session_state:
        path = journal_path()
        if path.is_file():
            try:
                st.session_state.paper_journal = _normalize_journal(pd.read_csv(path))
            except Exception:
                st.session_state.paper_journal = _empty_journal()
        else:
            st.session_state.paper_journal = _empty_journal()
    return st.session_state.paper_journal


def save_journal(df: pd.DataFrame) -> None:
    normalized = _normalize_journal(df)
    st.session_state.paper_journal = normalized
    try:
        normalized.to_csv(journal_path(), index=False)
    except OSError:
        pass


def append_paper_trade(
    row: pd.Series,
    spot: float,
    sector: str = "",
    *,
    beta: float = 1.0,
) -> None:
    df = load_journal()
    cost = float(row.get("size_total_cost") or row.get("total_cost") or 0)
    if cost <= 0:
        cost = float(row.get("ask", 0)) * 100

    contracts = int(float(row.get("size_contracts") or 1))
    if contracts < 1:
        contracts = 1

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
        "contracts": contracts,
        "delta": float(row.get("delta") or 0),
        "theta": float(row.get("theta") or 0),
        "vega": float(row.get("vega") or 0),
        "iv_at_entry": float(row.get("iv") or 0),
        "beta": float(beta or 1.0),
        "entry_dte": int(float(row.get("dte") or 0)),
    }
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    save_journal(df)


def close_paper_trade(index: int) -> tuple[bool, str]:
    df = load_journal()
    if index < 0 or index >= len(df):
        return False, "Invalid trade index."

    row = df.iloc[index]
    if str(row.get("status", "")).lower() != "open":
        return False, "Trade is already closed."

    ticker = str(row["ticker"]).upper()
    strike = float(row["strike"])
    expiration = str(row["expiration"])

    try:
        spot_exit = get_spot_price(ticker)
        quote = get_call_quote(ticker, strike, expiration)
        exit_bid = float(quote.get("bid") or quote.get("ask") or quote.get("last") or 0)
        exit_iv = float(quote.get("iv") or row.get("iv_at_entry") or 0.3)
    except Exception as exc:
        if is_rate_limit_error(exc):
            return False, "Yahoo rate limit — wait and retry."
        return False, f"Could not fetch exit quote: {exc}"

    if exit_bid <= 0:
        return False, "No valid exit bid from Yahoo — try again later."

    attr = attribute_long_call_pnl(
        entry_ask=float(row["entry_ask"]),
        exit_bid=exit_bid,
        spot_entry=float(row["spot_at_entry"]),
        spot_exit=spot_exit,
        iv_entry=float(row.get("iv_at_entry") or 0.3),
        iv_exit=exit_iv,
        delta_entry=float(row.get("delta") or 0),
        theta_entry=float(row.get("theta") or 0),
        vega_entry=float(row.get("vega") or 0),
        contracts=int(float(row.get("contracts") or 1)),
        logged_at=str(row.get("logged_at", "")),
    )

    df.at[index, "status"] = "closed"
    df.at[index, "closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df.at[index, "exit_bid"] = exit_bid
    df.at[index, "exit_spot"] = spot_exit
    df.at[index, "exit_iv"] = exit_iv
    df.at[index, "actual_pnl"] = attr.actual_pnl
    df.at[index, "attr_delta"] = attr.delta_pnl
    df.at[index, "attr_theta"] = attr.theta_pnl
    df.at[index, "attr_vega"] = attr.vega_pnl
    df.at[index, "attr_residual"] = attr.residual_pnl
    df.at[index, "autopsy_note"] = attr.summary_line()
    save_journal(df)
    return True, (
        f"Closed {ticker} ${strike:g} — P&L ${attr.actual_pnl:+,.0f} over {attr.days_held}d. "
        f"{attr.summary_line()}"
    )


def open_trades_risk_total() -> float:
    df = load_journal()
    open_df = open_journal_trades(df)
    if open_df.empty:
        return 0.0
    losses = pd.to_numeric(open_df["mc_p95_loss"], errors="coerce").fillna(0)
    return float(losses.sum())


def compute_mirror_exposure() -> tuple[float, list[dict[str, float | str]]]:
    open_df = open_journal_trades(load_journal())
    if open_df.empty:
        return 0.0, []
    try:
        spy_price = get_spot_price("SPY")
    except Exception:
        spy_price = 0.0
    if spy_price <= 0:
        return 0.0, []

    live_spots: dict[str, float] = {}
    for ticker in open_df["ticker"].astype(str).str.upper().unique():
        try:
            live_spots[ticker] = get_spot_price(ticker)
        except Exception:
            continue

    return beta_weighted_spy_shares(open_df, spy_price, live_spots=live_spots)


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


def render_mirror_check(*, in_sidebar: bool = False) -> None:
    """Beta-weighted SPY equivalent exposure for open journal positions."""
    spy_equiv, legs = compute_mirror_exposure()
    open_df = open_journal_trades(load_journal())
    open_count = len(open_df)

    container = st.sidebar if in_sidebar else st
    if in_sidebar:
        container.markdown("**Mirror Check**")
    else:
        container.subheader("Mirror Check")

    if open_count == 0:
        container.caption("No open paper trades — SPY-equivalent exposure is 0.")
        return

    container.metric(
        "SPY-equivalent shares",
        f"{spy_equiv:,.0f}",
        help="Sum of delta × contracts × 100 × spot × beta / SPY price across open calls.",
    )

    warn = exposure_warning(spy_equiv)
    if warn:
        container.warning(warn)
    else:
        container.caption(
            f"{open_count} open leg(s) — beta-weighted market exposure translated to SPY shares."
        )

    if legs:
        leg_df = pd.DataFrame(legs)
        with container.expander("Per-ticker breakdown", expanded=False):
            container.dataframe(leg_df, use_container_width=True, hide_index=True)


def render_risk_dashboard(bankroll: float) -> bool:
    """Show cumulative exposure; return True if new trades are locked."""
    total = open_trades_risk_total()
    cap = bankroll * ACCOUNT_RISK_LOCK_PCT if bankroll > 0 else 0
    df = load_journal()
    open_count = len(open_journal_trades(df))

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

    render_mirror_check(in_sidebar=False)

    if not df.empty:
        with st.expander("Paper trade journal", expanded=False):
            st.dataframe(df.tail(20), use_container_width=True, hide_index=True)
            _render_close_trade_ui(df)
            st.download_button(
                "Download journal (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                file_name=JOURNAL_FILENAME,
                mime="text/csv",
                key="download_journal",
            )
    return locked


def _trade_label(row: pd.Series) -> str:
    return (
        f"{row['ticker']} ${float(row['strike']):g} exp {str(row['expiration'])[:10]} "
        f"(logged {str(row['logged_at'])[:16]})"
    )


def _render_close_trade_ui(df: pd.DataFrame) -> None:
    open_df = open_journal_trades(df)
    if open_df.empty:
        return

    st.markdown("**Autopsy Engine — close a paper trade**")
    st.caption(
        "Fetches live bid/spot/IV and splits your P&L into Direction (Delta), "
        "Time (Theta), and Volatility (Vega)."
    )

    labels = [_trade_label(row) for _, row in open_df.iterrows()]
    indices = list(open_df.index)
    choice = st.selectbox(
        "Open trade to close",
        options=range(len(labels)),
        format_func=lambda i: labels[i],
        key="journal_close_pick",
    )

    if st.button("Close trade & run autopsy", key="journal_close_btn", type="primary"):
        ok, message = close_paper_trade(indices[choice])
        if ok:
            st.success(message)
        else:
            st.error(message)
        st.rerun()


def render_execute_button(
    row: pd.Series,
    spot: float,
    *,
    sector: str = "",
    beta: float = 1.0,
    button_key: str,
    locked: bool,
) -> None:
    if locked:
        st.button("Execute Paper Trade (locked)", key=button_key, disabled=True)
        return
    if st.button("Execute Paper Trade", key=button_key, type="secondary"):
        append_paper_trade(row, spot, sector=sector, beta=beta)
        st.success(f"Logged {row.get('ticker')} ${row['strike']} call to journal.")
        st.rerun()
