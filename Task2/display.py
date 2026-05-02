"""
Terminal display layer for market data.
Shows asset prices in a formatted table.
"""

from datetime import datetime
from typing import List

from .fetchers.base import FetchResult


def render_price_table(results: List[FetchResult], fetched_time: datetime) -> None:
    """Create and display a table of asset prices."""

    # Convert time into readable format (IST)
    timestamp = fetched_time.strftime("%Y-%m-%d %H:%M:%S") + " IST"

    # Define column widths
    asset_width = 12
    price_width = 12
    currency_width = 8
    source_width = 12

    # Create table borders using characters
    top_line = (
        "┌" + "─" * (asset_width + 2)
        + "┬" + "─" * (price_width + 2)
        + "┬" + "─" * (currency_width + 2)
        + "┬" + "─" * (source_width + 2)
        + "┐"
    )

    mid_line = (
        "├" + "─" * (asset_width + 2)
        + "┼" + "─" * (price_width + 2)
        + "┼" + "─" * (currency_width + 2)
        + "┼" + "─" * (source_width + 2)
        + "┤"
    )

    bottom_line = (
        "└" + "─" * (asset_width + 2)
        + "┴" + "─" * (price_width + 2)
        + "┴" + "─" * (currency_width + 2)
        + "┴" + "─" * (source_width + 2)
        + "┘"
    )

    # Print table title with timestamp
    print(f"\nAsset Prices — fetched at {timestamp}")

    # Print table header
    print(top_line)
    print(
        "│ "
        + "Asset".ljust(asset_width)
        + " │ "
        + "Price".ljust(price_width)
        + " │ "
        + "Currency".ljust(currency_width)
        + " │ "
        + "Source".ljust(source_width)
        + " │"
    )
    print(mid_line)

    # Loop through all results
    for result in results:

        # If data fetch was successful
        if result.success and result.data:
            name = result.data.name.ljust(asset_width)
            price = f"{result.data.price:,.2f}".ljust(price_width)
            currency = result.data.currency.ljust(currency_width)
            source = (result.data.source or "").ljust(source_width)

            # Print normal row
            print(f"│ {name} │ {price} │ {currency} │ {source} │")

        else:
            # If fetch failed → show N/A
            name = str(result.asset_name).ljust(asset_width)
            na_label = "N/A".ljust(price_width)
            dash = "—".ljust(currency_width)
            source = "—".ljust(source_width)

            # Print fallback row
            print(f"│ {name} │ {na_label} │ {dash} │ {source} │")

    # Print bottom border
    print(bottom_line)