"""
Asset configuration module.

Defines:
- Optional API keys (providers skipped if not set)
- API endpoints
- Retry settings
- Assets to fetch
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optional API keys
# If key is missing, that API will be skipped automatically
TWELVE_API_KEY: str | None = os.getenv("TWELVE_API_KEY") or None
ALPHA_API_KEY:  str | None = os.getenv("ALPHA_API_KEY")  or None
FCS_PUBLIC_KEY: str | None = os.getenv("FCS_PUBLIC_KEY") or None
FCS_API_KEY:    str | None = os.getenv("FCS_API_KEY") or None


# Request settings
# Controls API timeout and retry behavior
REQUEST_TIMEOUT_SECONDS = 5
MAX_RETRY_ATTEMPTS      = 3
RETRY_WAIT_SECONDS      = 2


# API endpoints
TWELVE_BASE_URL    = "https://api.twelvedata.com/price"
TWELVE_TIME_SERIES_URL = "https://api.twelvedata.com/time_series"
ALPHA_BASE_URL     = "https://www.alphavantage.co/query"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
BINANCE_BASE_URL   = "https://api.binance.com/api/v3/ticker/price"
COINCAP_BASE_URL   = "https://api.coincap.io/v2/assets"
FCS_BASE_URL       = "https://fcsapi.com/api-v3/forex/latest"


# List of assets to fetch
# Each asset contains required info for different APIs
ASSETS_TO_FETCH = [

    # Crypto assets
    {
        "name":          "BTC",
        "fetcher":       "crypto",
        "coin_id":       "bitcoin",
        "twelve_symbol": "BTC/USD",
        "alpha_from":    "BTC",
        "alpha_to":      "USD",
        "currency":      "USD",
    },

    # Index (NSE)
    {
        "name":           "NIFTY50",
        "fetcher":        "equity",
        "symbol_name":    "NIFTY 50",
        "fcs_symbol":     "NIFTY50",
        "nsepy_symbol":   "NIFTY 50",
        "yf_symbol":      "^NSEI",
        "twelve_symbols": [],
        "alpha_symbol":   None,
        "currency":       "INR",
    },

    # Stock (NSE)
    {
        "name":           "RELIANCE",
        "fetcher":        "equity",
        "symbol_name":    "RELIANCE",
        "yf_symbol":      "RELIANCE.NS",
        "fcs_symbol":     "RELIANCE.BSE",
        "twelve_symbols": [],
        "alpha_symbol":   "RELIANCE.BSE",
        "currency":       "INR",
    },
]