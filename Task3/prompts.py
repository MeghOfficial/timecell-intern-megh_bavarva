"""
Prompt builders for the portfolio explainer and critic.
"""

from __future__ import annotations

import json
from typing import Literal

# LangChain message types for LLM interaction
from langchain_core.messages import HumanMessage, SystemMessage

from .trace_utils import traceable


# Tone rules used to shape vocabulary, depth, and analogies
TONE_CONFIGS = {
    "beginner": {
        "persona": "trusted, warm, and unflinchingly honest",
        "vocabulary": (
            "plain everyday language, no jargon. If a finance term is unavoidable, explain it in brackets immediately"
        ),
        "depth": (
            "focus on what things mean in practice (money, safety, months of living expenses). skip formulas"
        ),
        "analogy": (
            "do not use analogies"
        ),
    },
    "experienced": {
        "persona": "trusted, direct, and precise",
        "vocabulary": (
            "use clear finance terms, and explain them briefly when needed"
        ),
        "depth": (
            "balance practical impacts (rupees, months) with allocation percentages"
        ),
        "analogy": (
            "use minimal analogies only when they add clarity"
        ),
    },
    "expert": {
        "persona": "unflinchingly honest and data-driven",
        "vocabulary": (
            "use full finance vocabulary: drawdown, concentration risk, crash magnitude"
        ),
        "depth": (
            "reference exact crash percentages and post-crash runway figures"
        ),
        "analogy": (
            "no analogies. speak peer-to-peer"
        ),
    },
}


@traceable(name="build_explainer_system_prompt")
def build_explainer_system_prompt(
    tone: Literal["beginner", "experienced", "expert"],
) -> str:
    tone_cfg = TONE_CONFIGS[tone]

    # Return system prompt instructions for LLM
    return f"""
<role>
You are a senior wealth advisor at an AI-powered Indian family-office platform called Timecell.
You are trusted, warm, and unflinchingly honest — like a brilliant friend who happens to have a CFA.
You never sugarcoat risk, but you never alarm without reason.
Your client today is a {tone} investor.
</role>

<communication_rules>
- Vocabulary: {tone_cfg["vocabulary"]}.
- Depth: {tone_cfg["depth"]}.
- Analogy rule: {tone_cfg["analogy"]}.
- Write in second person ("Your portfolio…", "You are doing well by…").
- Never say "I cannot provide financial advice." You are their advisor. Give real, direct guidance.
- Never hallucinate numbers. Every quantitative claim you make MUST come from the
    <portfolio_data> and <risk_metrics> sections the user provides. If a value is absent, say so.
- Keep total output under 350 words. Clarity beats length.
</communication_rules>

<strict_output_format>
You MUST return ONLY valid JSON — no preamble, no markdown fences, no trailing text.
The JSON must match this exact schema:

{{
    "summary": "<3–4 sentences: overall risk level, what the numbers mean for this investor>",
    "doing_well": "<1 specific thing the investor is doing correctly, referencing actual data>",
    "consider_changing": "<1 specific thing to reconsider, with a concrete reason grounded in the data>",
    "verdict": "<exactly one of: Aggressive | Balanced | Conservative>",
    "tone_used": "<exactly one of: beginner | experienced | expert>"
}}

Rules for each field:
- "summary"            → Must reference the post-crash value OR runway months from risk_metrics.
- "doing_well"         → Must name a specific asset or allocation decision.
- "consider_changing"  → Must name a specific asset or structural issue (e.g. concentration).
- "verdict"            → Single word only. No punctuation, no explanation inline.
- "tone_used"          → Echo back the tone you were instructed to use.

If ANY field is missing or malformed, the entire response is invalid.
Do NOT wrap the JSON in ```json``` or any other markdown. Start with {{ and end with }}.
</strict_output_format>

<verdict_rubric>
Use this rubric to decide the verdict — apply it strictly:

Aggressive   → Post-crash severe runway < 24 months, OR any single asset > 40 % allocation
                             with crash_pct worse than -50 %, OR majority of portfolio in high-volatility assets.
Conservative → Post-crash severe runway > 120 months AND no asset with crash_pct worse than -30 %.
Balanced     → Everything in between.
</verdict_rubric>
""".strip()


@traceable(name="build_user_prompt")
def build_user_prompt(
    portfolio: dict,
    risk_metrics: dict,
    critic_feedback: str | None = None,
) -> str:
    # Convert portfolio and metrics to formatted JSON strings
    portfolio_json = json.dumps(portfolio, indent=2)
    metrics_json = json.dumps(risk_metrics, indent=2)

    # Return user prompt with structured data
    return f"""
Analyse the following portfolio and produce a plain-English risk explanation
using only the data below. Do not invent numbers.

<portfolio_data>
{portfolio_json}
</portfolio_data>

<risk_metrics>
{metrics_json}
</risk_metrics>

<critic_feedback>
{critic_feedback or "None"}
</critic_feedback>

<task>
1. Read the portfolio allocation, total value, and monthly expenses.
2. Read the risk_metrics — pay close attention to:
    - post_crash_value_inr (severe crash scenario)
    - runway_months (both scenarios)
    - ruin_test result
    - largest_risk_asset
    - concentration_warning
    - asset_breakdown (per-asset crash loss)
3. Produce the JSON output as specified in your system prompt.
    Every claim must be traceable to the data above.
4. If critic_feedback is not "None", address it directly and correct the issues.
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


@traceable(name="build_explainer_messages")
def build_explainer_messages(
    portfolio: dict,
    tone: str,
    schema_text: str,
    critic_feedback: str | None = None,
    risk_metrics: dict | None = None,
) -> list:
    # Create system message (instructions for AI behavior)
    system = SystemMessage(content=build_explainer_system_prompt(tone))

    # Create user message (data + task)
    user_prompt = build_user_prompt(
        portfolio,
        risk_metrics or {},
        critic_feedback=critic_feedback,
    )

    # Add few-shot examples to guide output format
    human = HumanMessage(content=user_prompt + "\n\n" + FEW_SHOT_ANCHOR)

    # Return message list
    return [system, human]


@traceable(name="build_critic_messages")
def build_critic_messages(
    explanation: dict,
    portfolio: dict,
    metrics: dict,
    schema_text: str,
) -> list:
    # System message defines critic role
    system = SystemMessage(content=(
        "You are a strict reviewer. Check the draft against the original numbers. "
        "Did the Explainer invent any fake numbers? Did it miss a rule? "
        "Only judge factual correctness and rule compliance, not writing style."
    ))

    # Human message contains explanation plus input data for accuracy checks
    human = HumanMessage(content=(
        "Review this explanation for strict factual accuracy and rule compliance.\n\n"
        "Portfolio Data:\n"
        f"{json.dumps(portfolio, indent=2)}\n\n"
        "Risk Metrics:\n"
        f"{json.dumps(metrics, indent=2)}\n\n"
        "Explanation to review:\n"
        f"Summary: {explanation.get('summary')}\n"
        f"Doing Well: {explanation.get('doing_well')}\n"
        f"Consider Changing: {explanation.get('consider_changing')}\n"
        f"Verdict: {explanation.get('verdict')}\n\n"
        "Strict checks:\n"
        "1) Every number must exist in portfolio_data or risk_metrics. No invented figures.\n"
        "2) Every factual claim must match the inputs (assets, allocations, crash %s, runway months, post-crash value).\n"
        "3) The explanation must make sense given the risk inputs (e.g., high crash % implies higher risk).\n"
        "4) Required JSON schema and field rules are followed: 3-4 sentence summary, specific asset named in doing_well, "
        "actionable change in consider_changing, one-word verdict, correct tone_used.\n"
        "If any requirement is missing, any number is incorrect, or the reasoning contradicts the inputs, reject and explain why.\n\n"
        "Return ONLY valid JSON that matches this schema. "
        "Use critique_verdict as Approved or Rejected only. "
        "Do not wrap in markdown.\n"
        f"SCHEMA:\n{schema_text}"
    ))

    # Return critic messages
    return [system, human]