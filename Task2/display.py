"""
Terminal display layer for market data.
Shows asset prices in a formatted table.
"""

from datetime import datetime
from typing import List

from .fetchers.base import FetchResult


def render_price_table(results: List[FetchResult], fetched_time: datetime) -> None:
    """Create and display a table of asset prices."""
    timestamp = fetched_time.strftime("%Y-%m-%d %H:%M:%S") + " IST"

    asset_width = 10
    price_width = 12
    currency_width = 8
    top_line = (
        "┌" + "─" * (asset_width + 2)
        + "┬" + "─" * (price_width + 2)
        + "┬" + "─" * (currency_width + 2)
        + "┐"
    )
    mid_line = (
        "├" + "─" * (asset_width + 2)
        + "┼" + "─" * (price_width + 2)
        + "┼" + "─" * (currency_width + 2)
        + "┤"
    )
    bottom_line = (
        "└" + "─" * (asset_width + 2)
        + "┴" + "─" * (price_width + 2)
        + "┴" + "─" * (currency_width + 2)
        + "┘"
    )

    print(f"\nAsset Prices — fetched at {timestamp}")
    print(top_line)
    print(
        "│ "
        + "Asset".ljust(asset_width)
        + " │ "
        + "Price".ljust(price_width)
        + " │ "
        + "Currency".ljust(currency_width)
        + " │"
    )
    print(mid_line)

    for result in results:
        if result.success and result.data:
            name = result.data.name.ljust(asset_width)
            price = f"{result.data.price:,.2f}".ljust(price_width)
            currency = result.data.currency.ljust(currency_width)
            print(f"│ {name} │ {price} │ {currency} │")
        else:
            name = str(result.asset_name).ljust(asset_width)
            error_label = "ERROR".ljust(price_width)
            dash = "—".ljust(currency_width)
            print(f"│ {name} │ {error_label} │ {dash} │")

    print(bottom_line)