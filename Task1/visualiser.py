"""
CLI Visualiser
Shows portfolio risk report in terminal
"""


def cli_bar_chart(assets: list, title: str = "Allocation Breakdown", bar_width: int = 40) -> None:
    # Print chart title
    print(f"\n{title}")
    print("─" * 55)

    # Loop through each asset
    for asset in assets:
        # Get asset name and allocation %
        name = asset.get("name", "")
        pct = asset.get("allocation_pct", 0)

        # Calculate how much bar should be filled
        filled = round((pct / 100) * bar_width)

        # Remaining empty part of bar
        empty = bar_width - filled

        # Create bar using blocks
        bar = "█" * filled + "░" * empty

        # Print formatted line
        print(f"  {name:<10} {bar}  {pct}%")

    print("─" * 55)


def render_scenario_summary(scenario: dict) -> None:
    # Get runway value
    runway = scenario.get("runway_months")

    # Handle infinite runway case
    if runway == "∞":
        runway_text = "∞ (no expenses)"
    else:
        runway_text = f"{runway} months"

    # Print scenario summary
    print(f"{scenario.get('scenario', 'Scenario')} Summary")
    print(f"Post-Crash Value      : ₹{scenario.get('post_crash_value_inr', 0):,.0f}")
    print(f"Runway                : {runway_text}")
    print(f"Ruin Test             : {scenario.get('ruin_test', 'N/A')}")
    print(f"Largest Risk Asset    : {scenario.get('largest_risk_asset', 'N/A')}")
    print(f"Concentration Warning : {scenario.get('concentration_warning', False)}")


def render_full_report(metrics: dict, portfolio: dict, scenarios: dict | None = None) -> None:
    # Print report header
    print("TIMECELL RISK REPORT")

    # Show basic portfolio info
    print(f"Portfolio Value   : ₹{portfolio.get('total_value_inr', 0):,.0f}")
    print(f"Monthly Expenses  : ₹{portfolio.get('monthly_expenses_inr', 0):,.0f}")
    print()

    # Show allocation bar chart
    cli_bar_chart(portfolio.get("assets", []), title="Portfolio Allocation")
    print()

    # Print summary + per-asset crash impact tables for each scenario (Severe & Moderate)
    if scenarios and "severe_crash" in scenarios and "moderate_crash" in scenarios:
        for key in ("severe_crash", "moderate_crash"):
            sc = scenarios[key]
            print()
            # Short scenario summary (5 important things)
            print(f"{sc.get('scenario', key)} — Summary")
            print("─" * 55)
            post = sc.get('post_crash_value_inr', sc.get('post_crash_value', 0))
            runway = sc.get('runway_months', 'N/A')
            ruin = sc.get('ruin_test', 'N/A')
            largest = sc.get('largest_risk_asset', 'N/A')
            conc = sc.get('concentration_warning', False)
            print(f"Post-Crash Value      : ₹{post:,.0f}")
            print(f"Runway (months)       : {runway}")
            print(f"Ruin Test             : {ruin}")
            print(f"Largest Risk Asset    : {largest}")
            print(f"Concentration Warning : {conc}")

            # Per-asset table
            print()
            print(f"{sc.get('scenario', key)} — Per-Asset Crash Impact")
            print("─" * 80)
            # Header
            print(f"{'Asset':<12} {'Before (₹)':>14} {'After (₹)':>14} {'Loss (₹)':>14} {'Risk Score':>14}")
            print("─" * 80)
            for a in sc.get('asset_breakdown', []):
                name = a.get('name', '')
                before = a.get('asset_value_inr', 0)
                after = a.get('post_crash_value_inr', 0)
                loss = a.get('crash_loss_inr', 0)
                rscore = a.get('risk_score', 0)
                print(f"{name:<12} {before:14,.0f} {after:14,.0f} {loss:14,.0f} {rscore:14,.2f}")
            print("─" * 80)