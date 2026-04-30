"""
Equity fetcher using a fallback system.

Tries 3 sources:
1. Twelve Data (used only if API key is available)
2. Alpha Vantage (used only if API key is available)
3. yfinance (always used, no API key needed)
"""

from __future__ import annotations

import logging
from typing import Callable

import yfinance as yf

from .base import (
    SESSION, AssetPrice, FetchResult, now_ist,
)
from ..config import (
    ALPHA_API_KEY, ALPHA_BASE_URL,
    MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_WAIT_SECONDS,
    TWELVE_API_KEY, TWELVE_BASE_URL,
)

logger = logging.getLogger(__name__)


# Custom error used for retryable API failures
class TransientAPIError(Exception):
    """Used when API fails temporarily (like rate limits)."""


def _check_twelve_response(data: dict) -> None:
    """Check Twelve Data response and raise errors if needed."""

    # If price exists, response is valid
    if "price" in data:
        return

    code = data.get("code", 0)
    msg  = data.get("message", "unknown error")

    # Retryable errors
    if code == 429:
        raise TransientAPIError("rate limit reached")
    if code == 500:
        raise TransientAPIError("server error")

    # Permanent error
    if code == 404:
        raise ValueError("invalid symbol")

    raise ValueError(f"Twelve Data error {code}: {msg}")


def _check_alpha_response(data: dict) -> None:
    """Check Alpha Vantage response and validate data."""

    # Retryable error (too many requests)
    if "Note" in data:
        raise TransientAPIError("rate limit exceeded")

    # Daily limit reached
    if "Information" in data:
        raise ValueError("daily API limit reached")

    quote = data.get("Global Quote", {})

    # Check if price exists
    if not quote.get("05. price"):
        raise ValueError("no price data returned")


# Fetch price from Twelve Data
def _fetch_twelve_equity(twelve_symbol: str) -> float:
    response = SESSION.get(
        TWELVE_BASE_URL,
        params={"symbol": twelve_symbol, "apikey": TWELVE_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Validate response
    _check_twelve_response(data)

    return float(data["price"])


# Fetch price from Alpha Vantage
def _fetch_alpha_equity(av_symbol: str) -> float:
    response = SESSION.get(
        ALPHA_BASE_URL,
        params={
            "function": "GLOBAL_QUOTE",
            "symbol":   av_symbol,
            "apikey":   ALPHA_API_KEY,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Validate response
    _check_alpha_response(data)

    return float(data["Global Quote"]["05. price"])


# Fetch price from yfinance (no API key required)
def _fetch_yfinance(yf_symbol: str) -> float:
    ticker = yf.Ticker(yf_symbol)
    price  = None

    # Try fast_info first (quick access)
    for attr in ("last_price", "regular_market_price"):
        val = getattr(ticker.fast_info, attr, None)

        # Check for valid number (ignore NaN)
        if val is not None and val == val:
            price = float(val)
            break

    # If fast_info fails, use historical data
    if price is None:
        hist = ticker.history(period="1d")
        if hist.empty:
            raise ValueError(f"no data for {yf_symbol}")
        price = float(hist["Close"].iloc[-1])

    # Avoid invalid zero price
    if price == 0.0:
        raise ValueError(f"zero price for {yf_symbol}")

    return price


# Retry wrapper for handling temporary failures
def _with_retry(
    fn:         Callable[[], float],
    asset_name: str,
    provider:   str,
) -> float:
    """Retry function for temporary API failures."""

    import time

    last_exc: Exception = RuntimeError("no attempts made")

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            return fn()

        # Retry only for temporary errors
        except TransientAPIError as exc:
            last_exc = exc
            wait = RETRY_WAIT_SECONDS * (2 ** (attempt - 1))

            logger.warning(
                "%s from %s failed (%s). Retrying %d/%d in %ds...",
                asset_name, provider, exc, attempt, MAX_RETRY_ATTEMPTS, wait,
            )

            time.sleep(wait)

        # Do not retry for permanent errors
        except Exception as exc:
            raise exc

    raise last_exc


# Main function to fetch equity price
def fetch_equity(
    name:          str,
    symbol_name:   str,
    yf_symbol:     str,
    twelve_symbol: str,
    currency:      str,
) -> FetchResult:
    """
    Fetch equity price using fallback approach.
    Tries multiple APIs until one succeeds.
    """

    price:       float | None = None
    source_used: str   | None = None

    # Try Twelve Data first (if API key exists)
    if TWELVE_API_KEY:
        try:
            price = _with_retry(
                fn=lambda: _fetch_twelve_equity(twelve_symbol),
                asset_name=name,
                provider="Twelve Data",
            )
            source_used = "Twelve Data"

        except Exception as exc:
            logger.warning(f"{name}: Twelve Data failed ({exc})")

    else:
        logger.debug(f"{name}: Twelve Data skipped (no API key)")

    # Try Alpha Vantage next
    if price is None and ALPHA_API_KEY:
        av_symbol = yf_symbol.replace(".NS", "").replace("^", "")

        try:
            price = _with_retry(
                fn=lambda: _fetch_alpha_equity(av_symbol),
                asset_name=name,
                provider="Alpha Vantage",
            )
            source_used = "Alpha Vantage"

        except Exception as exc:
            logger.warning(f"{name}: Alpha Vantage failed ({exc})")

    elif price is None:
        logger.debug(f"{name}: Alpha Vantage skipped (no API key)")

    # Final fallback: yfinance
    if price is None:
        try:
            price = _fetch_yfinance(yf_symbol)
            source_used = "yfinance"

        except Exception as exc:
            logger.error(f"{name}: all sources failed ({exc})")

    # Return success result
    if price is not None and source_used is not None:
        return FetchResult(
            success=True,
            asset_name=name,
            data=AssetPrice(
                name=name,
                symbol=yf_symbol,
                price=price,
                currency=currency,
                source=source_used,
                fetched_at=now_ist(),
            ),
        )

    # Return failure result
    return FetchResult(
        success=False,
        asset_name=name,
        error=f"Twelve Data, Alpha Vantage, yfinance all failed for {name}",
    )