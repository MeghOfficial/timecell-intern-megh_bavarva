"""
Crypto fetcher using a fallback system.

Tries 3 sources:
1. CoinGecko (always used, no API key needed)
2. Twelve Data (used only if API key is available)
3. Alpha Vantage (used only if API key is available)
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from .base import SESSION, AssetPrice, FetchResult, now_ist
from .equity import (
    TransientAPIError,
    _check_twelve_response,     # reuse same validation logic
    _with_retry,                # reuse retry logic
)
from ..config import (
    ALPHA_API_KEY, ALPHA_BASE_URL,
    COINGECKO_BASE_URL,
    MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_WAIT_SECONDS,
    TWELVE_API_KEY, TWELVE_BASE_URL,
)

logger = logging.getLogger(__name__)


# Fetch price from CoinGecko (no API key needed)
def _fetch_coingecko(coin_id: str, vs_currency: str) -> float:
    response = SESSION.get(
        f"{COINGECKO_BASE_URL}/simple/price",
        params={"ids": coin_id, "vs_currencies": vs_currency},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Check if coin exists in response
    if coin_id not in data:
        raise ValueError(f"CoinGecko: no data for '{coin_id}'")

    price = data[coin_id].get(vs_currency)

    # Check if price exists
    if price is None:
        raise ValueError(f"CoinGecko: no {vs_currency} price for '{coin_id}'")

    # Avoid invalid zero price
    if float(price) == 0.0:
        raise ValueError(f"CoinGecko: zero price returned for '{coin_id}'")

    return float(price)


# Fetch price from Twelve Data
def _fetch_twelve_crypto(twelve_symbol: str) -> float:
    response = SESSION.get(
        TWELVE_BASE_URL,
        params={"symbol": twelve_symbol, "apikey": TWELVE_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Validate response using shared function
    _check_twelve_response(data)

    return float(data["price"])


# Fetch price from Alpha Vantage
def _fetch_alpha_crypto(from_currency: str, to_currency: str) -> float:
    response = SESSION.get(
        ALPHA_BASE_URL,
        params={
            "function":      "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency.upper(),
            "to_currency":   to_currency.upper(),
            "apikey":        ALPHA_API_KEY,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    # Handle rate limits
    if "Note" in data:
        raise TransientAPIError("Alpha Vantage per-second limit — retrying")
    if "Information" in data:
        raise ValueError("Alpha Vantage daily limit reached")

    rate_data = data.get("Realtime Currency Exchange Rate", {})
    rate = rate_data.get("5. Exchange Rate")

    # Check if exchange rate exists
    if not rate:
        raise ValueError(
            f"Alpha Vantage: no exchange rate for {from_currency}/{to_currency}"
        )

    return float(rate)


# Main function to fetch crypto price
def fetch_crypto(
    name:          str,
    coin_id:       str,
    twelve_symbol: str,
    alpha_from:    str,
    alpha_to:      str,
    currency:      str = "USD",
) -> FetchResult:
    """
    Fetch crypto price using fallback approach.
    Tries multiple APIs until one succeeds.
    """

    vs_currency  = currency.lower()
    price:       float | None = None
    source_used: str   | None = None

    # Try CoinGecko first (most reliable and free)
    try:
        price = _with_retry(
            fn=lambda: _fetch_coingecko(coin_id, vs_currency),
            asset_name=name,
            provider="CoinGecko",
        )
        source_used = "CoinGecko"
        logger.info("✓ %s via CoinGecko: %.2f %s", name, price, currency)

    except Exception as exc:
        logger.warning(
            "✗ %s — CoinGecko failed (%s). Trying Twelve Data...", name, exc,
        )

    # Try Twelve Data if CoinGecko fails and API key is available
    if price is None and TWELVE_API_KEY:
        try:
            price = _with_retry(
                fn=lambda: _fetch_twelve_crypto(twelve_symbol),
                asset_name=name,
                provider="Twelve Data",
            )
            source_used = "Twelve Data"
            logger.info("✓ %s via Twelve Data: %.2f %s", name, price, currency)

        except Exception as exc:
            logger.warning(
                "✗ %s — Twelve Data failed (%s). Trying Alpha Vantage...",
                name, exc,
            )

    elif price is None:
        logger.debug("Twelve Data skipped for %s — no API key.", name)

    # Try Alpha Vantage if others fail and API key is available
    if price is None and ALPHA_API_KEY:
        try:
            price = _with_retry(
                fn=lambda: _fetch_alpha_crypto(alpha_from, alpha_to),
                asset_name=name,
                provider="Alpha Vantage",
            )
            source_used = "Alpha Vantage"
            logger.info("✓ %s via Alpha Vantage: %.2f %s", name, price, currency)

        except Exception as exc:
            logger.error(
                "✗ %s — all sources failed. Last error: %s", name, exc,
            )

    elif price is None:
        logger.debug("Alpha Vantage skipped for %s — no API key.", name)

    # Return success result
    if price is not None and source_used is not None:
        return FetchResult(
            success=True,
            asset_name=name,
            data=AssetPrice(
                name=name,
                symbol=coin_id,
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
        error=f"CoinGecko, Twelve Data, Alpha Vantage all failed for {name}",
    )