"""
CLI Visualiser
Shows portfolio risk report in terminal
"""


def cli_bar_chart(assets: list, title: str = "Allocation Breakdown", bar_width: int = 40) -> None:
    print(f"\n{title}")
    print("─" * 55)
    for asset in assets:
        name = asset.get("name", "")
        pct = asset.get("allocation_pct", 0)
        filled = round((pct / 100) * bar_width)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty
        print(f"  {name:<10} {bar}  {pct}%")
    print("─" * 55)


def render_scenario_summary(scenario: dict) -> None:
    runway = scenario.get("runway_months")
    if runway == "∞":
        runway_text = "∞ (no expenses)"
    else:
        runway_text = f"{runway} months"

    print(f"{scenario.get('scenario', 'Scenario')} Summary")
    print(f"Post-Crash Value      : ₹{scenario.get('post_crash_value_inr', 0):,.0f}")
    print(f"Runway                : {runway_text}")
    print(f"Ruin Test             : {scenario.get('ruin_test', 'N/A')}")
    print(f"Largest Risk Asset    : {scenario.get('largest_risk_asset', 'N/A')}")
    print(f"Concentration Warning : {scenario.get('concentration_warning', False)}")


def render_full_report(metrics: dict, portfolio: dict, scenarios: dict | None = None) -> None:
    print("TIMECELL RISK REPORT")
    print(f"Portfolio Value   : ₹{portfolio.get('total_value_inr', 0):,.0f}")
    print(f"Monthly Expenses  : ₹{portfolio.get('monthly_expenses_inr', 0):,.0f}")
    print()

    cli_bar_chart(portfolio.get("assets", []), title="Portfolio Allocation")
    print()

    print("Risk Summary")
    print(f"Post-Crash Value      : ₹{metrics.get('post_crash_value', 0):,.0f}")
    print(f"Runway (months)       : {metrics.get('runway_months', 0)}")
    print(f"Ruin Test             : {metrics.get('ruin_test', 'N/A')}")
    print(f"Largest Risk Asset    : {metrics.get('largest_risk_asset', 'N/A')}")
    print(f"Concentration Warning : {metrics.get('concentration_warning', False)}")

    if scenarios and "severe_crash" in scenarios and "moderate_crash" in scenarios:
        print()
        render_scenario_summary(scenarios["severe_crash"])
        print()
        render_scenario_summary(scenarios["moderate_crash"])
