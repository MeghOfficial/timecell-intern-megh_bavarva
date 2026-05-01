"""
Pydantic schemas for structured LLM output.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class PortfolioExplanation(BaseModel):
    """Structured output from the explainer node."""

    # Short summary explaining portfolio risk in simple English (3–4 sentences)
    summary: str = Field(
        description=(
            "3-4 sentence plain-English summary of the portfolio risk level for a non-expert."
        ),
        min_length=50,  # Minimum length ensures meaningful explanation
    )

    # One positive point about the portfolio
    doing_well: str = Field(
        description=(
            "One specific thing the investor is doing well."
        ),
        min_length=20,  # Avoid too short answers
    )

    # One suggestion for improvement with reason
    consider_changing: str = Field(
        description=(
            "One specific change the investor should consider, and why."
        ),
        min_length=20,  # Ensure explanation is clear
    )

    # Final classification of portfolio type
    verdict: Literal["Aggressive", "Balanced", "Conservative"] = Field(
        description="One-line verdict."
    )

    # Tone used for explanation (based on user level)
    tone_used: Literal["beginner", "experienced", "expert"] = Field(
        description="Tone used in the explanation."
    )


class CritiqueResult(BaseModel):
    """Structured output from the critic node."""

    # Indicates if explanation is correct or not
    is_accurate: bool = Field(
        description="True if explanation is accurate given the metrics."
    )

    # List of mistakes found (empty if no issues)
    issues_found: list[str] = Field(
        description="List of inaccuracies; empty if none.",
        default_factory=list,  # Default is empty list
    )

    # Improved version of summary if mistakes exist
    improved_summary: str | None = Field(
        description=(
            "Corrected summary if issues found; None otherwise."
        ),
        default=None,  # Default is None (no correction)
    )

    # Final decision of critic
    critique_verdict: Literal["Approved", "Rejected"] = Field(
        description="Accuracy verdict."
    )