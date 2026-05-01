"""
Prompt builders for the portfolio explainer and critic.
"""

from __future__ import annotations

import json
from typing import Literal

# LangChain message types for LLM interaction
from langchain_core.messages import HumanMessage, SystemMessage


def build_explainer_system_prompt(
    tone: Literal["beginner", "experienced", "expert"],
) -> str:
    # Define how the AI should behave based on user level
    tone_personas = {
        "beginner": (
            "friendly and patient; use simple words, avoid jargon, and give clear "
            "analogies (like a 'financial GPS')"
        ),
        "experienced": (
            "a confident wealth manager; be concise and direct, assuming they "
            "understand basic concepts like 'volatility' and 'diversification'"
        ),
        "expert": (
            "a quantitative risk analyst; be precise and data-driven, using terms "
            "like 'drawdown', 'correlation', and 'convexity'"
        ),
    }

    # Return system prompt instructions for LLM
    return f"""
ROLE AND OBJECTIVE
You are a world-class financial advisor, but your style is {tone_personas[tone]}. You are speaking to a non-expert client, so keep the language simple and friendly while staying honest. Your sole task is to analyze a client's investment portfolio and provide a clear, honest, and actionable risk explanation.

ABSOLUTE RULES (Must Follow)
1. NO HALLUCINATION: Base your analysis only on the provided portfolio data. If it's not in the data, do not mention it.
2. NO MARKDOWN: Return ONLY a raw JSON object. No preamble, no markdown code blocks, no commentary outside the JSON.
3. STRICT FORMAT: Your entire response must conform exactly to the required JSON schema.

Your task: Analyze the client's portfolio. You will receive portfolio data in the user message.

Required output JSON schema:
{{
    "summary": "A 3-4 sentence plain-English summary of the portfolio's risk level.",
    "doing_well": "One specific thing the investor is doing well. Be specific and reference the portfolio data.",
    "consider_changing": "One specific thing the investor should consider changing, and why. Must be actionable and tied to the data.",
    "verdict": "One of: Aggressive, Balanced, Conservative",
    "tone_used": "One of: beginner, experienced, expert"
}}

Rules for each field:
- summary: Must include at least one specific number from the portfolio data (e.g., total value, monthly expenses, or allocation percent). Explain any numbers in very simple English for a non-expert. Never use analogies or metaphors; be direct.
- doing_well: Must name a specific asset or allocation decision.
- consider_changing: Must name a specific asset or structural issue (e.g. concentration) AND include at least one specific number from the provided data.
- verdict: Must exactly match the provided expected_verdict. Single word only.
- tone_used: Echo back the instructed tone.

Verdict rubric:
- Aggressive: Severe runway < 24 months, OR any single asset > 40% with crash_pct worse than -50%.
- Conservative: Severe runway > 120 months AND no asset with crash_pct worse than -30%.
- Balanced: Everything in between.
""".strip()


def build_user_prompt(
    portfolio: dict,
    expected_verdict: str,
    critic_feedback: str | None = None,
) -> str:
    # Convert portfolio and metrics to formatted JSON strings
    portfolio_json = json.dumps(portfolio, indent=2)

    # Return user prompt with structured data
    return f"""
Analyse the following portfolio and produce a plain-English risk explanation
using only the data below. You may use numbers when needed, but explain them in very simple English. Do not invent numbers.

<portfolio_data>
{portfolio_json}
</portfolio_data>

<expected_verdict>
{expected_verdict}
</expected_verdict>

<critic_feedback>
{critic_feedback or "None"}
</critic_feedback>

<task>
1. Read the portfolio allocation, total value, and monthly expenses.
2. Produce the JSON output as specified in your system prompt.
    The verdict field must exactly match <expected_verdict>.
3. If critic_feedback is not "None", address it directly and correct the issues.
   Every claim must be traceable to the data above.
</task>

Respond with ONLY the JSON object. Nothing else.
""".strip()


# Few-shot examples to guide LLM output format and quality
FEW_SHOT_ANCHOR = """
<example>
Below is an example of a perfectly formatted response.
Do NOT use these numbers - they are illustrative only.

{
  "summary": "Your portfolio is high-risk. In a severe market crash, it could drop from Rs1 Cr to roughly Rs42 L - that covers only about 5 months of your Rs80,000 monthly expenses. The biggest danger is your 30% bet on Bitcoin, which could lose 80% of its value overnight.",
  "doing_well": "Holding 10% in Cash is a smart move - it acts as a buffer that survives any crash intact, giving you immediate liquidity when markets are in freefall.",
  "consider_changing": "Your NIFTY50 allocation at 40% crosses the concentration threshold. Spreading even 10% of that into bonds or international equity would meaningfully reduce your single-market exposure.",
  "verdict": "Aggressive",
  "tone_used": "beginner"
}
</example>

<example>
Portfolio: 100% Cash
{
    "summary": "Your portfolio is very low risk because it is fully in cash. In a severe crash, the post-crash value stays the same and your runway is long, so you can cover expenses without selling volatile assets. This means your downside exposure is minimal, but growth may be limited.",
    "doing_well": "Keeping 100% in Cash eliminates crash losses and preserves liquidity.",
    "consider_changing": "Consider allocating a small portion to low-volatility assets to improve long-term growth, since your current allocation is fully defensive.",
    "verdict": "Conservative",
    "tone_used": "beginner"
}
</example>

<example>
Portfolio: Ultra-Aggressive Crypto-Heavy
{
    "summary": "Your portfolio is highly aggressive with most of the allocation in BTC and ETH. In a severe crash, the portfolio value can drop sharply and the runway can shrink quickly. This makes your ability to fund expenses more fragile during downturns.",
    "doing_well": "You still hold 10% in GOLD, which provides some diversification away from crypto.",
    "consider_changing": "Consider reducing the combined BTC and ETH allocation to lower concentration risk, since both assets can lose 80% or more in a crash.",
    "verdict": "Aggressive",
    "tone_used": "experienced"
}
</example>

<example>
Portfolio: All Risk-Free Assets
{
    "summary": "Your portfolio is conservative with all assets expected to have zero crash loss. In a severe crash, the post-crash value remains stable and the runway stays strong. This prioritizes capital preservation over growth.",
    "doing_well": "Allocating to FD and GOLD keeps volatility low and protects principal.",
    "consider_changing": "If your goal includes growth, consider a modest allocation to equities to balance safety with long-term returns.",
    "verdict": "Conservative",
    "tone_used": "experienced"
}
</example>

"""


def build_explainer_messages(
    portfolio: dict,
    tone: str,
    schema_text: str,
    expected_verdict: str,
    critic_feedback: str | None = None,
) -> list:
    # Create system message (instructions for AI behavior)
    system = SystemMessage(content=build_explainer_system_prompt(tone))

    # Create user message (data + task)
    user_prompt = build_user_prompt(
        portfolio,
        expected_verdict,
        critic_feedback=critic_feedback,
    )

    # Add few-shot examples to guide output format
    human = HumanMessage(content=user_prompt + "\n\n" + FEW_SHOT_ANCHOR)

    # Return message list
    return [system, human]


def build_critic_messages(
    explanation: dict,
    metrics: dict,
    schema_text: str,
) -> list:
    # Extract severe crash metrics
    severe = metrics["severe_crash"]

    # System message defines critic role
    system = SystemMessage(content=(
        "You are a strict financial accuracy reviewer. "
        "Only judge factual correctness, not writing style."
    ))

    # Human message contains explanation + actual metrics for verification
    human = HumanMessage(content=(
        "Review this explanation for factual accuracy.\n\n"
        f"Total Value (INR): {int(metrics['portfolio_value_inr']):,}\n"
        f"Post-Crash Value (Severe): {int(severe['post_crash_value_inr']):,}\n"
        f"Runway (months): {severe['runway_months']}\n"
        f"Ruin Test: {severe['ruin_test']}\n"
        f"Largest Risk Asset: {severe['largest_risk_asset']}\n"
        f"Concentration Warning: {severe['concentration_warning']}\n\n"
        "Explanation to review:\n"
        f"Summary: {explanation['summary']}\n"
        f"Doing Well: {explanation['doing_well']}\n"
        f"Consider Changing: {explanation['consider_changing']}\n"
        f"Verdict: {explanation['verdict']}\n\n"
        "Return ONLY valid JSON that matches this schema. "
        "Use critique_verdict as Approved or Rejected only. "
        "Do not wrap in markdown.\n"
        f"SCHEMA:\n{schema_text}"
    ))

    # Return critic messages
    return [system, human]