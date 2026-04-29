"""
Task 01 — Portfolio Risk Calculator

Main file to run:
- normal example portfolio
- multiple edge case portfolios
"""

import logging

try:
    from .risk_calculator import compute_risk_metrics
    from .visualiser import render_full_report, console
except ImportError:
    from risk_calculator import compute_risk_metrics
    from visualiser import render_full_report, console

from rich.rule import Rule


# show only warning logs
# change to DEBUG if you want detailed logs
logging.basicConfig(level=logging.WARNING)


# example portfolio from problem statement
EXAMPLE_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}


# edge case: 100% cash portfolio
# no crash risk
CASH_ONLY_PORTFOLIO = {
    "total_value_inr": 5_000_000,
    "monthly_expenses_inr": 100_000,
    "assets": [
        {"name": "CASH", "allocation_pct": 100, "expected_crash_pct": 0},
    ],
}


# edge case: very aggressive portfolio
# heavy crypto exposure
AGGRESSIVE_PORTFOLIO = {
    "total_value_inr": 20_000_000,
    "monthly_expenses_inr": 200_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 60, "expected_crash_pct": -80},
        {"name": "ETH", "allocation_pct": 30, "expected_crash_pct": -85},
        {"name": "GOLD", "allocation_pct": 10, "expected_crash_pct": -15},
    ],
}


# edge case: zero monthly expenses
# runway becomes infinite
ZERO_EXPENSES_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 0,
    "assets": [
        {"name": "BTC", "allocation_pct": 50, "expected_crash_pct": -70},
        {"name": "NIFTY50", "allocation_pct": 50, "expected_crash_pct": -35},
    ],
}


# edge case: very high expenses
# runway becomes very small
HIGH_EXPENSES_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 3_000_000,
    "assets": [
        {"name": "NIFTY50", "allocation_pct": 100, "expected_crash_pct": -40},
    ],
}


# edge case: crash more than 100%
# code should limit it to -100%
EXTREME_CRASH_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 100_000,
    "assets": [
        {
            "name": "SUPER_RISKY",
            "allocation_pct": 100,
            "expected_crash_pct": -120,
        },
    ],
}


# edge case: no assets in portfolio
# treated like all cash
NO_ASSETS_PORTFOLIO = {
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 50_000,
    "assets": [],
}


# edge case: all assets are risk free
# no crash loss expected
ALL_RISK_FREE_PORTFOLIO = {
    "total_value_inr": 25_000_000,
    "monthly_expenses_inr": 200_000,
    "assets": [
        {"name": "FD", "allocation_pct": 60, "expected_crash_pct": 0},
        {"name": "GOLD", "allocation_pct": 40, "expected_crash_pct": 0},
    ],
}


def run(portfolio_dict: dict, label: str) -> None:
    #print portfolio title
    console.print(Rule(f"[bold yellow]{label}[/bold yellow]"))

    #calculate risk metrics
    metrics = compute_risk_metrics(portfolio_dict)

    #if error exists, show error message
    if "error" in metrics:
        console.print(f"[bold red]Error: {metrics['error']}[/bold red]")

    #otherwise show full report
    else:
        render_full_report(metrics)

    #print empty line for clean output
    console.print()


if __name__ == "__main__":
    
    #run normal example portfolio
    run(EXAMPLE_PORTFOLIO, "Example Portfolio — 1 Crore INR")

    #run 100% cash portfolio
    run(CASH_ONLY_PORTFOLIO, "Edge Case — 100% Cash")

    #run high crypto aggressive portfolio
    run(AGGRESSIVE_PORTFOLIO, "Edge Case — Ultra-Aggressive Crypto-Heavy")

    #run zero monthly expenses case
    run(ZERO_EXPENSES_PORTFOLIO, "Edge Case — Zero Monthly Expenses")

    #run very high expenses case
    run(HIGH_EXPENSES_PORTFOLIO, "Edge Case — Very High Expenses (Short Runway)")

    #run crash more than 100% case
    run(EXTREME_CRASH_PORTFOLIO, "Edge Case — Crash >100% (Clamped to -100%)")

    #run no assets case
    run(NO_ASSETS_PORTFOLIO, "Edge Case — No Assets (Treated as all cash)")

    #run all risk-free assets case
    run(ALL_RISK_FREE_PORTFOLIO, "Edge Case — All Assets Risk-Free")