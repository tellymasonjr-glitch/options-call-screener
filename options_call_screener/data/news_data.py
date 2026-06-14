"""News retrieval and VADER sentiment via Yahoo Finance."""

from __future__ import annotations

from typing import Any

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import (
    SENTIMENT_BEARISH,
    SENTIMENT_BULLISH,
    SENTIMENT_MULT_BEARISH,
    SENTIMENT_MULT_BULLISH,
    SENTIMENT_MULT_NEUTRAL,
)


def fetch_news(ticker: str) -> list[dict[str, Any]]:
    try:
        raw = yf.Ticker(ticker.upper()).news or []
        return [a for a in raw if isinstance(a, dict)]
    except Exception:
        return []


def _article_text(article: dict[str, Any]) -> str:
    parts = []
    for key in ("title", "summary", "description", "body", "content"):
        value = article.get(key)
        if value:
            parts.append(str(value))
    # yfinance nests content under content.title etc.
    content = article.get("content")
    if isinstance(content, dict):
        for key in ("title", "summary", "description"):
            value = content.get(key)
            if value:
                parts.append(str(value))
    return " ".join(parts).strip()


def analyze_sentiment(ticker: str, articles: list[dict[str, Any]] | None = None) -> dict[str, float]:
    if articles is None:
        articles = fetch_news(ticker)

    analyzer = SentimentIntensityAnalyzer()
    scores: list[float] = []

    for article in articles[:20]:
        text = _article_text(article)
        if not text:
            continue
        scores.append(analyzer.polarity_scores(text)["compound"])

    if not scores:
        return {"mean_compound": 0.0, "multiplier": SENTIMENT_MULT_NEUTRAL, "article_count": 0}

    mean_compound = sum(scores) / len(scores)
    if mean_compound >= SENTIMENT_BULLISH:
        multiplier = SENTIMENT_MULT_BULLISH
    elif mean_compound <= SENTIMENT_BEARISH:
        multiplier = SENTIMENT_MULT_BEARISH
    else:
        multiplier = SENTIMENT_MULT_NEUTRAL

    return {
        "mean_compound": mean_compound,
        "multiplier": multiplier,
        "article_count": len(scores),
    }
