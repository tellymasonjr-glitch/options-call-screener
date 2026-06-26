"""Streamlit entry point for the Options Call Screener."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from analytics.scan_snapshot import build_scan_snapshot
from data.yf_utils import is_rate_limit_error
from screener import run_scan
from ui.auth import check_pin
from ui.education import render_engine_guide
from ui.exit_checker import render_exit_checker
from ui.results import render_header, render_results
from ui.sidebar import render_sidebar
from ui.sizing_sandbox import render_sizing_sandbox
from config import DEFAULT_BANKROLL
from ui.snapshot_bar import render_scan_snapshot_bar
from ui.trade_journal import render_risk_dashboard

APP_VERSION = "5.5.0"
APP_ROOT = str(ROOT)

st.set_page_config(
    page_title="Smart Trade Idea Scanner",
    page_icon="📈",
    layout="wide",
)


def main() -> None:
    if not check_pin():
        st.stop()

    render_header(app_version=APP_VERSION, app_root=APP_ROOT)
    render_engine_guide()
    render_sizing_sandbox(expanded=True)
    bankroll = float(st.session_state.get("sandbox_bankroll", DEFAULT_BANKROLL))
    execution_locked = render_risk_dashboard(bankroll)
    st.session_state["execution_locked"] = execution_locked
    render_exit_checker(expanded=False)

    config = render_sidebar()

    # Only run a fresh scan when the Scan button was actually pressed this run.
    # Otherwise re-render the last scan from session_state so unrelated widget
    # interactions (e.g. the Deep Dive ticker selector) don't wipe the results.
    if config is not None:
        progress = st.progress(0.0, text="Starting scan...")
        try:
            output = run_scan(config, progress=progress)
        except Exception as exc:
            progress.empty()
            if is_rate_limit_error(exc):
                st.error("Yahoo Finance rate limit reached — too many data requests at once.")
                st.info(
                    "**What to do:** Scan **5 or fewer tickers**, wait **2–3 minutes**, then tap "
                    "**Scan** again. Results are cached for **10 minutes**. Run a second batch "
                    "(HOOD, INTC, PFE, MARA, WBD) after the first finishes."
                )
                return
            raise
        progress.progress(1.0, text="Done!")
        progress.empty()

        results = output.results if hasattr(output, "results") else output
        macro = output.macro if hasattr(output, "macro") else None
        snapshot = (
            build_scan_snapshot(output, app_version=APP_VERSION, tickers_requested=config.tickers)
            if hasattr(output, "results")
            else None
        )

        if snapshot is not None:
            st.session_state.latest_scan_snapshot = snapshot
            history = list(st.session_state.get("scan_snapshots", []))
            history.insert(0, snapshot)
            st.session_state.scan_snapshots = history[:20]

        # Drop a stale Deep Dive selection so the new scan's options stay valid.
        valid_tickers = [r.ticker for r in results]
        if st.session_state.get("deep_dive_ticker") not in valid_tickers:
            st.session_state.pop("deep_dive_ticker", None)

        st.session_state.last_scan = {
            "results": results,
            "macro": macro,
            "snapshot": snapshot,
        }

    last_scan = st.session_state.get("last_scan")
    if last_scan is None:
        st.info(
            "Set up your scan in the sidebar, then click **Scan for Trading Ideas**. "
            "Use the Risk Manager above to practice sizes, or **Exit Check** if you're "
            "already in a paper trade."
        )
        return

    if last_scan.get("snapshot") is not None:
        render_scan_snapshot_bar(last_scan["snapshot"])
    render_results(
        last_scan["results"],
        macro=last_scan.get("macro"),
        execution_locked=execution_locked,
    )


if __name__ == "__main__":
    main()
