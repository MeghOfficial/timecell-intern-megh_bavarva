"""
Pipeline for risk metrics, explanation, and critique.
"""

from __future__ import annotations

import json
import logging
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

# Import Gemini API wrapper
from .api import stream_json

# Import Pydantic models (schemas)
from .models import CritiqueResult, PortfolioExplanation

# Import prompt builders
from .prompts import build_critic_messages, build_explainer_messages

# Try importing risk calculator from Task1
try:
    from Task1.risk_calculator import compute_risk_metrics
except ImportError:
    # If direct import fails, adjust path and retry
    from sys import path as _path
    _path.insert(0, "..")
    from Task1.risk_calculator import compute_risk_metrics

# Create logger
logger = logging.getLogger(__name__)


class ExplainerState(TypedDict, total=False):
    portfolio: dict
    tone: str
    metrics: dict
    expected_verdict: str
    explanation: PortfolioExplanation
    critique: CritiqueResult
    raw_text: str
    errors: list[str]
    revision: int
    max_revisions: int
    critic_feedback: str | None


def _as_number(value: object) -> float | None:
    if value in ("∞", "inf", "INF"):
        return float("inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_verdict(portfolio: dict, metrics: dict) -> str:
    severe = metrics.get("severe_crash", {})
    runway_months = _as_number(severe.get("runway_months"))
    assets = portfolio.get("assets", [])

    has_concentration_risk = any(
        isinstance(asset, dict)
        and asset.get("allocation_pct", 0) > 40
        and asset.get("expected_crash_pct", 0) < -50
        for asset in assets
    )

    if runway_months is not None and runway_months < 24:
        return "Aggressive"
    if has_concentration_risk:
        return "Aggressive"

    all_assets_safe = all(
        isinstance(asset, dict)
        and asset.get("expected_crash_pct", 0) >= -30
        for asset in assets
    )

    if runway_months is not None and runway_months > 120 and all_assets_safe:
        return "Conservative"

    return "Balanced"


def explain_portfolio(
    portfolio: dict,
    tone: Literal["beginner", "experienced", "expert"] = "beginner",
) -> tuple[PortfolioExplanation | None, CritiqueResult | None, str | None, list[str]]:
    
    # List to store errors
    errors: list[str] = []

    # Step 1: Compute risk metrics
    try:
        metrics = compute_risk_metrics(portfolio)

        # If risk calculator returns error, raise exception
        if metrics.get("error"):
            raise ValueError(metrics["error"])

    except Exception as exc:
        # Handle risk calculation failure
        error = f"Risk computation failed: {exc}"
        logger.error(error)
        return None, None, None, [error]

    # Convert PortfolioExplanation schema into JSON text
    schema_text = json.dumps(PortfolioExplanation.model_json_schema(), indent=2)

    expected_verdict = _compute_verdict(portfolio, metrics)

    def explainer_node(state: ExplainerState) -> ExplainerState:
        try:
            messages = build_explainer_messages(
                portfolio=state["portfolio"],
                tone=state["tone"],
                schema_text=schema_text,
                expected_verdict=state["expected_verdict"],
                critic_feedback=state.get("critic_feedback"),
            )

            raw_text, explanation = stream_json(
                messages=messages,
                schema_model=PortfolioExplanation,
                temperature=0.3,
            )

            return {
                **state,
                "raw_text": raw_text,
                "explanation": explanation,
            }
        except Exception as exc:
            error = f"LLM explainer failed: {exc}"
            logger.error(error)
            return {
                **state,
                "errors": state.get("errors", []) + [error],
            }

    def critic_node(state: ExplainerState) -> ExplainerState:
        try:
            critic_schema_text = json.dumps(
                CritiqueResult.model_json_schema(),
                indent=2,
            )
            messages = build_critic_messages(
                explanation=state["explanation"].model_dump(),
                metrics=state["metrics"],
                schema_text=critic_schema_text,
            )

            _, critique = stream_json(
                messages=messages,
                schema_model=CritiqueResult,
                temperature=0.1,
            )

            feedback_parts: list[str] = [
                f"Critique verdict: {critique.critique_verdict}.",
            ]
            if critique.issues_found:
                feedback_parts.append("Issues found:")
                feedback_parts.extend(f"- {issue}" for issue in critique.issues_found)
            if critique.improved_summary:
                feedback_parts.append("Suggested corrected summary:")
                feedback_parts.append(critique.improved_summary)

            critic_feedback = "\n".join(feedback_parts)

            return {
                **state,
                "critique": critique,
                "critic_feedback": critic_feedback,
            }
        except Exception as exc:
            logger.warning("Critic failed (non-fatal): %s", exc)
            return {
                **state,
                "critique": None,
                "critic_feedback": None,
            }

    def should_retry(state: ExplainerState) -> str:
        if state.get("errors"):
            return END
        critique = state.get("critique")
        if critique and critique.critique_verdict == "Approved":
            return END
        if state.get("revision", 0) >= state.get("max_revisions", 3):
            return END
        return "explainer"

    def bump_revision(state: ExplainerState) -> ExplainerState:
        return {
            **state,
            "revision": state.get("revision", 0) + 1,
        }

    graph = StateGraph(ExplainerState)
    graph.add_node("explainer", explainer_node)
    graph.add_node("critic", critic_node)
    graph.add_node("bump_revision", bump_revision)

    graph.set_entry_point("explainer")
    graph.add_edge("explainer", "critic")
    graph.add_edge("critic", "bump_revision")
    graph.add_conditional_edges("bump_revision", should_retry)

    runner = graph.compile()

    final_state = runner.invoke({
        "portfolio": portfolio,
        "tone": tone,
        "metrics": metrics,
        "expected_verdict": expected_verdict,
        "errors": errors,
        "revision": 0,
        "max_revisions": 3,
    })

    return (
        final_state.get("explanation"),
        final_state.get("critique"),
        final_state.get("raw_text"),
        final_state.get("errors", []),
    )