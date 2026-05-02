"""
Portfolio Risk Calculator
Calculates crash survival metrics for a portfolio
"""

import logging
from typing import Any

try:
    from .models import Asset, Portfolio
except ImportError:
    from models import Asset, Portfolio

logger = logging.getLogger(__name__)

# Minimum months required to survive (else FAIL)
RUIN_THRESHOLD_MONTHS = 12

# If any asset > 40% → concentration risk
CONCENTRATION_THRESHOLD = 40


def _compute_scenario(
    portfolio: Portfolio,
    crash_multiplier: float = 1.0,
    scenario_label: str = "Severe Crash",
) -> dict[str, Any]:
    """
    Calculate portfolio risk for one crash scenario

    crash_multiplier = 1.0 → full crash
    crash_multiplier = 0.5 → moderate crash
    """

    # If total portfolio value is negative → invalid case
    if portfolio.total_value_inr < 0:
        return {
            "scenario": scenario_label,
            "error": "Portfolio value cannot be negative",
            "post_crash_value_inr": 0,
            "runway_months": 0,
            "ruin_test": "FAIL",
            "largest_risk_asset": "N/A",
            "concentration_warning": False,
            "asset_breakdown": [],
        }

    # Ensure crash multiplier stays between 0 and 1
    if crash_multiplier < 0:
        crash_multiplier = 0
    if crash_multiplier > 1:
        crash_multiplier = 1

    total_value = portfolio.total_value_inr
    monthly_expenses = portfolio.monthly_expenses_inr

    # If no assets → assume all money is safe (like cash)
    if not portfolio.assets:
        post_crash_value = total_value

        # If no expenses → infinite runway
        if monthly_expenses <= 0:
            runway_months = "∞"
            ruin_test = "PASS"
        else:
            runway_months = round(post_crash_value / monthly_expenses, 2)
            ruin_test = "PASS" if runway_months > RUIN_THRESHOLD_MONTHS else "FAIL"

        return {
            "scenario": scenario_label,
            "post_crash_value_inr": round(post_crash_value, 2),
            "runway_months": runway_months,
            "ruin_test": ruin_test,
            "largest_risk_asset": "None",
            "concentration_warning": False,
            "asset_breakdown": [],
        }

    # Initialize totals
    post_crash_value = 0
    asset_risk_scores = {}
    asset_breakdown = []

    # Process each asset
    for asset in portfolio.assets:
        # Skip invalid allocation values
        if not (0 <= asset.allocation_pct <= 100):
            continue

        # Calculate money invested in this asset
        asset_value = total_value * (asset.allocation_pct / 100)

        # Adjust crash % based on scenario
        effective_crash_pct = asset.expected_crash_pct * crash_multiplier

        # Loss cannot exceed 100%
        if effective_crash_pct < -100:
            effective_crash_pct = -100

        # Calculate loss amount
        crash_loss = asset_value * (effective_crash_pct / 100)

        # Remaining value after crash
        post_crash_asset_value = asset_value + crash_loss

        # Avoid negative value
        if post_crash_asset_value < 0:
            post_crash_asset_value = 0

        # Add to total portfolio value
        post_crash_value += post_crash_asset_value

        # Risk score = allocation × crash severity
        # risk score per scenario uses effective crash pct
        risk_score = asset.allocation_pct * abs(effective_crash_pct)
        asset_risk_scores[asset.name] = risk_score

        # Store detailed breakdown
        asset_breakdown.append({
            "name": asset.name,
            "allocation_pct": asset.allocation_pct,
            "asset_value_inr": round(asset_value, 2),
            "effective_crash_pct": effective_crash_pct,
            "crash_loss_inr": round(crash_loss, 2),
            "post_crash_value_inr": round(post_crash_asset_value, 2),
            "risk_score": round(risk_score, 2),
        })

    # Calculate survival months (runway)
    if monthly_expenses <= 0:
        runway_months = "∞"
        ruin_test = "PASS"
    else:
        runway = post_crash_value / monthly_expenses
        runway_months = round(runway, 2)
        ruin_test = "PASS" if runway > RUIN_THRESHOLD_MONTHS else "FAIL"

    # Find asset contributing highest risk
    if asset_risk_scores:
        largest_risk_asset = max(
            asset_risk_scores,
            key=asset_risk_scores.get
        )
    else:
        largest_risk_asset = "None"

    # Check if any asset has too much allocation
    concentration_warning = any(
        asset.allocation_pct > CONCENTRATION_THRESHOLD
        for asset in portfolio.assets
    )

    # Check if all assets are risk-free (no crash)
    all_risk_free = all(
        asset.expected_crash_pct == 0
        for asset in portfolio.assets
    )

    return {
        "scenario": scenario_label,
        "post_crash_value_inr": round(post_crash_value, 2),
        "runway_months": runway_months,
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
        "all_risk_free": all_risk_free,
        "asset_breakdown": asset_breakdown,
    }


def compute_risk_metrics(portfolio_dict: dict) -> dict[str, Any]:
    """
    Main function

    Takes portfolio dictionary
    Returns severe crash + moderate crash report
    """

    try:
        from .models import portfolio_from_dict
    except ImportError:
        from models import portfolio_from_dict

    # Validate input
    if not portfolio_dict or not isinstance(portfolio_dict, dict):
        return {
            "post_crash_value": 0,
            "runway_months": 0,
            "ruin_test": "FAIL",
            "largest_risk_asset": "N/A",
            "concentration_warning": False,
        }

    # Convert dict → Portfolio object
    try:
        portfolio = portfolio_from_dict(portfolio_dict)
    except Exception:
        return {
            "post_crash_value": 0,
            "runway_months": 0,
            "ruin_test": "FAIL",
            "largest_risk_asset": "N/A",
            "concentration_warning": False,
        }

    # Edge case: no money
    if portfolio.total_value_inr == 0:
        return {
            "post_crash_value": 0,
            "runway_months": 0,
            "ruin_test": "FAIL",
            "largest_risk_asset": "N/A",
            "concentration_warning": False,
        }

    total_value = portfolio.total_value_inr
    monthly_expenses = portfolio.monthly_expenses_inr

    # If no assets → treat as safe
    if not portfolio.assets:
        post_crash_value = total_value
        if monthly_expenses <= 0:
            runway_months = "∞"
            ruin_test = "PASS"
        else:
            runway_months = round(post_crash_value / monthly_expenses, 2)
            ruin_test = "PASS" if runway_months > RUIN_THRESHOLD_MONTHS else "FAIL"

        return {
            "post_crash_value": round(post_crash_value, 2),
            "runway_months": runway_months,
            "ruin_test": ruin_test,
            "largest_risk_asset": "None",
            "concentration_warning": False,
        }

    # Initialize
    post_crash_value = 0.0
    asset_risk_scores: dict[str, float] = {}

    # Process each asset
    for asset in portfolio.assets:
        if not (0 <= asset.allocation_pct <= 100):
            continue

        asset_value = total_value * (asset.allocation_pct / 100)

        effective_crash_pct = asset.expected_crash_pct
        if effective_crash_pct < -100:
            effective_crash_pct = -100

        crash_loss = asset_value * (effective_crash_pct / 100)
        post_crash_asset_value = asset_value + crash_loss

        if post_crash_asset_value < 0:
            post_crash_asset_value = 0

        post_crash_value += post_crash_asset_value

        # Calculate risk score
        risk_score = asset.allocation_pct * abs(asset.expected_crash_pct)
        asset_risk_scores[asset.name] = risk_score

    # Calculate runway
    if monthly_expenses <= 0:
        runway_months = "∞"
        ruin_test = "PASS"
    else:
        runway = post_crash_value / monthly_expenses
        runway_months = round(runway, 2)
        ruin_test = "PASS" if runway > RUIN_THRESHOLD_MONTHS else "FAIL"

    # Find highest risk asset
    largest_risk_asset = (
        max(asset_risk_scores, key=asset_risk_scores.get)
        if asset_risk_scores else "None"
    )

    # Check concentration risk
    concentration_warning = any(
        asset.allocation_pct > CONCENTRATION_THRESHOLD
        for asset in portfolio.assets
    )

    return {
        "post_crash_value": round(post_crash_value, 2),
        "runway_months": runway_months,
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
    }


def compute_risk_scenarios(portfolio_dict: dict) -> dict[str, Any]:
    """
    Bonus helper: returns severe and moderate crash scenarios.
    """
    try:
        from .models import portfolio_from_dict
    except ImportError:
        from models import portfolio_from_dict

    # Convert input to Portfolio object
    try:
        portfolio = portfolio_from_dict(portfolio_dict)
    except Exception as exc:
        return {"error": str(exc)}

    # Run two scenarios
    severe_crash = _compute_scenario(
        portfolio,
        crash_multiplier=1.0,
        scenario_label="Severe Crash",
    )

    moderate_crash = _compute_scenario(
        portfolio,
        crash_multiplier=0.5,
        scenario_label="Moderate Crash",
    )

    return {
        "severe_crash": severe_crash,
        "moderate_crash": moderate_crash,
    }