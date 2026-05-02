"""
Main entry point for live market data fetching.

Responsible for:
- Running all fetchers
- Handling concurrency
- Passing results to display layer
"""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

# Allow running this file directly (fixes import path)
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "Task2"

from .config import ASSETS_TO_FETCH
from .display import render_price_table
from .fetchers.base import FetchResult, now_ist
from .fetchers.crypto import fetch_crypto
from .fetchers.equity import fetch_equity


# Logging configuration
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# IST timezone setup
IST = timezone(timedelta(hours=5, minutes=30))


# Decide which fetcher to use based on asset type
def _dispatch_fetch(asset: dict) -> FetchResult:

    # Crypto assets
    if asset["fetcher"] == "crypto":
        return fetch_crypto(
            name=asset["name"],
            coin_id=asset["coin_id"],
            twelve_symbol=asset["twelve_symbol"],
            alpha_from=asset["alpha_from"],
            alpha_to=asset["alpha_to"],
            currency=asset["currency"],
        )

    # Equity assets (stocks, index)
    if asset["fetcher"] == "equity":
        twelve_symbols = asset.get("twelve_symbols")
        if not twelve_symbols:
            twelve_symbol = asset.get("twelve_symbol")
            twelve_symbols = [twelve_symbol] if twelve_symbol else []
        return fetch_equity(
            name=asset["name"],
            symbol_name=asset["symbol_name"],
            yf_symbol=asset["yf_symbol"],
            twelve_symbols=twelve_symbols,
            alpha_symbol=asset.get("alpha_symbol"),
            currency=asset["currency"],
            fcs_symbol=asset.get("fcs_symbol"),
            nsepy_symbol=asset.get("nsepy_symbol"),
        )

    # Unknown type safety case
    return FetchResult(
        success=False,
        asset_name=asset["name"],
        error=f"{asset['name']} — unknown fetcher type: '{asset['fetcher']}'",
    )


# Fetch all assets using parallel execution
def fetch_all_assets(
    assets: list = ASSETS_TO_FETCH
) -> tuple[List[FetchResult], datetime]:

    fetch_timestamp = now_ist()

    # Handle empty asset list
    if not assets:
        logger.warning("No assets provided for fetching.")
        return [], fetch_timestamp

    # Pre-create result list to preserve order
    results: List[FetchResult] = [None] * len(assets)   # type: ignore

    # ThreadPool used for parallel API calls
    with ThreadPoolExecutor(max_workers=max(1, len(assets))) as executor:

        # Submit all tasks and track their index
        future_to_index = {
            executor.submit(_dispatch_fetch, asset): idx
            for idx, asset in enumerate(assets)
        }

        # Process results as they complete
        for future in as_completed(future_to_index):
            idx = future_to_index[future]

            try:
                results[idx] = future.result()

            # Safety catch for unexpected failures
            except Exception as exc:
                asset_name = assets[idx]["name"]
                logger.error("Unexpected error fetching %s: %s", asset_name, exc)

                results[idx] = FetchResult(
                    success=False,
                    asset_name=asset_name,
                    error=f"{asset_name} — unexpected orchestrator error: {exc}",
                )

    return results, fetch_timestamp


# Main execution function
def main() -> int:

    # Fetch all asset prices
    results, fetch_timestamp = fetch_all_assets()

    # Exit early if nothing succeeded
    success_count = sum(1 for r in results if r.success)
    if success_count == 0:
        logger.critical("CRITICAL: No data from any source. Exiting.")
        sys.exit(1)

    # Display results with mixed success/failure (N/A for failed assets)
    render_price_table(results, fetch_timestamp)

    # Exit successfully: at least one asset succeeded
    return 0


# Script entry point
if __name__ == "__main__":
    sys.exit(main())