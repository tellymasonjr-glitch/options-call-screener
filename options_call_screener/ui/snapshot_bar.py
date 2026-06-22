"""Scan snapshot download bar — rendered from app.py so results UI can stay decoupled."""

from __future__ import annotations

import streamlit as st

from analytics.scan_snapshot import snapshot_filename, snapshot_to_json
from ui.copy import HELP_SCAN_SNAPSHOT


def render_scan_snapshot_bar(snapshot: dict) -> None:
    """Download bar for timestamped scan snapshot JSON (Cloud persistence aid)."""
    top = snapshot.get("top_picks") or []
    summary = ", ".join(
        f"{p.get('ticker')} ${p.get('strike', 0):g} ({p.get('conviction_score', 0):.0f})"
        for p in top[:3]
    )
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(
            f"**Scan snapshot** `{snapshot.get('snapshot_id', '')}` — "
            f"top picks: {summary or 'none'}. "
            + HELP_SCAN_SNAPSHOT
        )
    with c2:
        st.download_button(
            "Download snapshot (JSON)",
            snapshot_to_json(snapshot).encode("utf-8"),
            file_name=snapshot_filename(snapshot),
            mime="application/json",
            key="scan_snapshot_download",
            use_container_width=True,
        )
