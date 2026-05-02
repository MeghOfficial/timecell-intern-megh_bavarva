"""
Crypto fetcher using a fallback system.

Tries sources in order:
1. Twelve Data (/price endpoint)
2. CoinGecko (free, no API key)
3. Binance (free, no API key)
4. CoinCap (free, no API key)
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
    BINANCE_BASE_URL,
    COINCAP_BASE_URL,
    MAX_RETRY_ATTEMPTS, REQUEST_TIMEOUT_SECONDS, RETRY_WAIT_SECONDS,
    TWELVE_API_KEY, TWELVE_BASE_URL,
)

from ..config import TWELVE_TIME_SERIES_URL

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


# Fetch price from Binance (no API key needed for public ticker)
def _fetch_binance(symbol: str = "BTCUSDT") -> float:
    response = SESSION.get(
        BINANCE_BASE_URL,
        params={"symbol": symbol},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    if "price" not in data:
        raise ValueError(f"Binance: no price for '{symbol}'")

    price = float(data["price"])

    # Avoid invalid zero price
    if price == 0.0:
        raise ValueError(f"Binance: zero price for '{symbol}'")

    return price


# Fetch price from CoinCap (no API key needed)
def _fetch_coincap(coin_id: str = "bitcoin") -> float:
    response = SESSION.get(
        f"{COINCAP_BASE_URL}/{coin_id}",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    if "data" not in data or "priceUsd" not in data.get("data", {}):
        raise ValueError(f"CoinCap: no price for '{coin_id}'")

    price = float(data["data"]["priceUsd"])

    # Avoid invalid zero price
    if price == 0.0:
        raise ValueError(f"CoinCap: zero price for '{coin_id}'")

    return price


# Fetch price from Twelve Data
def _fetch_twelve_crypto(twelve_symbol: str) -> float:
    # Use the simple price endpoint first for BTC and other cryptos
    response = SESSION.get(
        TWELVE_BASE_URL,
        params={"symbol": twelve_symbol, "apikey": TWELVE_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    _check_twelve_response(data)

    if "price" in data:
        logger.info("✓ %s via Twelve Data (price): %s", twelve_symbol, data["price"])
        return float(data["price"])

    # If price key is not returned, try time_series as a fallback
    response = SESSION.get(
        TWELVE_TIME_SERIES_URL,
        params={"symbol": twelve_symbol, "interval": "1min", "outputsize": 1, "apikey": TWELVE_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "values" in data and data.get("values"):
        latest = data["values"][0]
        close = latest.get("close")
        if close is not None:
            logger.info("✓ %s via Twelve Data (time_series close): %s", twelve_symbol, close)
            return float(close)

    raise ValueError(f"Twelve Data: no price for '{twelve_symbol}'")


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

    if "Error Message" in data or "error" in data:
        logger.error("Alpha Vantage: invalid API key or request.")
        raise ValueError("invalid API key")

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
    Tries sources in order until one succeeds:
    1. Twelve Data
    2. CoinGecko
    3. Binance
    4. CoinCap
    """

    vs_currency  = currency.lower()
    price:       float | None = None
    source_used: str   | None = None

    # Try Twelve Data first
    if TWELVE_API_KEY:
        try:
            price = _with_retry(
                fn=lambda: _fetch_twelve_crypto(twelve_symbol),
                asset_name=name,
                provider="Twelve Data",
            )
            source_used = "Twelve Data"
            logger.info("✓ %s via Twelve Data: %.2f %s", name, price, currency)
        except Exception as exc:
            msg = str(exc).lower()
            if "invalid symbol" in msg or "invalid symbol" in repr(exc).lower():
                logger.warning("%s: Twelve Data invalid symbol: %s", name, twelve_symbol)
            else:
                logger.warning("✗ %s — Twelve Data failed (%s). Trying CoinGecko...", name, exc)
    else:
        logger.debug("Twelve Data skipped for %s (API key missing). Trying CoinGecko...", name)

    # Try CoinGecko next
    if price is None:
        try:
            price = _with_retry(
                fn=lambda: _fetch_coingecko(coin_id, vs_currency),
                asset_name=name,
                provider="CoinGecko",
            )
            source_used = "CoinGecko"
            logger.info("✓ %s via CoinGecko: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.warning("✗ %s — CoinGecko failed (%s). Trying Binance...", name, exc)

    # Try Binance next
    if price is None:
        try:
            price = _with_retry(
                fn=lambda: _fetch_binance(f"{coin_id.upper()}USD" if coin_id == "bitcoin" else f"{coin_id.upper()}USD"),
                asset_name=name,
                provider="Binance",
            )
            source_used = "Binance"
            logger.info("✓ %s via Binance: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.warning("✗ %s — Binance failed (%s). Trying CoinCap...", name, exc)

    # Final fallback: CoinCap
    if price is None:
        try:
            price = _with_retry(
                fn=lambda: _fetch_coincap(coin_id),
                asset_name=name,
                provider="CoinCap",
            )
            source_used = "CoinCap"
            logger.info("✓ %s via CoinCap: %.2f %s", name, price, currency)
        except Exception as exc:
            logger.error("✗ %s — all sources failed. Last error: %s", name, exc)

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
    logger.error(
        "%s: all sources failed. Please try again after some time.",
        name,
    )
    return FetchResult(
        success=False,
        asset_name=name,
        error=f"Twelve Data, CoinGecko, Binance, CoinCap all failed for {name}",
    )