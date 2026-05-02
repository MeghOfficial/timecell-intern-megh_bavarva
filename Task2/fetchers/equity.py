"""
Equity fetcher using a fallback system.

Tries sources in order:
1. Alpha Vantage (TIME_SERIES_DAILY)
2. FCS API (with HMAC-SHA256 token)
3. yfinance (free, no API key needed)
4. nsepy (for NIFTY50, free, no API key needed)
"""

from __future__ import annotations

import logging
import time
import hmac
import hashlib
from typing import Callable

import yfinance as yf

from .base import (
    SESSION, AssetPrice, FetchResult, now_ist,
)
from ..config import (
    ALPHA_API_KEY, ALPHA_BASE_URL,
    FCS_PUBLIC_KEY, FCS_API_KEY, FCS_BASE_URL,
    MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_WAIT_SECONDS,
    TWELVE_API_KEY, TWELVE_BASE_URL,
)

from ..config import TWELVE_TIME_SERIES_URL

logger = logging.getLogger(__name__)


# Custom error used for retryable API failures
class TransientAPIError(Exception):
    """Used when API fails temporarily (like rate limits)."""


def _check_twelve_response(data: dict) -> None:
    """Check Twelve Data response and raise errors if needed."""
    # If price exists or time_series 'values' exists, response is valid
    if "price" in data or "values" in data:
        return

    code = data.get("code", 0)
    msg  = data.get("message", "unknown error")

    if "apikey" in str(msg).lower():
        logger.error("Twelve Data: invalid API key or key missing.")
        raise ValueError("invalid API key")

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

    if "Error Message" in data or "error" in data:
        logger.error("Alpha Vantage: invalid API key or request.")
        raise ValueError("invalid API key")

    quote = data.get("Global Quote", {})

    # Check if price exists
    if not quote.get("05. price"):
        raise ValueError("no price data returned")


# Fetch price from Twelve Data
def _fetch_twelve_equity(twelve_symbol: str) -> float:
    # Prefer the time_series endpoint to get the latest close price
    params = {"symbol": twelve_symbol, "interval": "1min", "outputsize": 1, "apikey": TWELVE_API_KEY}
    response = SESSION.get(TWELVE_TIME_SERIES_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()

    # time_series returns 'values' as an array of OHLC points
    if isinstance(data, dict) and "values" in data and data.get("values"):
        try:
            latest = data["values"][0]
            close = latest.get("close") or latest.get("close")
            if close is None:
                # fallback to price endpoint if structure unexpected
                raise ValueError("no close price in time_series response")
            logger.info("✓ %s via Twelve Data (time_series %s): %s", twelve_symbol, twelve_symbol, close)
            return float(close)
        except Exception:
            # fall back to the simple price endpoint
            pass

    # Fallback: call the simple price endpoint if time_series failed to return usable data
    response = SESSION.get(
        TWELVE_BASE_URL,
        params={"symbol": twelve_symbol, "apikey": TWELVE_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
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


# Fetch price from FCS API (with HMAC-SHA256 authentication)
def _fetch_fcs_equity(fcs_symbol: str) -> float:
    """Fetch equity price from FCS API using HMAC-SHA256 token."""
    if not FCS_PUBLIC_KEY or not FCS_API_KEY:
        raise ValueError("FCS API credentials not configured")

    # Generate HMAC-SHA256 token
    expiry = int(time.time()) + 300  # Token valid for 5 minutes
    message = FCS_PUBLIC_KEY + str(expiry)
    token = hmac.new(
        FCS_API_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # Call FCS API
    params = {
        "id": fcs_symbol,
        "_public_key": FCS_PUBLIC_KEY,
        "_expiry": expiry,
        "_token": token,
    }

    response = SESSION.get(
        FCS_BASE_URL,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Check for errors
    if data.get("status") != 200:
        raise ValueError(f"FCS API error: {data.get('msg', 'Unknown error')}")

    # Extract price from response
    if "response" not in data or not data["response"]:
        raise ValueError(f"FCS API: no data for {fcs_symbol}")

    response_data = data["response"][0] if isinstance(data["response"], list) else data["response"]
    price = response_data.get("price") or response_data.get("bid")

    if not price:
        raise ValueError(f"FCS API: no price for {fcs_symbol}")

    return float(price)


# Fetch price from nsepy (for NIFTY50, no API key needed)
def _fetch_nsepy(symbol: str) -> float:
    """Fetch NSE data using nsepy library."""
    try:
        from nsepy import get_quote
        quote = get_quote(symbol)
        
        # nsepy returns a Series with various fields
        # Get the lastPrice or close price
        if hasattr(quote, 'lastPrice'):
            price = quote['lastPrice']
        elif hasattr(quote, 'close'):
            price = quote['close']
        else:
            # Try to get price from the series
            price = quote.get('lastPrice') or quote.get('close')
        
        if not price or price == 0.0:
            raise ValueError(f"nsepy: zero or invalid price for {symbol}")
        
        return float(price)
    except ImportError:
        raise ValueError("nsepy not installed. Install with: pip install nsepy")
    except Exception as exc:
        raise ValueError(f"nsepy failed: {exc}")


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
    twelve_symbols: list[str],
    alpha_symbol:  str | None,
    currency:      str,
    fcs_symbol:    str | None = None,
    nsepy_symbol:  str | None = None,
) -> FetchResult:
    """
    Fetch equity price using fallback approach.
    
    Chains used:
    - RELIANCE (BSE): Alpha Vantage -> FCS API -> yfinance
    - NIFTY50: Alpha Vantage -> FCS API -> yfinance -> nsepy
    """

    price:       float | None = None
    source_used: str   | None = None

    # Try Alpha Vantage first
    if price is None and ALPHA_API_KEY and alpha_symbol:
        try:
            price = _with_retry(
                fn=lambda: _fetch_alpha_equity(alpha_symbol),
                asset_name=name,
                provider="Alpha Vantage",
            )
            source_used = "Alpha Vantage"
            logger.info("✓ %s via Alpha Vantage: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.warning("%s: Alpha Vantage failed (%s). Trying FCS API...", name, exc)
    
    # Skip Alpha Vantage silently if API key missing
    elif price is None and not ALPHA_API_KEY:
        logger.debug("%s: Alpha Vantage skipped (API key missing). Trying FCS API...", name)

    # Try FCS API next
    if price is None and fcs_symbol:
        if FCS_PUBLIC_KEY and FCS_API_KEY:
            try:
                price = _with_retry(
                    fn=lambda: _fetch_fcs_equity(fcs_symbol),
                    asset_name=name,
                    provider="FCS API",
                )
                source_used = "FCS API"
                logger.info("✓ %s via FCS API: %.2f %s", name, price, currency)
            except Exception as exc:
                logger.warning("%s: FCS API failed (%s). Trying yfinance...", name, exc)
        else:
            logger.debug("%s: FCS API skipped (credentials missing). Trying yfinance...", name)

    # Try yfinance next
    if price is None:
        try:
            price = _fetch_yfinance(yf_symbol)
            source_used = "yfinance"
            logger.info("✓ %s via yfinance: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.warning("%s: yfinance failed (%s).", name, exc)
            
            # For NIFTY50, try nsepy as last resort
            if price is None and nsepy_symbol:
                logger.warning("%s: Trying nsepy...", name)

    # Final fallback: nsepy (only for NIFTY50)
    if price is None and nsepy_symbol:
        try:
            price = _with_retry(
                fn=lambda: _fetch_nsepy(nsepy_symbol),
                asset_name=name,
                provider="nsepy",
            )
            source_used = "nsepy"
            logger.info("✓ %s via nsepy: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.error("%s: nsepy failed (%s). All sources exhausted.", name, exc)

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
    logger.error(
        "%s: all sources failed. Please try again after some time.",
        name,
    )
    
    sources_tried = [s for s in ["Alpha Vantage", "FCS API", "yfinance", "nsepy"] if s]
    error_msg = f"{', '.join(sources_tried)} all failed for {name}"
    
    return FetchResult(
        success=False,
        asset_name=name,
        error=error_msg,
    )