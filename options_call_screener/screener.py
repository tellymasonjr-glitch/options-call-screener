"""Orchestrates the full scan pipeline for one or more tickers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from analytics.filters import passes_0dte_filters, passes_hard_filters
from analytics.scalper import (
    build_scalper_rationale,
    score_0dte_contracts,
    tag_scalper_picks,
)
from analytics.scoring import build_rationale, score_contracts, tag_picks
from analytics.macro import MacroEnvironment, build_macro_environment
from analytics.position_sizing import apply_sizing_to_picks
from analytics.stock_profile import StockProfile, build_stock_profile
from analytics.volatility import collect_iv_samples, iv_rank as calc_iv_rank
from config import DELTA_BOUNDS, DELTA_BOUNDS_0DTE, CONVICTION_MIN_DTE, DEFAULT_BASE_RISK_PCT, SCAN_TICKER_DELAY_SEC
from data.cached_fetch import fetch_call_contracts, fetch_earnings, fetch_news, get_price_history
from data.earnings import expiration_near_earnings, upcoming_earnings_dates
from data.news_data import analyze_sentiment


@dataclass
class ScanConfig:
    tickers: list[str]
    max_budget: float
    min_dte: int
    max_dte: int
    risk_profile: str
    avoid_earnings: bool
    picks_per_ticker: int
    bankroll: float = 0.0
    base_risk_pct: float = DEFAULT_BASE_RISK_PCT
    enable_position_sizing: bool = True


@dataclass
class TickerResult:
    ticker: str
    spot: float
    hv_30: float
    trend_up: bool
    sentiment: dict[str, float]
    profile: StockProfile | None = None
    picks: pd.DataFrame = field(default_factory=pd.DataFrame)
    scalper_picks: pd.DataFrame = field(default_factory=pd.DataFrame)
    error: str | None = None
    contracts_scanned: int = 0
    contracts_passed: int = 0
    contracts_scanned_0dte: int = 0
    contracts_passed_0dte: int = 0


@dataclass
class ScanOutput:
    results: list[TickerResult]
    macro: MacroEnvironment


def scan_ticker(
    config: ScanConfig,
    ticker: str,
    spy_history: pd.DataFrame | None = None,
    macro: MacroEnvironment | None = None,
) -> TickerResult:
    ticker = ticker.upper().strip()

    try:
        history = get_price_history(ticker)
        profile = build_stock_profile(ticker, history, spy_history)
        spot = profile.spot
        hv_30 = profile.hv_30
        trend_up = profile.above_sma_20

        articles = fetch_news(ticker)
        sentiment = analyze_sentiment(ticker, articles)

        earnings = fetch_earnings(ticker) if config.avoid_earnings else []
        earn_dates = upcoming_earnings_dates(ticker, earnings) if config.avoid_earnings else []

        include_0dte = config.min_dte == 0
        conviction_min = CONVICTION_MIN_DTE if include_0dte else max(config.min_dte, 1)
        conviction_max = config.max_dte

        raw_contracts: list[dict[str, Any]] = []
        if conviction_min <= conviction_max:
            raw_contracts = fetch_call_contracts(
                ticker, conviction_min, conviction_max, spot
            )
        iv_samples = collect_iv_samples(raw_contracts)

        delta_min, delta_max = DELTA_BOUNDS.get(
            config.risk_profile, DELTA_BOUNDS["moderate"]
        )

        filtered: list[dict[str, Any]] = []
        for contract in raw_contracts:
            if config.avoid_earnings and expiration_near_earnings(
                contract["expiration"], earn_dates
            ):
                continue

            rank = calc_iv_rank(float(contract.get("iv", 0) or 0), iv_samples)
            ok, _reason = passes_hard_filters(
                contract, config.max_budget, delta_min, delta_max, rank
            )
            if ok:
                filtered.append(contract)

        scored = score_contracts(
            filtered,
            spot,
            hv_30,
            trend_up,
            sentiment,
            iv_samples,
            profile=profile,
            macro_multiplier=macro.macro_multiplier if macro else 1.0,
        )
        if macro and macro.hard_block:
            picks = pd.DataFrame()
        else:
            picks = tag_picks(scored, config.max_budget, config.picks_per_ticker)

        if not picks.empty:
            picks["scan_mode"] = "conviction"
            picks["ticker"] = ticker
            if config.enable_position_sizing and config.bankroll > 0:
                picks = apply_sizing_to_picks(picks, config.bankroll, config.base_risk_pct)
            picks["rationale"] = picks.apply(
                lambda row: build_rationale(
                    row, spot, sentiment, profile,
                    vix_hint=macro.vix if macro else None,
                ),
                axis=1,
            )

        scalper_picks = pd.DataFrame()
        scanned_0dte = 0
        passed_0dte = 0
        if include_0dte:
            raw_0dte = fetch_call_contracts(ticker, 0, 0, spot)
            scanned_0dte = len(raw_0dte)
            delta_0dte_min, delta_0dte_max = DELTA_BOUNDS_0DTE
            filtered_0dte: list[dict[str, Any]] = []
            for contract in raw_0dte:
                ok, _reason = passes_0dte_filters(
                    contract, config.max_budget, delta_0dte_min, delta_0dte_max
                )
                if ok:
                    filtered_0dte.append(contract)
            passed_0dte = len(filtered_0dte)
            scored_0dte = score_0dte_contracts(filtered_0dte, spot, profile)
            scalper_picks = tag_scalper_picks(scored_0dte, config.picks_per_ticker)
            if not scalper_picks.empty:
                scalper_picks["rationale"] = scalper_picks.apply(
                    lambda row: build_scalper_rationale(row, spot, profile), axis=1
                )

        return TickerResult(
            ticker=ticker,
            spot=spot,
            hv_30=hv_30,
            trend_up=trend_up,
            sentiment=sentiment,
            profile=profile,
            picks=picks,
            scalper_picks=scalper_picks,
            contracts_scanned=len(raw_contracts),
            contracts_passed=len(filtered),
            contracts_scanned_0dte=scanned_0dte,
            contracts_passed_0dte=passed_0dte,
        )
    except Exception as exc:
        return TickerResult(
            ticker=ticker, spot=0, hv_30=0, trend_up=False, sentiment={}, error=str(exc)
        )


def run_scan(config: ScanConfig, progress=None) -> ScanOutput:
    spy_history = get_price_history("SPY")
    macro = build_macro_environment(spy_history)
    results: list[TickerResult] = []
    tickers = config.tickers
    total = len(tickers)

    for i, ticker in enumerate(tickers):
        if progress is not None:
            progress.progress(
                i / max(total, 1),
                text=f"Scanning {ticker} ({i + 1} of {total})...",
            )
        if i > 0:
            time.sleep(SCAN_TICKER_DELAY_SEC)
        results.append(scan_ticker(config, ticker, spy_history, macro))

    return ScanOutput(results=results, macro=macro)
