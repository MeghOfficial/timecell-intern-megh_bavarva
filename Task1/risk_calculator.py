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

    # portfolio value must be positive
    if portfolio.total_value_inr <= 0:
        return {
            "scenario": scenario_label,
            "error": "Portfolio value must be positive",
            "post_crash_value_inr": 0,
            "runway_months": 0,
            "ruin_test": "FAIL",
            "largest_risk_asset": "N/A",
            "concentration_warning": False,
            "asset_breakdown": [],
        }

    # keep multiplier between 0 and 1
    if crash_multiplier < 0:
        crash_multiplier = 0
    if crash_multiplier > 1:
        crash_multiplier = 1

    total_value = portfolio.total_value_inr
    monthly_expenses = portfolio.monthly_expenses_inr

    # if no assets, treat as all cash
    if not portfolio.assets:
        post_crash_value = total_value

        if monthly_expenses <= 0:
            runway_months = "∞"
            ruin_test = "PASS"
        else:
            runway_months = round(post_crash_value / monthly_expenses, 1)
            ruin_test = "PASS" if runway_months > 12 else "FAIL"

        return {
            "scenario": scenario_label,
            "post_crash_value_inr": round(post_crash_value, 2),
            "runway_months": runway_months,
            "ruin_test": ruin_test,
            "largest_risk_asset": "None",
            "concentration_warning": False,
            "asset_breakdown": [],
        }

    post_crash_value = 0
    asset_risk_scores = {}
    asset_breakdown = []

    for asset in portfolio.assets:
        # skip wrong allocation values
        if not (0 <= asset.allocation_pct <= 100):
            continue

        # money invested in this asset
        asset_value = total_value * (asset.allocation_pct / 100)

        # calculate crash %
        effective_crash_pct = asset.expected_crash_pct * crash_multiplier

        # maximum loss cannot be more than 100%
        if effective_crash_pct < -100:
            effective_crash_pct = -100

        # crash loss
        crash_loss = asset_value * (effective_crash_pct / 100)

        # value left after crash
        post_crash_asset_value = asset_value + crash_loss

        if post_crash_asset_value < 0:
            post_crash_asset_value = 0

        post_crash_value += post_crash_asset_value

        # risk score = allocation × crash size
        risk_score = asset.allocation_pct * abs(asset.expected_crash_pct)
        asset_risk_scores[asset.name] = risk_score

        asset_breakdown.append({
            "name": asset.name,
            "allocation_pct": asset.allocation_pct,
            "asset_value_inr": round(asset_value, 2),
            "effective_crash_pct": effective_crash_pct,
            "crash_loss_inr": round(crash_loss, 2),
            "post_crash_value_inr": round(post_crash_asset_value, 2),
        })

    # runway calculation
    if monthly_expenses <= 0:
        runway_months = "∞"
        ruin_test = "PASS"
    else:
        runway = post_crash_value / monthly_expenses

        if runway > 12000:
            runway_months = "∞"
        else:
            runway_months = round(runway, 1)

        ruin_test = "PASS" if runway > 12 else "FAIL"

    # largest risk asset
    if asset_risk_scores:
        largest_risk_asset = max(
            asset_risk_scores,
            key=asset_risk_scores.get
        )
    else:
        largest_risk_asset = "None"

    # concentration warning
    concentration_warning = any(
        asset.allocation_pct > 40
        for asset in portfolio.assets
    )

    # check if all assets are risk free
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

    # check input
    if not portfolio_dict or not isinstance(portfolio_dict, dict):
        return {
            "error": "Invalid portfolio dictionary",
            "portfolio_value_inr": 0,
            "monthly_expenses_inr": 0,
            "severe_crash": {"error": "Invalid input"},
            "moderate_crash": {"error": "Invalid input"},
        }

    try:
        portfolio = portfolio_from_dict(portfolio_dict)
    except Exception as e:
        return {
            "error": f"Portfolio validation failed: {str(e)}",
            "portfolio_value_inr": 0,
            "monthly_expenses_inr": 0,
            "severe_crash": {"error": str(e)},
            "moderate_crash": {"error": str(e)},
        }

    # severe crash = full crash
    severe_crash = _compute_scenario(
        portfolio,
        crash_multiplier=1.0,
        scenario_label="Severe Crash"
    )

    # moderate crash = half crash
    moderate_crash = _compute_scenario(
        portfolio,
        crash_multiplier=0.5,
        scenario_label="Moderate Crash"
    )

    return {
        "portfolio_value_inr": portfolio.total_value_inr,
        "monthly_expenses_inr": portfolio.monthly_expenses_inr,
        "severe_crash": severe_crash,
        "moderate_crash": moderate_crash,
    }