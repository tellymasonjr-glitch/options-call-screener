"""Equity quotes, historicals, and options chains via Yahoo Finance (no login)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

from analytics.greeks import call_greeks
from data.trading_calendar import market_today
from data.yf_utils import call_with_retry


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _ticker_obj(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.upper().strip())


def get_spot_price(ticker: str) -> float:
    t = _ticker_obj(ticker)

    def _fetch() -> float:
        price = _to_float(
            t.fast_info.get("lastPrice") or t.fast_info.get("regularMarketPrice")
        )
        if price <= 0:
            hist = t.history(period="5d")
            if hist.empty:
                raise RuntimeError(f"No quote data for {ticker}")
            price = float(hist["Close"].iloc[-1])
        return price

    return call_with_retry(_fetch)


def get_price_history(ticker: str) -> pd.DataFrame:
    t = _ticker_obj(ticker)

    def _fetch() -> pd.DataFrame:
        hist = t.history(period="1y", interval="1d", auto_adjust=True)
        if hist.empty:
            raise RuntimeError(f"No historical data for {ticker}")

        df = hist.reset_index()
        df = df.rename(
            columns={
                "Date": "date",
                "Close": "close",
                "High": "high",
                "Low": "low",
                "Volume": "volume",
            }
        )
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        return (
            df[["date", "close", "high", "low", "volume"]]
            .sort_values("date")
            .reset_index(drop=True)
        )

    return call_with_retry(_fetch)


def dte_from_expiration(expiration: str) -> int:
    exp_date = datetime.strptime(expiration[:10], "%Y-%m-%d").date()
    return (exp_date - market_today()).days


def list_near_term_expirations(ticker: str, max_dte: int = 14) -> list[tuple[str, int]]:
    """Return (expiration, dte) pairs for diagnostics when same-day chain is empty."""
    t = _ticker_obj(ticker)

    def _load_expirations() -> list[str]:
        return list(t.options or [])

    try:
        expirations = call_with_retry(_load_expirations, base_delay_sec=3.0)
    except Exception:
        return []

    out: list[tuple[str, int]] = []
    for exp in expirations:
        dte = dte_from_expiration(exp)
        if 0 <= dte <= max_dte:
            out.append((exp[:10], dte))
    return sorted(out, key=lambda x: x[1])


def fetch_call_contracts(
    ticker: str,
    min_dte: int,
    max_dte: int,
    spot: float | None = None,
) -> list[dict[str, Any]]:
    """Fetch call contracts within DTE window; Greeks computed when missing."""
    t = _ticker_obj(ticker)
    if spot is None:
        spot = get_spot_price(ticker)

    def _load_expirations() -> list[str]:
        return list(t.options or [])

    try:
        expirations = call_with_retry(_load_expirations, base_delay_sec=4.0)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load options expirations for {ticker}: {exc}"
        ) from exc

    contracts: list[dict[str, Any]] = []

    for exp in expirations:
        dte = dte_from_expiration(exp)
        if dte < 0 or dte < min_dte or dte > max_dte:
            continue

        def _load_chain(expiration: str = exp):
            return t.option_chain(expiration)

        try:
            chain = call_with_retry(_load_chain, base_delay_sec=4.0)
        except Exception:
            continue

        calls = chain.calls
        if calls is None or calls.empty:
            continue

        for _, row in calls.iterrows():
            ask = _to_float(row.get("ask"))
            bid = _to_float(row.get("bid"))
            if ask <= 0:
                ask = _to_float(row.get("lastPrice"))
            if bid <= 0 and ask > 0:
                bid = ask * 0.98

            strike = _to_float(row.get("strike"))
            iv = _to_float(row.get("impliedVolatility"))
            if iv <= 0:
                iv = 0.30

            greeks = call_greeks(spot, strike, dte, iv)

            contracts.append(
                {
                    "ticker": ticker.upper(),
                    "option_id": str(row.get("contractSymbol", "")),
                    "expiration": exp,
                    "dte": dte,
                    "strike": strike,
                    "bid": bid,
                    "ask": ask,
                    "mark": _to_float(row.get("lastPrice")),
                    "delta": greeks["delta"],
                    "gamma": greeks["gamma"],
                    "theta": greeks["theta"],
                    "vega": greeks["vega"],
                    "iv": iv,
                    "open_interest": int(_to_float(row.get("openInterest"))),
                    "volume": int(_to_float(row.get("volume"))),
                }
            )

    return contracts


def get_call_quote(ticker: str, strike: float, expiration: str) -> dict[str, float]:
    """Look up bid/ask/last for one call contract."""
    t = _ticker_obj(ticker)
    exp = expiration[:10]

    def _load_chain():
        return t.option_chain(exp)

    try:
        chain = call_with_retry(_load_chain)
    except Exception as exc:
        raise RuntimeError(
            f"Could not load options for {ticker} exp {exp}: {exc}"
        ) from exc

    calls = chain.calls
    if calls is None or calls.empty:
        raise RuntimeError(f"No call chain for {ticker} exp {exp}")

    match = calls[(calls["strike"] - strike).abs() < 0.01]
    if match.empty:
        raise RuntimeError(f"No ${strike:g} strike found for {ticker} exp {exp}")

    row = match.iloc[0]
    ask = _to_float(row.get("ask"))
    bid = _to_float(row.get("bid"))
    last = _to_float(row.get("lastPrice"))
    if ask <= 0:
        ask = last
    if bid <= 0 and ask > 0:
        bid = ask * 0.98
    iv = _to_float(row.get("impliedVolatility"))
    if iv <= 0:
        iv = 0.30
    return {"ask": ask, "bid": bid, "last": last, "iv": iv}
