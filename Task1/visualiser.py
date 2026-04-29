"""
CLI Visualiser
Shows portfolio risk report in terminal
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.text import Text

# used to print styled output in terminal
console = Console()


def _ruin_badge(ruin_test: str) -> Text:
    # show PASS or FAIL in color

    if ruin_test == "PASS":
        return Text("✓ PASS", style="bold green")

    return Text("✗ FAIL", style="bold red")


def _concentration_badge(warning: bool) -> Text:
    # show concentration warning status

    if warning:
        return Text(
            "⚠ YES — Review concentration",
            style="bold yellow"
        )

    return Text(
        "✓ No concentration risk",
        style="green"
    )


def render_scenario_table(scenario: dict) -> Table:
    # create one table for one crash scenario
    # example: Severe Crash or Moderate Crash

    table = Table(
        title=f"[bold]{scenario['scenario']}[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        min_width=55,
    )

    # table column names
    table.add_column("Asset", style="white", width=10)
    table.add_column("Alloc %", justify="right", style="cyan")
    table.add_column("Crash %", justify="right", style="red")
    table.add_column("Loss (₹)", justify="right", style="red")
    table.add_column("Post-Crash (₹)", justify="right", style="green")

    # add each asset row
    for asset in scenario["asset_breakdown"]:
        table.add_row(
            asset["name"],
            f"{asset['allocation_pct']:.0f}%",
            f"{asset['effective_crash_pct']:.1f}%",
            f"₹{abs(asset['crash_loss_inr']):,.0f}",
            f"₹{asset['post_crash_value_inr']:,.0f}",
        )

    return table


def render_summary_panel(scenario: dict) -> Panel:
    # create summary box for important results

    runway = scenario["runway_months"]

    # if no monthly expenses then runway is infinite
    if runway == "∞":
        runway_text = "∞ (no expenses)"
    else:
        runway_text = f"{runway} months"

    # important final results
    content = [
        f"Post-Crash Value      : ₹{scenario['post_crash_value_inr']:,.0f}",
        f"Runway                : {runway_text}",
        f"Ruin Test             : {_ruin_badge(scenario['ruin_test'])}",
        f"Largest Risk Asset    : {scenario['largest_risk_asset']}",
        f"Concentration Warning : {_concentration_badge(scenario['concentration_warning'])}",
    ]

    return Panel(
        "\n".join(content),
        title=f"{scenario['scenario']} Summary",
        border_style="blue",
        padding=(1, 2),
    )


def cli_bar_chart(
    assets: list[dict],
    title: str = "Allocation Breakdown"
) -> None:
    # simple bar chart using terminal only
    # no plotting library used

    max_width = 40
    fill = "█"
    empty = "░"

    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("─" * 60)

    for asset in assets:
        name = asset["name"].ljust(10)
        pct = asset["allocation_pct"]

        # calculate how much bar should be filled
        filled = int((pct / 100) * max_width)
        empty_space = max_width - filled

        # create bar visually
        bar = (
            f"[green]{fill * filled}[/green]"
            f"[dim]{empty * empty_space}[/dim]"
        )

        console.print(
            f"{name} {bar} {pct:.0f}%"
        )

    console.print("─" * 60)


def render_full_report(metrics: dict) -> None:
    # main function to show complete report

    # top summary panel
    console.print(
        Panel(
            f"Portfolio Value: ₹{metrics['portfolio_value_inr']:,.0f}\n"
            f"Monthly Expenses: ₹{metrics['monthly_expenses_inr']:,.0f}",
            title="TIMECELL RISK REPORT",
            border_style="white",
        )
    )

    # show asset allocation bar chart
    cli_bar_chart(
        metrics["severe_crash"]["asset_breakdown"],
        title="Portfolio Allocation"
    )

    console.print()

    # show severe crash and moderate crash tables side by side
    console.print(
        Columns([
            render_scenario_table(metrics["severe_crash"]),
            render_scenario_table(metrics["moderate_crash"]),
        ])
    )

    console.print()

    # show final summary panels
    console.print(
        render_summary_panel(metrics["severe_crash"])
    )

    console.print(
        render_summary_panel(metrics["moderate_crash"])
    )
