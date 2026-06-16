"""Streamlit results rendering."""

from __future__ import annotations

from pathlib import Path

import plotly.express as px
import pandas as pd
import streamlit as st

from analytics.macro import MacroEnvironment
from screener import TickerResult
from ui.column_config import CONVICTION_COLUMN_CONFIG, SCALPER_COLUMN_CONFIG
from ui.copy import (
    APP_SUBTITLE,
    APP_TITLE,
    DISCLAIMER_FRIENDLY,
    HELP_BETA,
    HELP_CONVICTION,
    HELP_MACRO_MULT,
    HELP_RSI,
    HELP_SPY,
    HELP_SPY_SMA,
    HELP_TREND_SCORE,
    HELP_VIX,
    HELP_VS_SPY,
    MACRO_INTRO,
    MACRO_TITLE,
    STOCK_HEALTH_INTRO,
    STOCK_HEALTH_TITLE,
)

_TAG_LABELS = {
    "best_overall": "Top pick",
    "best_value": "Best value",
    "best_budget": "Budget-friendly",
    "0dte_best": "Top same-day scalp",
    "0dte_scalper": "Same-day scalp",
}

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
    "size_tier",
    "size_contracts",
    "size_total_cost",
    "size_risk_pct",
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


def _total_cost_dollars(row: pd.Series) -> float:
    contracts = int(row.get("size_contracts", 0) or 0)
    deployed = row.get("size_total_cost")
    if contracts > 0 and deployed is not None and not pd.isna(deployed) and float(deployed) > 0:
        return float(deployed)
    cost = row.get("total_cost")
    if cost is not None and not pd.isna(cost):
        return float(cost)
    return float(row.get("ask", 0) or 0) * 100


def _expected_return_per_contract(row: pd.Series) -> float | None:
    ev = row.get("ev")
    if ev is None or pd.isna(ev):
        return None
    return float(ev)


def _format_expected_return(row: pd.Series) -> str | None:
    """Dollar expected return from BS/HV model (per contract, scaled if sized)."""
    ev_per = _expected_return_per_contract(row)
    if ev_per is None:
        return None
    contracts = int(row.get("size_contracts", 0) or 0)
    if contracts >= 1:
        total = ev_per * contracts
        return (
            f"Expected Return: \\${ev_per:+,.0f}/contract "
            f"(\\${total:+,.0f} at {contracts} contract{'s' if contracts != 1 else ''})"
        )
    return f"Expected Return: \\${ev_per:+,.0f}/contract"


def _pick_confidence(row: pd.Series) -> float | None:
    for key in ("display_confidence", "conviction_score", "raw_conviction", "scalper_score"):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return None


def _format_pick_line(row: pd.Series, *, suffix: str = "", numbered: bool = True) -> str:
    """Paper-trade line; backslash-escape $ so Streamlit markdown does not break spacing."""
    strike = _format_strike(float(row["strike"]))
    expiry = _format_exp_short(str(row["expiration"]))
    cost = _total_cost_dollars(row)
    score = _pick_confidence(row)

    prefix = f"{int(row['rank'])}. " if numbered else ""
    line = (
        f"{prefix}{row['ticker']} — buy call at \\${strike} target, "
        f"expires {expiry}{suffix}"
    )
    if score is not None:
        line += f" · confidence {score:.0f}/100"
    ev_line = _format_expected_return(row)
    if ev_line:
        line += f" · {ev_line}"
    line += f" · Total Cost: \\${cost:,.0f}"
    return line


def render_simple_pick_list(ranked: pd.DataFrame, *, title: str, suffix: str = "") -> None:
    """Simple numbered list for quick logging."""
    st.subheader(title)
    st.caption(
        "**Expected Return** is the model's average profit or loss in dollars per contract "
        "(positive = math says the premium is cheap vs. normal stock swings; negative = overpriced)."
    )

    if ranked.empty:
        st.caption("Nothing matched your filters in this mode.")
        return

    loggable = ranked.copy()
    if "conviction_score" in loggable.columns:
        loggable = loggable.sort_values(
            ["conviction_score", "ev"] if "ev" in loggable.columns else ["conviction_score"],
            ascending=[False, False] if "ev" in loggable.columns else [False],
        ).reset_index(drop=True)
        loggable = loggable.drop(columns=["rank"], errors="ignore")
        loggable.insert(0, "rank", range(1, len(loggable) + 1))

    shown = 0
    for _, row in loggable.iterrows():
        score = _pick_confidence(row)
        if score is not None and score < 1:
            continue
        st.markdown(_format_pick_line(row, suffix=suffix))
        shown += 1

    if shown == 0 and not loggable.empty:
        st.info("No high-confidence ideas in this batch — widen filters or try another ticker group.")

    if "kelly_edge_ok" in ranked.columns and "conviction_score" in ranked.columns:
        demoted = ranked[
            (~ranked["kelly_edge_ok"]) & (ranked["conviction_score"] >= 1)
        ].sort_values("conviction_score", ascending=False)
        if not demoted.empty:
            with st.expander("Lower-edge ideas (Half-Kelly caution — size small or skip)", expanded=False):
                st.caption(
                    "These still show a confidence score, but Kelly sizing suggests minimal or no bankroll risk."
                )
                for i, (_, row) in enumerate(demoted.head(8).iterrows(), start=1):
                    row = row.copy()
                    row["rank"] = i
                    st.markdown(_format_pick_line(row, suffix=suffix))


def render_bottom_results(
    ranked: pd.DataFrame,
    scalper_ranked: pd.DataFrame,
    *,
    include_0dte: bool,
) -> None:
    """Download + simple lists — always at the bottom after ticker tabs."""
    st.divider()
    st.subheader("Today's Best Ideas")

    if ranked.empty and scalper_ranked.empty:
        st.info(
            "No ideas matched your filters. Try raising max cost, widening the time limit, "
            "or switching to a bolder risk setting."
        )
        if include_0dte:
            st.caption(
                "Same-day mode was on — many 0DTE contracts fail volume or spread checks."
            )
        return

    if not ranked.empty:
        st.download_button(
            "Download full results (CSV)",
            ranked.to_csv(index=False).encode("utf-8"),
            file_name="trade_ideas_confidence.csv",
            mime="text/csv",
            key="download_conviction_csv",
        )
        render_simple_pick_list(ranked, title="Quick List — Log These for Paper Trading")

    if include_0dte:
        st.divider()
        if not scalper_ranked.empty:
            st.download_button(
                "Download same-day scalps (CSV)",
                scalper_ranked.to_csv(index=False).encode("utf-8"),
                file_name="trade_ideas_same_day.csv",
                mime="text/csv",
                key="download_scalper_csv",
            )
        render_simple_pick_list(
            scalper_ranked,
            title="Same-Day Scalp List",
            suffix=" (today only)",
        )


def render_header(app_version: str = "?", app_root: str = "") -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.success(f"Live market data via Yahoo Finance · version {app_version}")
    if app_root:
        st.caption(f"Running from: `{app_root}`")
    st.warning(DISCLAIMER_FRIENDLY)

    template_path = Path(__file__).resolve().parents[2] / "paper_trade_log_template.csv"
    if template_path.is_file():
        st.download_button(
            "Download paper-trade log template (Google Sheets)",
            template_path.read_bytes(),
            file_name="paper_trade_log_template.csv",
            mime="text/csv",
            key="download_paper_log_template",
            help="Copy-paste into Google Sheets to track 20–30 paper trades during your test period.",
        )


def render_macro_environment(macro: MacroEnvironment) -> None:
    """Traffic-light market weather before ticker results."""
    st.subheader(MACRO_TITLE)
    st.caption(MACRO_INTRO)
    icons = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    icon = icons.get(macro.traffic_light, "⚪")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Market Fear (VIX)",
        f"{macro.vix:.1f}",
        help=HELP_VIX,
    )
    c2.metric(
        "Overall Market (SPY)",
        f"${macro.spy_spot:.2f}",
        help=HELP_SPY,
    )
    c3.metric(
        "Market Trend (20-day avg)",
        f"${macro.spy_sma_20:.2f}",
        help=HELP_SPY_SMA,
    )
    c4.metric(
        "Safety Haircut",
        f"{macro.macro_multiplier:.2f}x",
        help=HELP_MACRO_MULT,
    )

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
                    delta=f"News tone {sent:+.2f}",
                    help="Stock price now · news tone from recent headlines (-1 negative to +1 positive).",
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
            "strike": "Target Price ($)",
            "conviction": "Confidence Score (0–100)",
            "cost_size": "Total Cost ($)",
            "dte": "Days Left",
        },
        title=f"{result.ticker} — How Each Idea Scores",
        hover_data={
            "ticker": True,
            "expiration": True,
            "ask": ":.2f",
            "delta": ":.2f",
            "prob_itm": ":.1%",
            "iv_rank": ":.0f",
        },
    )


def _render_pick_table(
    df: pd.DataFrame,
    cols: list[str],
    *,
    column_config: dict | None = None,
) -> None:
    display = df.copy()
    if "tag" in display.columns:
        display["tag"] = display["tag"].map(lambda t: _TAG_LABELS.get(str(t), str(t) or ""))
    if "prob_itm" in display.columns:
        display["prob_itm"] = display["prob_itm"].map(lambda x: f"{x:.1%}")
    if "edge_pct" in display.columns:
        display["edge_pct"] = display["edge_pct"].map(lambda x: f"{x:+.1%}")
    if "spread_pct" in display.columns:
        display["spread_pct"] = display["spread_pct"].map(lambda x: f"{x:.1%}")
    if "ev" in display.columns:
        def _fmt_ev(x: object) -> str:
            if x is None or (isinstance(x, float) and pd.isna(x)):
                return "—"
            try:
                return f"${float(x):+,.0f}"
            except (TypeError, ValueError):
                return "—"

        display["ev"] = display["ev"].map(_fmt_ev)

    visible = [c for c in cols if c in display.columns]
    cfg = column_config or {}
    st.dataframe(
        display[visible],
        column_config={k: v for k, v in cfg.items() if k in visible},
        use_container_width=True,
        hide_index=True,
    )


def render_ticker_tab(result: TickerResult) -> None:
    if result.error:
        st.error(f"{result.ticker}: {result.error}")
        return

    profile = result.profile
    if profile:
        st.subheader(f"{result.ticker} — {STOCK_HEALTH_TITLE}")
        st.caption(STOCK_HEALTH_INTRO)
        p = profile
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Trend Health Score",
            f"{p.profile_score:.0f}/100",
            help=HELP_TREND_SCORE,
        )
        c2.metric("Momentum (RSI)", f"{p.rsi_14:.0f}", help=HELP_RSI)
        c3.metric(
            "Strength vs Market",
            f"{p.rel_strength_20:+.1%}",
            help=HELP_VS_SPY,
        )
        c4.metric(
            "Price Swing Risk (Beta)",
            f"{p.beta_60:.2f}",
            help=HELP_BETA,
        )

        trend_short = "Up" if p.above_sma_20 else "Down"
        trend_med = "Up" if p.above_sma_50 else "Down"
        trend_long = "Up" if p.above_sma_200 else "Down"
        st.caption(
            f"**Normal volatility:** {p.hv_30:.1%} / {p.hv_60:.1%} / {p.hv_90:.1%} (30/60/90 days) · "
            f"**Trend (short / med / long):** {trend_short} / {trend_med} / {trend_long} · "
            f"**52-week range position:** {p.pct_52w_range:.0f}% · "
            f"**Drop from recent high:** {p.drawdown_from_high:.1%} · "
            f"**Recent change (20d / 60d):** {p.roc_20:+.1%} / {p.roc_60:+.1%} · "
            f"**Momentum:** {'Buyers winning' if p.macd_bullish else 'Sellers winning'} · "
            f"**Volume vs average:** {p.volume_ratio:.1f}x · "
            f"**Bollinger %B:** {p.tech.pct_b:.2f}"
        )
        st.caption(
            f"**Suggested hard stop-loss (2× ATR):** \\${p.tech.atr_stop_2x:.2f} "
            f"(14-day ATR \\${p.tech.atr_14:.2f})"
        )
        if p.tech.low_volume_breakout:
            st.warning(
                "**Low Volume Breakout Warning** — price is pushing up but today's volume "
                "is below the 20-day average. Breakout may be a trap."
            )
        if p.tech.midrange_chop:
            st.warning(
                "**Mid-range drift** — price is chopping sideways (Bollinger %B 0.30–0.70). "
                "Confidence score is penalized until a clearer breakout or reversal forms."
            )
        t = p.tech
        if t.breakout_confirmed:
            st.success(
                "**Breakout confirmed** — new 20-day high with volume ≥ 1.2× the 20-day average."
            )
        elif t.new_20d_high:
            st.info("At/near a 20-day high — watch for volume confirmation before sizing up.")
        if t.near_52w_high:
            st.info(
                f"**Near 52-week high** — only {t.pct_from_52w_high:.1%} below the high "
                "(HOOD-at-$30 style breakout zone if trend holds)."
            )
        if t.pct_from_round <= 0.03:
            st.info(
                f"**Round-number zone** — within 3% of \\${t.nearest_round:g} "
                "(psychological level traders watch)."
            )
        if t.momentum_accelerating:
            st.caption("Momentum is **accelerating** (5-day pace faster than 20-day trend).")

    st.write(
        f"Longer-term scan: looked at **{result.contracts_scanned}** contracts; "
        f"**{result.contracts_passed}** passed your filters."
    )
    if result.contracts_scanned_0dte or not result.scalper_picks.empty:
        st.write(
            f"Same-day scan: **{result.contracts_scanned_0dte}** contracts; "
            f"**{result.contracts_passed_0dte}** passed quick-scalp filters."
        )

    if result.picks.empty and result.scalper_picks.empty:
        st.info(
            "No contracts matched. Try a higher max cost, wider time limit, or bolder risk setting."
        )
        return

    if not result.picks.empty:
        st.subheader("Ranked Ideas (Confidence Score)")
        st.caption(HELP_CONVICTION)
        _render_pick_table(result.picks, DISPLAY_COLS, column_config=CONVICTION_COLUMN_CONFIG)

        try:
            st.plotly_chart(_build_scatter_chart(result), use_container_width=True)
        except Exception as exc:
            st.error(f"Could not render chart: {exc}")
            st.caption("Try: menu (⋮) → Clear cache, then hard refresh.")

        top = result.picks.iloc[0]
        cal_note = top.get("calendar_note")
        if cal_note and str(cal_note).strip():
            st.caption(f"**Calendar context:** {cal_note}")
        risk_warn = top.get("risk_warnings")
        if risk_warn and str(risk_warn).strip():
            for msg in str(risk_warn).split("|"):
                if msg.strip():
                    st.warning(msg.strip())
        if "size_summary" in top and top.get("size_summary"):
            st.info(f"**Recommended size:** {top['size_summary']}")
        kelly = top.get("half_kelly_pct")
        if kelly is not None and not pd.isna(kelly) and float(kelly) > 0:
            st.caption(
                f"**Quarter-Kelly max bankroll risk** on this contract: {float(kelly):.1f}% "
                "(capped at 3% — sizing uses the lower of tier risk or Kelly)."
            )
        ev = top.get("ev")
        if ev is not None and not pd.isna(ev):
            st.caption(f"**Expected return (1 contract):** \\${float(ev):+,.0f} at expiry (model estimate).")
        with st.expander("Why this idea? (plain English)", expanded=True):
            st.markdown(top.get("rationale", "No explanation available."))

    if not result.scalper_picks.empty:
        st.subheader("Same-Day Scalp Ideas")
        st.caption(
            "Expires today — scored on volume and movement, not long-term confidence. "
            "Much riskier; for experienced users only."
        )
        _render_pick_table(
            result.scalper_picks,
            SCALPER_DISPLAY_COLS,
            column_config=SCALPER_COLUMN_CONFIG,
        )
        top_scalper = result.scalper_picks.iloc[0]
        with st.expander("Why this same-day pick?", expanded=False):
            st.write(top_scalper.get("rationale", "No explanation available."))


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
