"""Streamlit entry point for the Options Call Screener."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from screener import run_scan
from ui.results import render_header, render_results
from ui.sidebar import render_sidebar
from ui.sizing_sandbox import render_sizing_sandbox

APP_VERSION = "3.3.0"
APP_ROOT = str(ROOT)

st.set_page_config(
    page_title="Options Call Screener",
    page_icon="📈",
    layout="wide",
)


def main() -> None:
    render_header(app_version=APP_VERSION, app_root=APP_ROOT)
    render_sizing_sandbox(expanded=True)

    config = render_sidebar()
    if config is None:
        st.info("Configure settings in the sidebar, then click **Analyze Market Opportunities**.")
        return

    progress = st.progress(0.0, text="Starting scan...")
    output = run_scan(config)
    progress.progress(1.0, text="Complete")
    progress.empty()
    if hasattr(output, "results"):
        render_results(output.results, macro=output.macro)
    else:
        render_results(output)


if __name__ == "__main__":
    main()
