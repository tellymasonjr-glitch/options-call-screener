"""Streamlit-cached Yahoo Finance fetchers — cuts repeat API calls on Cloud."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import CACHE_TTL_SECONDS
from data import earnings as earnings_mod
from data import market_data as md
from data import news_data


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_price_history(ticker: str) -> pd.DataFrame:
    return md.get_price_history(ticker)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_spot_price(ticker: str) -> float:
    return md.get_spot_price(ticker)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_call_contracts(
    ticker: str,
    min_dte: int,
    max_dte: int,
    spot_key: float,
) -> list[dict]:
    """spot_key is -1 when spot should be fetched inside market_data."""
    spot = None if spot_key < 0 else spot_key
    return md.fetch_call_contracts(ticker, min_dte, max_dte, spot=spot)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_news(ticker: str) -> list[dict]:
    return news_data.fetch_news(ticker)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_earnings(ticker: str) -> list[dict]:
    return earnings_mod.fetch_earnings(ticker)
