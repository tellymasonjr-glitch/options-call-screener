"""Streamlit entry point for the Options Call Screener."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from screener import run_scan
from ui.auth import check_pin
from ui.results import render_header, render_results
from ui.sidebar import render_sidebar
from ui.sizing_sandbox import render_sizing_sandbox

APP_VERSION = "3.4.3"
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
    render_sizing_sandbox(expanded=True)

    config = render_sidebar()
    if config is None:
        st.info(
            "Set up your scan in the sidebar, then click **Scan for Trading Ideas**. "
            "Use the Risk Manager above to practice position sizes first."
        )
        return

    progress = st.progress(0.0, text="Scanning the market...")
    output = run_scan(config)
    progress.progress(1.0, text="Done!")
    progress.empty()
    if hasattr(output, "results"):
        render_results(output.results, macro=output.macro)
    else:
        render_results(output)


if __name__ == "__main__":
    main()
