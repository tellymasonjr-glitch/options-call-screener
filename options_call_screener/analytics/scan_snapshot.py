"""Scan snapshot capture — timestamped JSON record of top picks and macro context."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import pandas as pd

from analytics.macro import MacroEnvironment

if TYPE_CHECKING:
    from screener import ScanOutput, TickerResult


def _safe_float(val: object, default: float = 0.0) -> float:
    try:
        out = float(val)
        if pd.isna(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def _pick_payload(row: pd.Series, ticker: str, profile_garch: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "strike": _safe_float(row.get("strike")),
        "expiration": str(row.get("expiration", ""))[:10],
        "ask": _safe_float(row.get("ask")),
        "dte": int(_safe_float(row.get("dte"))),
        "conviction_score": _safe_float(row.get("conviction_score")),
        "display_confidence": _safe_float(row.get("display_confidence")),
        "ev": _safe_float(row.get("ev")),
        "prob_itm": _safe_float(row.get("prob_itm")),
        "iv_rank": _safe_float(row.get("iv_rank")),
        "effective_hv": _safe_float(row.get("effective_hv") or profile_garch.get("effective_hv")),
        "garch_vol_5d": _safe_float(row.get("garch_vol_5d") or profile_garch.get("garch_vol_5d")),
        "garch_regime": str(row.get("garch_regime") or profile_garch.get("garch_regime") or "neutral"),
        "mc_p95_loss": _safe_float(row.get("mc_p95_loss")),
        "mc_prob_profit": _safe_float(row.get("mc_prob_profit")),
        "tag": str(row.get("tag") or ""),
    }


def _garch_payload(result: TickerResult) -> dict[str, Any]:
    if result.profile is None:
        return {}
    p = result.profile
    return {
        "spot": round(p.spot, 4),
        "hv_30": round(p.hv_30, 4),
        "effective_hv": round(p.effective_hv, 4),
        "garch_vol_5d": round(p.garch_vol_5d, 4),
        "garch_hv_ratio": round(p.garch_hv_ratio, 4),
        "garch_regime": p.garch_regime,
        "garch_available": p.garch_available,
    }


def _macro_indices() -> dict[str, float]:
    from data.cached_fetch import get_spot_price

    indices: dict[str, float] = {}
    for sym in ("SPY", "QQQ", "IWM"):
        try:
            indices[sym] = round(float(get_spot_price(sym)), 2)
        except Exception:
            continue
    return indices


def build_scan_snapshot(
    output: ScanOutput,
    *,
    app_version: str,
    tickers_requested: list[str] | None = None,
    top_n: int = 3,
) -> dict[str, Any]:
    """Build a JSON-serializable snapshot from a completed scan."""
    macro = output.macro
    garch_by_ticker = {r.ticker: _garch_payload(r) for r in output.results if r.error is None}

    candidates: list[tuple[float, pd.Series, str, dict[str, Any]]] = []
    for result in output.results:
        if result.error or result.picks.empty:
            continue
        garch = garch_by_ticker.get(result.ticker, {})
        for _, row in result.picks.iterrows():
            score = _safe_float(row.get("conviction_score"))
            candidates.append((score, row, result.ticker, garch))

    candidates.sort(key=lambda x: x[0], reverse=True)
    top_picks = [_pick_payload(row, ticker, garch) for _, row, ticker, garch in candidates[:top_n]]

    return {
        "snapshot_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "app_version": app_version,
        "tickers_requested": tickers_requested or [r.ticker for r in output.results],
        "tickers_scanned": len(output.results),
        "macro": {
            "vix": round(macro.vix, 2),
            "spy_spot": round(macro.spy_spot, 2),
            "spy_sma_20": round(macro.spy_sma_20, 2),
            "spy_above_sma_20": macro.spy_above_sma_20,
            "macro_multiplier": round(macro.macro_multiplier, 3),
            "traffic_light": macro.traffic_light,
            "headline": macro.headline,
            "indices": _macro_indices(),
        },
        "garch_by_ticker": garch_by_ticker,
        "top_picks": top_picks,
    }


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, default=str)


def snapshot_filename(snapshot: dict[str, Any]) -> str:
    sid = snapshot.get("snapshot_id", "scan")
    return f"scan_snapshot_{sid}.json"
