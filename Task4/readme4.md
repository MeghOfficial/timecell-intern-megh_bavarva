# Task 4 — Fingerprint Analyzer + Assumption Inversion (Timecell)

## One-line summary
A small web prototype that translates a portfolio allocation into a plain‑English "money habit" fingerprint, a bias-corrected "ghost portfolio" recommendation, and concrete tripwire warnings that tell an HNI user when a recommended change would stop making sense.

## Why I built this (copy these three sentences)
Problem: HNI families often make portfolio choices driven by behavioural biases; they need a simple, plain-English check that translates allocations into behavioural risks and concrete warning signals.  
User: This is aimed at Indian HNI investors (family offices / multi‑generational households) who hold concentrated assets like real estate and gold alongside equities and need crash‑resilience guidance.  
Why this matters: Unlike numeric dashboards, this tool pairs a bias-corrected "ghost portfolio" recommendation with tripwire warnings, producing actionable plain‑English advice that existing tools rarely generate.

## What this prototype does (short)
- Phase 1 — Money Habit Check: reads your allocations and uses an LLM to produce a short behavioural label (e.g., "Careful Saver"), a 0–100 behavioural score, a 6‑dimension fingerprint (home bias, safety seeking, FOMO, diversification, patience, recency bias), and a ghost (bias‑corrected) portfolio allocation.  
- Phase 2 — When This Breaks: given the ghost portfolio and user constraints (horizon, liquidity need, max drawdown, opportunity cost), the LLM returns precise tripwires (warning names, thresholds, timeframe, watch signals), a confidence level, and a one‑line verdict (PROCEED / PROCEED WITH CAUTION / DO NOT PROCEED).  
- UI details: the app enforces that total allocation must equal 100% before analysis is allowed; outputs are presented as cards with allocation bars, a radar fingerprint, a simple 0–100 score, and readable tripwire cards.

## Who benefits
Primary: Indian HNI investors and family offices who prefer plain‑English guidance and quick, actionable warnings rather than dense tables.  
Secondary: product evaluators who want to see an LLM-driven UX for translating behavioural risk into operational signals (tripwires) for monitoring.

## Product decisions & tradeoffs (short)
- Chosen format: lightweight web UI — quick to demo and accessible to non-technical reviewers. Tradeoff: a browser app requires a third‑party LLM key and CORS-enabled APIs for live runs.  
- Scope: intentionally focused on interpretation + warning signals rather than portfolio execution or brokerage integrations. This keeps the product simple and auditably explainable.  
- Privacy: the UI stores the API key only in memory; if you deploy this publicly, move keys to a backend to avoid exposing them in the browser.

## How to run (recommended, reproducible)
1. Start a simple static server from the repository root (recommended to avoid file:// fetch/CORS edge cases):

```bash
# from the repo root
python -m http.server 8000
# then open in browser:
# http://localhost:8000/Task4/index.html
```

2. Open `Task4/index.html` in your browser.  
3. In the API Key box, paste your Groq API key (or another OpenAI-compatible key if you adapt the fetch call). The prototype currently uses the model name `llama-3.3-70b-versatile` in the code — confirm the model name from your provider console if you get model errors.  
4. Make your total allocation exactly `100%`, then click **Find My Money Style**. After Phase 1 completes, click **Find Warning Signs** to run Phase 2.

Notes:
- If you get CORS or model-not-found errors, either run with a server and correct key/model, or use the offline demo (instructions below).  
- The UI does no persistent storage; the API key stays only in the browser memory for the session.

## Offline demo / run without an API key (quick evaluator instructions)
If you do not have a Groq API key or cannot call the LLM from your browser, you can simulate the outputs directly in the browser console without editing files.

1. Open `Task4/index.html` in the browser (served or file).  
2. Open the devtools console and paste the following to inject sample Phase 1 + Phase 2 outputs and re-render the UI:

```javascript
// Sample fingerprint (Phase 1)
state.fingerprint = {
  behavioral_type: "Careful Saver",
  behavioral_description: "You prioritise safety and steady returns. You avoid big equity bets.",
  behavioral_score: 72,
  fingerprint: { home_bias: 65, safety_seeking: 78, fomo_exposure: 22, diversification: 55, patience_score: 68, recency_bias: 30 },
  ghost_portfolio: { equity_india: 20, equity_intl: 10, debt: 25, fd: 15, gold: 20, real_estate: 5, nifty50: 0, cash: 5 },
  return_drag: "0.8%",
  primary_shift: "Reduce home bias by moving 10% from Indian equities to diversified debt",
  insights: ["You hold more home bias than necessary.", "Consider moving a small portion to debt for stability.", "Start with a 10% rebalance test."]
};

// Sample inversion (Phase 2)
state.inversion = {
  decision_summary: "Move 10% from Indian Equities to Debt",
  tripwires: [
    { label: "Equity Collapse", asset: "Indian Equities", condition: "falls more than", threshold: "-25%", timeframe: "within 12 months", context: "A 25% fall would wipe out most of the proposed gain and force painful selling.", probability: "medium", watch_signal: "NIFTY drops by 12% in one month" },
    { label: "Liquidity Shock", asset: "Cash", condition: "drops below", threshold: "3% of portfolio", timeframe: "in year 1-2", context: "If you need cash, rebalancing becomes hard.", probability: "low", watch_signal: "Large family expense planned" }
  ],
  confidence_level: 76,
  neutral_scenario: "If markets stay steady, both choices perform similarly over 5 years.",
  pre_mortem: "If inflation spikes, debt returns may lag; if equities rally, the move will underperform.",
  verdict: "PROCEED WITH CAUTION",
  verdict_reasoning: "Reasonable for preserving capital but limits upside"
};

render();
```

This produces the same UI artifacts as a live LLM: fingerprint card, ghost portfolio bars, and tripwires.

## Exact README fixes applied / suggested (do these edits)
1. Add the 3‑sentence "Why I built this" block above (done here).  
2. Add the "How to run" section with the `python -m http.server` notes (done here).  
3. Add the "Product decisions" bullets so evaluators see the persona and tradeoffs (done here).  
4. Add an offline demo option (the browser console snippet above) so reviewers can run without an API key (done here).

## Next improvements (priority suggestions)
- Add a small crash-survival indicator (a deterministic calculator that estimates portfolio loss under a 2008-style drawdown scenario) so this prototype ties directly to Task 1 metrics. This can be a 1‑function deterministic slider and a single line of UI text.  
- Make a demo toggle in `Task4/index.html` that returns canned JSON when `?demo=1` is present in the URL, or add a `demo` checkbox. I can implement this patch if you want.  
- Move API calls to a tiny server-side proxy to hide keys and avoid CORS; for a polished demo, add instructions and a small `server.py` with a single endpoint.

## Files touched / created
- `Task4/index.html` — main prototype UI & client LLM calls (existing).  
- `Task4/readme4.md` — this file (new) with rationale, run steps, and demo instructions.

---

If you'd like, I can now (choose one):
- A) Patch `Task4/index.html` to add an explicit demo toggle (`?demo=1`) and canned responses (no API call) — quick.  
- B) Patch `Task4/index.html` to add the "HNI family" header copy and a one-line crash-survival indicator (deterministic).  
- C) Do both A + B.

Tell me which option you want and I'll apply the code changes and test locally.