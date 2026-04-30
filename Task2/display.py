"""
Terminal display layer for market data.
Shows asset prices in a formatted table.
"""

from datetime import datetime
from typing import List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .fetchers.base import AssetPrice, FetchResult

console = Console()


def format_price(price: float) -> str:
    """Format price based on its size."""
    if price >= 1_000:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.2f}"
    return f"{price:.6f}"


def get_source_style(source_name: str) -> str:
    """Return display style for each data source."""
    styles = {
        "CoinGecko": "bold yellow",
        "Yahoo Finance": "bold cyan",
    }
    return styles.get(source_name, "white")


def render_price_table(results: List[FetchResult], fetched_time: datetime) -> None:
    """Create and display a table of asset prices."""

    # Format time for display
    timestamp = fetched_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    # Create table layout
    table = Table(
        title=f"[bold white]Asset Prices — fetched at {timestamp}[/bold white]",
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="white",
        padding=(0, 1),
    )

    # Define table columns
    table.add_column("Asset", style="bold white", width=10)
    table.add_column("Price", justify="right", width=16)
    table.add_column("Currency", justify="center", width=10)
    table.add_column("Source", justify="center", width=15)
    table.add_column("Status", justify="center", width=10)

    success_count = 0
    failure_count = 0

    for result in results:

        # If data was fetched successfully
        if result.success and result.data:
            asset: AssetPrice = result.data

            table.add_row(
                asset.name,
                format_price(asset.price),
                asset.currency,
                Text(asset.source, style=get_source_style(asset.source)),
                Text("✓ OK", style="bold green"),
            )
            success_count += 1

        # If fetching failed
        else:
            table.add_row(
                result.asset_name,
                "—",
                "—",
                "—",
                Text("✗ FAIL", style="bold red"),
            )
            failure_count += 1

    # Print the table
    console.print()
    console.print(table)

    # Prepare summary of results
    summary = [f"[green]✓ {success_count} fetched[/green]"]

    # If there are failures, show error details
    if failure_count:
        summary.append(f"[red]✗ {failure_count} failed[/red]")

        console.print()
        console.print(Panel(
            "\n".join(
                f"[red]✗[/red] {r.error}"
                for r in results if not r.success
            ),
            title="[bold red]Fetch Errors[/bold red]",
            border_style="red",
        ))

    # Print final summary line
    console.print(
        f"\n  Fetched [bold]{len(results)}[/bold] assets — {' | '.join(summary)}\n"
    )