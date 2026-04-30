"""
Shared base types, HTTP session, and IST clock.

Everything shared across fetchers lives here.
This avoids duplication and keeps code consistent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime    import datetime
from typing      import Optional

import pytz
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# IST timezone used across the project
IST = pytz.timezone("Asia/Kolkata")

def now_ist() -> datetime:
    """Return current time in IST timezone."""
    return datetime.now(tz=IST)


# Create a shared HTTP session for all API calls
# This improves performance by reusing connections
# and avoids creating a new session for every request
def _build_session() -> requests.Session:
    session = requests.Session()

    # Set default headers for all requests
    session.headers.update({
        "User-Agent": "TimecellDataFetcher/1.0 (github.com/timecell)",
        "Accept":     "application/json",
    })

    # Retry only for connection-level errors (not API logic errors)
    transport_retry = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],   # retry on server errors
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=transport_retry)

    # Attach retry adapter to both HTTP and HTTPS
    session.mount("https://", adapter)
    session.mount("http://",  adapter)

    return session


# Single shared session used everywhere in project
SESSION = _build_session()


# Standard data structure for asset price
# All fetchers must return data in this format
@dataclass
class AssetPrice:
    name:       str          # asset name (BTC, NIFTY50, etc.)
    symbol:     str          # API symbol or ticker
    price:      float        # latest price
    currency:   str          # USD, INR, etc.
    source:     str          # API source name
    fetched_at: datetime     # time when data was fetched


# Standard result wrapper for all fetch operations
# Always returns success or failure without raising exceptions
@dataclass
class FetchResult:
    success:    bool
    asset_name: str                  # always available for display
    data:       Optional[AssetPrice] = None
    error:      Optional[str]        = None   # short error message (provider + reason)