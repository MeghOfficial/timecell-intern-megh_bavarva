"""
Pipeline for risk metrics, explanation, and critique.
"""

from __future__ import annotations

import json
import logging
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

# Import Gemini API wrapper (used to call LLM)
from .api import stream_json

# Import Pydantic models (structured output schemas)
from .models import CritiqueResult, PortfolioExplanation

# Import prompt builders (used to create LLM prompts)
from .prompts import build_critic_messages, build_explainer_messages

# Try importing risk calculator from Task1
try:
    from Task1.risk_calculator import compute_risk_metrics
except ImportError:
    # If import fails, adjust path and retry
    from sys import path as _path
    _path.insert(0, "..")
    from Task1.risk_calculator import compute_risk_metrics

# Create logger for debugging
logger = logging.getLogger(__name__)


# Define structure of pipeline state
class ExplainerState(TypedDict, total=False):
    portfolio: dict
    tone: str
    metrics: dict
    explanation: PortfolioExplanation
    critique: CritiqueResult
    raw_text: str
    critic_raw_text: str
    critic_raw_texts: list[str]
    errors: list[str]
    revision: int
    max_revisions: int
    critic_feedback: str | None


# Convert value to number safely
def _as_number(value: object) -> float | None:
    # Handle infinity values
    if value in ("∞", "inf", "INF"):
        return float("inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# Decide final portfolio category (Aggressive / Balanced / Conservative)
def _compute_verdict(portfolio: dict, metrics: dict) -> str:
    runway_months = _as_number(metrics.get("runway_months"))
    assets = portfolio.get("assets", [])

    # Check if any asset has extreme crash risk (< -50%)
    has_extreme_crash = any(
        isinstance(asset, dict)
        and asset.get("expected_crash_pct", 0) < -50
        for asset in assets
    )

    # Check concentration warning
    concentration_warning = bool(metrics.get("concentration_warning", False))

    # If risky → Aggressive
    if has_extreme_crash or concentration_warning:
        return "Aggressive"

    # Check if all assets are relatively safe
    all_assets_safe = all(
        isinstance(asset, dict)
        and asset.get("expected_crash_pct", 0) >= -30
        for asset in assets
    )

    # If very safe and long runway → Conservative
    if runway_months is not None and runway_months > 120 and all_assets_safe:
        return "Conservative"

    # Default → Balanced
    return "Balanced"


def explain_portfolio(
    portfolio: dict,
    tone: Literal["beginner", "experienced", "expert"] = "beginner",
) -> dict:
    
    # Store errors during execution
    errors: list[str] = []

    # Step 1: Compute risk metrics
    try:
        metrics = compute_risk_metrics(portfolio)

        # If error returned from risk calculator → raise exception
        if metrics.get("error"):
            raise ValueError(metrics["error"])

    except Exception as exc:
        # Handle failure in risk calculation
        error = f"Risk computation failed: {exc}"
        logger.error(error)
        return None, None, None, [error]

    # Convert explanation schema into JSON format (for LLM)
    schema_text = json.dumps(PortfolioExplanation.model_json_schema(), indent=2)

    # Step 2: Explainer node (LLM generates explanation)
    def explainer_node(state: ExplainerState) -> ExplainerState:
        try:
            # Build prompt messages
            messages = build_explainer_messages(
                portfolio=state["portfolio"],
                tone=state["tone"],
                schema_text=schema_text,
                critic_feedback=state.get("critic_feedback"),
                risk_metrics=state.get("metrics"),
            )

            # Call LLM and get structured output
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
            # Handle LLM failure
            error = f"LLM explainer failed: {exc}"
            logger.error(error)
            return {
                **state,
                "errors": state.get("errors", []) + [error],
            }

    # Step 3: Critic node (second LLM checks correctness)
    def critic_node(state: ExplainerState) -> ExplainerState:
        try:
            # Convert critique schema to JSON
            critic_schema_text = json.dumps(
                CritiqueResult.model_json_schema(),
                indent=2,
            )

            # Build critic prompt
            messages = build_critic_messages(
                explanation=state["explanation"].model_dump(),
                portfolio=state["portfolio"],
                metrics=state["metrics"],
                schema_text=critic_schema_text,
            )

            # Call critic LLM
            critic_raw_text, critique = stream_json(
                messages=messages,
                schema_model=CritiqueResult,
                temperature=0.1,
            )

            # Prepare readable feedback
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
                "critic_raw_text": critic_raw_text,
                "critic_raw_texts": state.get("critic_raw_texts", []) + [critic_raw_text],
                "critic_feedback": critic_feedback,
            }

        except Exception as exc:
            # Critic failure is not fatal
            logger.warning("Critic failed (non-fatal): %s", exc)
            return {
                **state,
                "critique": None,
                "critic_raw_text": None,
                "critic_raw_texts": state.get("critic_raw_texts", []),
                "critic_feedback": None,
            }

    # Step 4: Decide whether to retry explanation
    def should_retry(state: ExplainerState) -> str:
        if state.get("errors"):
            return END

        critique = state.get("critique")

        # If approved → stop
        if critique and critique.critique_verdict == "Approved":
            return END

        # If max retries reached → stop
        if state.get("revision", 0) >= state.get("max_revisions", 3):
            return END

        # Else → retry explainer
        return "explainer"

    # Step 5: Increase revision count
    def bump_revision(state: ExplainerState) -> ExplainerState:
        return {
            **state,
            "revision": state.get("revision", 0) + 1,
        }

    # Step 6: Build LangGraph workflow
    graph = StateGraph(ExplainerState)

    graph.add_node("explainer", explainer_node)
    graph.add_node("critic", critic_node)
    graph.add_node("bump_revision", bump_revision)

    # Define flow
    graph.set_entry_point("explainer")
    graph.add_edge("explainer", "critic")
    graph.add_edge("critic", "bump_revision")
    graph.add_conditional_edges("bump_revision", should_retry)

    # Compile graph into runnable pipeline
    runner = graph.compile()

    # Execute pipeline
    final_state = runner.invoke({
        "portfolio": portfolio,
        "tone": tone,
        "metrics": metrics,
        "errors": errors,
        "revision": 0,
        "max_revisions": 3,
    })

    # Return final results
    return {
        "raw_text": final_state.get("raw_text"),
        "critic_raw_text": final_state.get("critic_raw_text"),
        "critic_raw_texts": final_state.get("critic_raw_texts", []),
        "structured_output": final_state.get("explanation"),
        "critique": final_state.get("critique"),
        "errors": final_state.get("errors", []),
    }