"""
Task 03_1 - AI-Powered Portfolio Explainer (Gemini)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv


# Allow running this file directly: python Task3_1/main.py
# If script is run directly, adjust path so relative imports work
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "Task3"

# Import models and main pipeline function
from .models import CritiqueResult, PortfolioExplanation
from .pipeline import explain_portfolio

# Load environment variables from .env file
load_dotenv()

# Configure logging settings
logging.basicConfig(
    level=logging.WARNING,  # Show warnings and above
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Create logger for this file
logger = logging.getLogger(__name__)


# Example portfolio data for testing
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


def render_explanation(
    exp: PortfolioExplanation,
    critique: CritiqueResult | None,
    tone: str,
    raw_text: str | None,
) -> None:
    # Print selected tone
    print(f"\nTone: {tone}")

    # Print raw LLM output if available
    if raw_text:
        print("\nRaw LLM response:")
        print(raw_text)

    # Print parsed structured output
    print("\nParsed output:")

    print("Summary:")
    print(exp.summary)

    print("\nDoing well:")
    print(exp.doing_well)

    print("\nConsider changing:")
    print(exp.consider_changing)

    print("\nVerdict:")
    print(exp.verdict)

    print("\nTone used:")
    print(exp.tone_used)

    # If critique is available, print it
    if critique:
        print("\nCritique verdict:")
        print(critique.critique_verdict)

        # Print issues if any found
        if critique.issues_found:
            print("Issues:")
            for issue in critique.issues_found:
                print(f"- {issue}")

        # Print improved summary if available
        if critique.improved_summary:
            print("Improved summary:")
            print(critique.improved_summary)


def run_explainer(
    portfolio: dict,
    tone: Literal["beginner", "experienced", "expert"] = "beginner",
) -> None:
    # Call main pipeline function to generate explanation
    result = explain_portfolio(portfolio, tone=tone)
    errors = result.get("errors", [])
    explanation = result.get("structured_output")
    critique = result.get("critique")
    raw_text = result.get("raw_text")

    # If errors exist, print them and stop
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return

    # If no explanation generated, show error
    if not explanation:
        print("ERROR: No explanation generated.")
        return

    # Render final explanation output
    render_explanation(explanation, critique, tone, raw_text)


# Main entry point of program
if __name__ == "__main__":
    # Run explainer for different user levels (tones)
    for tone in ("beginner", "experienced", "expert"):
        run_explainer(EXAMPLE_PORTFOLIO, tone=tone)