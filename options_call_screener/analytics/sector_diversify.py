"""Echo Chamber Guard — penalize duplicate sectors in a batch scan."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config import SECTOR_PENALTY_MULT

if TYPE_CHECKING:
    from screener import TickerResult


def apply_sector_diversification(
    results: list[TickerResult],
    sectors: dict[str, str],
) -> list[TickerResult]:
    """First stock in a sector keeps full score; duplicates get penalized."""
    sector_order: dict[str, int] = {}

    for result in results:
        sector = sectors.get(result.ticker, "Unknown")
        result.sector = sector
        if result.picks.empty:
            continue

        picks = result.picks.copy()
        picks["sector"] = sector
        mults = []
        for _ in range(len(picks)):
            idx = sector_order.get(sector, 0)
            sector_order[sector] = idx + 1
            mults.append(SECTOR_PENALTY_MULT ** idx)

        picks["sector_mult"] = mults
        for col in ("conviction_score", "display_confidence"):
            if col in picks.columns:
                picks[col] = (picks[col].astype(float) * picks["sector_mult"]).clip(0, 100)
        result.picks = picks

    return results
