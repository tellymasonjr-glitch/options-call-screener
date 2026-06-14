"""Streamlit results rendering."""

from __future__ import annotations

import plotly.express as px
import pandas as pd
import streamlit as st

from config import DISCLAIMER
from analytics.macro import MacroEnvironment
from screener import TickerResult

DISPLAY_COLS = [
    "tag",
    "expiration",
    "strike",
    "ask",
    "total_cost",
    "dte",
    "prob_itm",
    "delta",
    "bs_fair_hv",
    "edge_pct",
    "iv_hv_ratio",
    "iv_rank",
    "ev",
    "risk_reward",
    "breakeven",
    "open_interest",
    "volume",
    "spread_pct",
    "conviction_score",
]

SCALPER_DISPLAY_COLS = [
    "tag",
    "expiration",
    "strike",
    "ask",
    "total_cost",
    "dte",
    "delta",
    "gamma",
    "volume",
    "open_interest",
    "spread_pct",
    "iv_hv_ratio",
    "scalper_score",
]



def _combine_ranked_picks(results: list[TickerResult]) -> pd.DataFrame:
    """Merge all ticker picks into one list sorted best → worst by conviction."""
    frames = []
    for r in results:
        if r.error or r.picks.empty:
            continue
        df = r.picks.copy()
        df["ticker"] = r.ticker
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("conviction_score", ascending=False)
    combined = combined.drop_duplicates(
        subset=["ticker", "strike", "expiration"], keep="first"
    )
    combined = combined.sort_values("conviction_score", ascending=False).reset_index(drop=True)
    combined.insert(0, "rank", range(1, len(combined) + 1))
    return combined


def _combine_scalper_picks(results: list[TickerResult]) -> pd.DataFrame:
    frames = []
    for r in results:
        if r.error or r.scalper_picks.empty:
            continue
        df = r.scalper_picks.copy()
        df["ticker"] = r.ticker
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("scalper_score", ascending=False)
    combined = combined.drop_duplicates(
        subset=["ticker", "strike", "expiration"], keep="first"
    )
    combined = combined.sort_values("scalper_score", ascending=False).reset_index(drop=True)
    combined.insert(0, "rank", range(1, len(combined) + 1))
    return combined


def _format_exp_short(expiration: str) -> str:
    dt = pd.to_datetime(expiration)
    return f"{dt.month}/{dt.day}"


def _format_strike(strike: float) -> str:
    return str(int(strike)) if strike == int(strike) else f"{strike:g}"


def render_simple_pick_list(ranked: pd.DataFrame, *, title: str, suffix: str = "") -> None:
    """Standalone simple list under download: 1. XLF buy/call 55 7/18"""
    st.subheader(title)

    if ranked.empty:
        st.caption("No picks in this mode.")
        return

    for _, row in ranked.iterrows():
        line = (
            f"{int(row['rank'])}. {row['ticker']} buy/call "
            f"{_format_strike(float(row['strike']))} "
            f"{_format_exp_short(str(row['expiration']))}{suffix}"
        )
        st.markdown(line)


def render_bottom_results(
    ranked: pd.DataFrame,
    scalper_ranked: pd.DataFrame,
    *,
    include_0dte: bool,
) -> None:
    """Download + simple lists — always at the bottom after ticker tabs."""
    st.divider()
    st.subheader("Results")

    if ranked.empty and scalper_ranked.empty:
        st.info("No buy calls matched your filters. Try widening budget, DTE, or risk profile.")
        if include_0dte:
            st.caption("0 DTE scalper mode was on — many same-day contracts fail volume/spread filters.")
        return

    if not ranked.empty:
        st.download_button(
            "Download conviction results CSV",
            ranked.to_csv(index=False).encode("utf-8"),
            file_name="best_buy_calls_conviction.csv",
            mime="text/csv",
            key="download_conviction_csv",
        )
        render_simple_pick_list(ranked, title="Buy Calls — Conviction List")

    if include_0dte:
        st.divider()
        if not scalper_ranked.empty:
            st.download_button(
                "Download 0 DTE scalper CSV",
                scalper_ranked.to_csv(index=False).encode("utf-8"),
                file_name="best_buy_calls_0dte_scalper.csv",
                mime="text/csv",
                key="download_scalper_csv",
            )
        render_simple_pick_list(
            scalper_ranked,
            title="0 DTE Scalper — Simple List",
            suffix=" (0DTE)",
        )


def render_header(app_version: str = "?", app_root: str = "") -> None:
    st.title("Options Call Screener")
    st.caption(
        "Ranked buy-call ideas using Yahoo Finance data (quotes, options chains, news). "
        "No brokerage login required."
    )
    st.success(f"Data source: Yahoo Finance (yfinance) — v{app_version}")
    if app_root:
        st.caption(f"Running from: `{app_root}`")
    st.warning(DISCLAIMER)


def render_macro_environment(macro: MacroEnvironment) -> None:
    """Traffic-light macro header before ticker results."""
    st.subheader("Macro Environment")
    icons = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    icon = icons.get(macro.traffic_light, "⚪")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("VIX", f"{macro.vix:.1f}")
    c2.metric("SPY", f"${macro.spy_spot:.2f}")
    c3.metric("SPY 20d SMA", f"${macro.spy_sma_20:.2f}")
    c4.metric("Macro mult", f"{macro.macro_multiplier:.2f}x")

    if macro.traffic_light == "red":
        st.error(f"{icon} **{macro.headline}**")
    elif macro.traffic_light == "yellow":
        st.warning(f"{icon} **{macro.headline}**")
    else:
        st.success(f"{icon} **{macro.headline}**")
    st.caption(macro.detail)


def render_summary(results: list[TickerResult]) -> None:
    cols = st.columns(len(results))
    for col, result in zip(cols, results):
        with col:
            if result.error:
                st.metric(result.ticker, "Error")
            else:
                sent = result.sentiment.get("mean_compound", 0)
                st.metric(
                    result.ticker,
                    f"${result.spot:.2f}",
                    delta=f"Sentiment {sent:+.2f}",
                )


def _cell_float(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    return float(value)


def _quarantine_chart_data(result: TickerResult) -> dict[str, list]:
    """Extract pure Python lists — no Narwhals/pandas metadata reaches Plotly."""
    chart_df = result.picks
    tickers = (
        chart_df["ticker"].tolist()
        if "ticker" in chart_df.columns
        else [result.ticker] * len(chart_df)
    )

    return {
        "strike": [_cell_float(x) for x in chart_df["strike"].tolist()],
        "conviction": [_cell_float(x) for x in chart_df["conviction_score"].tolist()],
        "dte": [int(_cell_float(x)) for x in chart_df["dte"].tolist()],
        "cost_size": [
            max(5.0, _cell_float(x)) for x in chart_df["total_cost"].tolist()
        ],
        "ticker": [str(x) for x in tickers],
        "expiration": [str(x) for x in chart_df["expiration"].tolist()],
        "ask": [_cell_float(x) for x in chart_df["ask"].tolist()],
        "delta": [_cell_float(x) for x in chart_df["delta"].tolist()],
        "prob_itm": [_cell_float(x) for x in chart_df["prob_itm"].tolist()],
        "iv_rank": [_cell_float(x) for x in chart_df["iv_rank"].tolist()],
    }


def _build_scatter_chart(result: TickerResult) -> px.Figure:
    clean_data = _quarantine_chart_data(result)

    return px.scatter(
        clean_data,
        x="strike",
        y="conviction",
        size="cost_size",
        color="dte",
        labels={
            "strike": "Strike Price ($)",
            "conviction": "Conviction Score (0-100)",
            "cost_size": "Total Cost ($)",
            "dte": "DTE",
        },
        title=f"{result.ticker} — Options Candidates Dynamics",
        hover_data={
            "ticker": True,
            "expiration": True,
            "ask": ":.2f",
            "delta": ":.2f",
            "prob_itm": ":.1%",
            "iv_rank": ":.0f",
        },
    )


def _render_pick_table(df: pd.DataFrame, cols: list[str]) -> None:
    display = df.copy()
    if "prob_itm" in display.columns:
        display["prob_itm"] = display["prob_itm"].map(lambda x: f"{x:.1%}")
    if "edge_pct" in display.columns:
        display["edge_pct"] = display["edge_pct"].map(lambda x: f"{x:+.1%}")
    if "spread_pct" in display.columns:
        display["spread_pct"] = display["spread_pct"].map(lambda x: f"{x:.1%}")

    st.dataframe(
        display[[c for c in cols if c in display.columns]],
        use_container_width=True,
        hide_index=True,
    )


def render_ticker_tab(result: TickerResult) -> None:
    if result.error:
        st.error(f"{result.ticker}: {result.error}")
        return

    profile = result.profile
    if profile:
        st.subheader(f"{result.ticker} — Stock Behavior Profile")
        p = profile
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Profile Score", f"{p.profile_score:.0f}/100")
        c2.metric("RSI (14)", f"{p.rsi_14:.0f}")
        c3.metric("vs SPY (20d)", f"{p.rel_strength_20:+.1%}")
        c4.metric("Beta (60d)", f"{p.beta_60:.2f}")

        st.caption(
            f"HV 30/60/90d: **{p.hv_30:.1%} / {p.hv_60:.1%} / {p.hv_90:.1%}** · "
            f"SMA stack 20/50/200: **{'↑' if p.above_sma_20 else '↓'}/"
            f"{'↑' if p.above_sma_50 else '↓'}/{'↑' if p.above_sma_200 else '↓'}** · "
            f"52w range: **{p.pct_52w_range:.0f}%** · "
            f"Drawdown from high: **{p.drawdown_from_high:.1%}** · "
            f"ROC 20/60d: **{p.roc_20:+.1%}/{p.roc_60:+.1%}** · "
            f"MACD: **{'Bullish' if p.macd_bullish else 'Bearish'}** · "
            f"Volume vs 20d avg: **{p.volume_ratio:.1f}x**"
        )

    st.write(
        f"Conviction scan: **{result.contracts_scanned}** contracts; "
        f"**{result.contracts_passed}** passed filters."
    )
    if result.contracts_scanned_0dte or not result.scalper_picks.empty:
        st.write(
            f"0 DTE scalper: **{result.contracts_scanned_0dte}** contracts; "
            f"**{result.contracts_passed_0dte}** passed scalper filters."
        )

    if result.picks.empty and result.scalper_picks.empty:
        st.info("No contracts matched your filters. Try widening DTE, budget, or risk profile.")
        return

    if not result.picks.empty:
        st.subheader("Conviction picks")
        _render_pick_table(result.picks, DISPLAY_COLS)

        try:
            st.plotly_chart(_build_scatter_chart(result), use_container_width=True)
        except Exception as exc:
            st.error(f"Could not render chart: {exc}")
            st.caption("Try: Streamlit menu (⋮) → Clear cache, then hard refresh (Ctrl+Shift+R).")

        top = result.picks.iloc[0]
        with st.expander("Why this conviction pick?", expanded=True):
            st.write(top.get("rationale", "No rationale available."))

    if not result.scalper_picks.empty:
        st.subheader("0 DTE scalper picks")
        st.caption("Volume/gamma scoring only — not ranked by conviction EV.")
        _render_pick_table(result.scalper_picks, SCALPER_DISPLAY_COLS)
        top_scalper = result.scalper_picks.iloc[0]
        with st.expander("Why this 0 DTE pick?", expanded=False):
            st.write(top_scalper.get("rationale", "No rationale available."))


def render_results(
    results: list[TickerResult],
    macro: MacroEnvironment | None = None,
) -> None:
    if macro is not None:
        render_macro_environment(macro)
    render_summary(results)
    ranked = _combine_ranked_picks(results)
    scalper_ranked = _combine_scalper_picks(results)
    include_0dte = any(r.contracts_scanned_0dte > 0 for r in results)

    tabs = st.tabs([r.ticker for r in results])
    for tab, result in zip(tabs, results):
        with tab:
            render_ticker_tab(result)

    render_bottom_results(ranked, scalper_ranked, include_0dte=include_0dte)
