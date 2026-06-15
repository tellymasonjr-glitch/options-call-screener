"""Throttle and retry helpers for Yahoo Finance (shared Cloud IP rate limits)."""

from __future__ import annotations

import threading
import time
from typing import Callable, TypeVar

T = TypeVar("T")

_lock = threading.Lock()
_last_request_at = 0.0

try:
    from yfinance.exceptions import YFRateLimitError
except ImportError:

    class YFRateLimitError(Exception):
        """Fallback when yfinance exception type is unavailable."""


def is_rate_limit_error(exc: BaseException) -> bool:
    if isinstance(exc, YFRateLimitError):
        return True
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "ratelimit" in name or "rate limit" in text or "too many requests" in text


def throttle(min_interval_sec: float = 0.45) -> None:
    """Space out Yahoo requests to avoid burst rate limits on Streamlit Cloud."""
    global _last_request_at
    with _lock:
        now = time.monotonic()
        wait = min_interval_sec - (now - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()


def call_with_retry(
    func: Callable[..., T],
    *args,
    retries: int = 4,
    base_delay_sec: float = 2.0,
    **kwargs,
) -> T:
    last_err: BaseException | None = None
    for attempt in range(retries):
        throttle()
        try:
            return func(*args, **kwargs)
        except YFRateLimitError as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(base_delay_sec * (2**attempt))
        except Exception as exc:
            if is_rate_limit_error(exc):
                last_err = exc
                if attempt < retries - 1:
                    time.sleep(base_delay_sec * (2**attempt))
                continue
            raise
    if last_err is not None:
        raise last_err
    raise RuntimeError("call_with_retry failed without an error")
