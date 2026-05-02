# My Development Journey

I uploaded a PDF containing all the prompts that were given to me by the LLM.

## Task 1 – Portfolio Risk Calculator

**1. Understanding the problem and tech stack**

First, I gave this prompt to ChatGPT:

> “I have uploaded the PDF. From this, explain the problem statement very clearly in simple English. What do we need to solve so that we can get the best marks according to the evaluation schema? Give me a general idea of how to implement this problem.”

ChatGPT explained the problem clearly, and I got a solid understanding of the project.

**2. Getting a detailed step‑by‑step prompt**

My next prompt was:

> “Based on the provided PDF, give me a detailed prompt that will help me build this project step by step in an easy manner, covering each topic in detail, including inputs, outputs, and bonus questions. Write a strict prompt by stating that you have expertise in wealth management, the AI domain, and portfolio risk analysis. In the prompt, also mention which tech stack I should use for this project and why that specific stack should be used, with proper reasons.”

**3. Using Claude for tech stack and project structure**

I took that prompt together with the PDF description and provided it to Claude (with extended thinking). Claude helped me decide the best overall tech stack for the entire project, guided me on project structure, recommended which Python files to create, and explained why CLI‑first solutions are better for this assignment. Based on that advice, I created the required Python files and started implementing Task 1 section by section.

**4. Verifying formulas and logic**

Once the initial code was written, I manually verified the formulas and logic using multiple AI tools and different trusted sources to ensure the portfolio calculations were mathematically correct. I wanted to be certain the formulas were reliable before moving forward. I decided to use numpy/pandas but after conversation with DeepSeek I continued with my current logic. If the asset count ever grows significantly (e.g., 10,000+ assets), NumPy/Pandas can be added later without any problem.

**5. Adding edge cases and fixing errors**

I realised there were still many missing edge cases inside `main.py`. I went to DeepSeek and gave a prompt asking it to 

> "add all possible edge cases – especially for every `if-else` condition used inside the risk calculator – and to provide example cases for each condition."

DeepSeek returned updated code files with better validation and safer logic.
However, after running the updated code, I found an error related to the “no‑assets” edge case. I copied the same code back to DeepSeek and realised there was something wrong in the calculator file, so I asked it to generate the calculator logic again.

Even in the regenerated version, one important edge case was still missing. I manually identified and fixed that case myself. After that correction, all edge cases worked properly, and the program handled every expected scenario successfully.

**6. Cleaning variable names and adding comments**

Finally, I used GPT again and gave the prompt:

> "Improve code readability – converting variable names into meaningful names such as `total_allocation`, `post_crash_asset_value`, and similar descriptive variable names and `compute_risk_metrics` similar descriptive function name. And also add simple English comments and improve the output structure overall code structure so that the project would look professional and understandable."

This improved the final terminal output significantly.

---

## Task 2 – Live Market Data Fetch

### 1. Starting Point – Same Prompt as Task 1

I used the same prompt I had given for Task 1, but this time I provided the **Task 2 description** and the **evaluation schema** to Claude. I explicitly asked Claude to use web search to find public APIs for:

- Twelve Data
- Alpha Vantage
- `yfinance`

Claude returned a task overview, explained which tech stack to use and why (in simple English), and suggested a project structure with initial code.

### 2. The API Endpoint Problem

The initial code Claude gave me had API endpoints that were not working.  
I manually visited the official websites of Twelve Data and Alpha Vantage, generated my own free API keys, and found the correct, working endpoints. Then I fed those back to Claude.


### 3. Adding Fallback Logic

I realised that a single free API key can hit rate limits or experience server errors.  
So I decided to implement a **fallback chain** – a prioritized list of APIs for each asset. The system tries each source in order; if one fails (rate limit, timeout, server error), it automatically moves to the next.

Based on research and recommendations from DeepSeek and Claude, I chose the following fallback orders.

#### Fallback Order by Asset

| **Asset** | **Priority 1** | **Priority 2** | **Priority 3** | **Priority 4** |
|-----------|----------------|----------------|----------------|----------------|
| **BTC** (Cryptocurrency) | Twelve Data | CoinGecko | Binance | CoinCap |
| **RELIANCE** (Stock – BSE) | Alpha Vantage | FCS API | yfinance | – |
| **NIFTY50** (Index – NSE) | Alpha Vantage | FCS API | yfinance | nsepy |

#### Why This Order?

- **Twelve Data** (for BTC) – closest to real‑time, low latency.
- **Alpha Vantage** (for stocks/indices) – reliable free tier, though rate‑limited.
- **FCS API** – generous free plan (500 calls/month), no credit card required.
- **yfinance** – excellent fallback but delayed by ~15 minutes for NSE/BSE data.
- **nsepy** – NSE‑specific library, useful as a last resort for NIFTY50.

This layered approach ensures the system always returns a price, even when one or two sources are temporarily down.


I went to the official documentation for each API to verify the correct model names and code structure. I then tested the code on my machine in a separate test file. After confirming it worked, I pasted the verified code into GitCopilot and instructed it to modify my current implementation accordingly.

### 4. Strict Evaluation & Feedback

After that, I ran the code in the terminal and generated a strict evaluation prompt using GPT by giving this prompt:

> *"Write a detailed prompt that has an expert software engineer specializing in API integrations, data fetching systems, AI domains, data pipelines, and error handling. Also check whether the code is professional or not, evaluate performance, and finally give me what I can improve in this code for Task 2."*

ChatGPT then gave me the best and strict prompt. After that, I used that prompt for GitCopilot as the evaluator, and the code file is already accessible.

### 5. Fixing API Key Errors & Global Failure Handling

I pasted that error back to Claude and gave this prompt using DeepSeek:

> *"Fix this problem – when an API key is missing, wrong, or half‑written, don't show an error or bug. Instead, we have `yfinance` and crypto APIs that work without an API key, so use those in such scenarios.  
> If every single asset fails (no price from any API for BTC, ETH, NIFTY50, RELIANCE – all of them), then log a critical error and exit the program.  
> Why? Because if you have no data at all to show in your table, there's no point in continuing. The program cannot produce any useful output.  
> What to do: Track how many assets succeeded. After trying all assets, check:  
> - If at least one asset succeeded → show that data (put "N/A" for the failed ones)  
> - If zero assets succeeded → log `"CRITICAL: No data from any source. Exiting."` and call `sys.exit(1)`"*

### 6. Environment Variables & Security

I also added a `.env` file to the code instead of hardcoding keys, because pushing hardcoded keys would expose them. So I integrated `.env` properly. I used GPT to make the code clean, have a proper structure, and output a well‑formatted table and also told it to add simple English comments so that by reading the function names, variable names, and comments, even a non‑technical person can understand what is going on.

---

## Task 3 – AI-Powered Portfolio Explainer

- By providing the Task-3 description and earlier used prompt, I generated the code for Task-3. It gave me code without the bonus part — just a simple Python script using an LLM API.
  
- I first used the Gemini model because it has a free API key. 

### Problem faced

```json
{
  "error": {
    "code": 404,
    "message": "models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ListModels to see the list of available models and their supported methods.",
    "status": "NOT_FOUND"
  }
}
```

After that, I went to the official documentation of Google AI Studio, checked their model compatibility, and found the code using the following method:

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)
```

Then I pasted this into Git Copilot and gave the prompt:

> *"Use the provided code structure and use the same model as in this code, because this code is from the official docs of Gemini (Google AI Studio)."*

- After that i decided to used the Groq model because it provides a free API key and is remarkably fast—often returning responses in under a second. Gemini is free too, but it quickly hits rate limits after just a one to two runs. I don't have paid access to OpenAI or Anthropic. For security, I stored the key in a .env file.

- After that, the issue was fixed. I found that sometimes the AI model did not give the output we required — specifically the one‑line verdict — even though it was clearly mentioned in the prompt. So I decided to use the `BaseModel` of Pydantic (a LangChain feature) to enforce the output format we want.

- I also told Git Copilot to add `HumanMessage`, `AIMessage`, and `SystemMessage` for clear message context to the LLM. It just printed the output, but as mentioned in the problem, we needed to print the AI raw response as well, so I asked it to add the API raw response.

### Prompting Journey: How I Asked an LLM to Generate the Perfect Prompt

Below is the actual sequence of prompts I gave to an LLM (DeepSeek, then Claude) to help me build the strict, production-ready prompt for Task‑3.

#### Step 1: The First Prompt I Gave to DeepSeek

> **My prompt:**  
> *"Write a detailed prompt for an AI that explains portfolio risk in simple English. It should say what the investor is doing well, what to change, and give a verdict: Aggressive, Balanced, or Conservative. Make it work for different portfolios. Not hardcoded."*

**What the LLM gave back:**  
A short, generic prompt like:  
*"You are a financial advisor. Explain the risk of this portfolio: {{portfolio}}..."* – no constraints, no format, no JSON. It allowed hallucinations and had no way to ensure the one‑line verdict appeared. When I used that prompt with my Gemini model, the results were inconsistent: sometimes missing the verdict, sometimes inventing numbers.

I realised I needed a **much more detailed and structured prompt**. So I learned all the important prompting techniques used in the current tech market for generating better prompts.

#### Step 2: Adding More Requirements – The Second Prompt

I went back to DeepSeek and added more explicit instructions, drawing from what I had learned about few‑shot examples and no‑hallucination rules.

> **My improved prompt:**  
> *"Generate a strict prompt for an LLM that:  
> - Has a clear role (friendly financial advisor)  
> - Uses only provided portfolio data (no hallucination)  
> - Includes a few‑shot example to lock in tone and format  
> - Outputs a valid JSON object with specific keys: risk_summary, doing_well, consider_changing with proper why reasons, verdict"*

**What the LLM gave back:**  
A much longer prompt with sections: Role, Rules, Few‑shot Example, Output JSON Schema. It was better, but still missing some things. The prompt didn’t specify how to handle **configurable tone** (beginner/experienced/expert). It didn’t tell the model to **separate raw API response from structured output** – my code needed both. The JSON schema was loose (e.g., no enum for verdict, no length limit for the summary).

#### Step 3: Third Prompt to DeepSeek (More Comprehensive)

> **My prompt:**  
> *"You need a strict and detailed prompt for an AI that takes as input a portfolio (same structure as Task 1) and generates a plain‑English explanation of the portfolio's risk, written in the tone of a friendly but honest financial advisor talking to a non‑expert client. The output must always include:  
> → A 3–4 sentence plain‑English summary of the portfolio's risk level  
> → One specific thing the investor is doing well  
> → One specific thing the investor should consider changing, and why  
> → A one‑line verdict: 'Aggressive', 'Balanced', or 'Conservative'.  
> The script should accept different portfolios (not hardcoded to one example). Write the prompt so that the LLM returns the raw API response and the extracted structured output separately. Make the tone configurable: 'beginner', 'experienced', or 'expert' — and adjust the prompt accordingly. You have all the context you need. Take your time, search the web for the best prompt examples (such as those on Hugging Face where good prompts exist), merge what you find helpful, and then produce a large, comprehensive prompt as requested."*

#### Step 4: Merging from Hugging Face and Other Sources

I searched online (Hugging Face prompt engineering guides, Google AI Studio docs, LangChain best practices). I found techniques like:  
- **Chain‑of‑thought + self‑critique** (used in many production prompts)  
- **Enum constraints** in JSON schema  
- **Strict no‑extra‑text** rule  
- **Tone adaptation guidelines** (word choice based on expertise level)

Then I gave a **very detailed prompt to Claude** (because Claude is very good at following complex instructions).

After that, I went to Claude, gave the Task‑3 description and an evaluation schema, and provided this prompt:

> *"Generate a strict, production-quality prompt for an LLM that enforces the following: a clear role definition, precise step-by-step instructions, strict use of only provided input data (no hallucination), adherence to a given few-shot example for format and tone, and output strictly in a valid JSON schema with no extra text. The prompt must include explicit constraints, validation rules, and a self-critique step where the model reviews and corrects its own output for correctness, consistency, completeness, and JSON validity before returning the final answer. Structure the prompt cleanly using sections (such as Role, Rules, Input, Task, and Output Format).*  
>   
> *You need a strict and detailed prompt for an AI that takes as input a portfolio (same structure as in Task 1) and generates a plain-English explanation of the portfolio's risk. To do this, the AI should also use the risk_calculator helpers that were used in Task 1. I have provided the code for better context. The explanation must be written in the tone of a friendly but honest financial advisor talking to a non-expert client. The output must always include the following:*  
> *- A 3–4 sentence plain-English summary of the portfolio's risk level*  
> *- One specific thing the investor is doing well*  
> *- One specific thing the investor should consider changing, and why*  
> *- A one-line verdict: 'Aggressive', 'Balanced', or 'Conservative'.*  
>   
> *The script should accept different portfolios (not hardcoded to one example). Write the prompt so that the LLM returns the raw API response and the extracted structured output separately. Make the tone configurable: 'beginner', 'experienced', or 'expert' — and adjust the prompt accordingly. You have all the context you need. Take your time, search the web for the best prompt examples (such as those on Hugging Face where good prompts exist), merge what you find helpful, and then produce a large, comprehensive prompt as requested."*

**What Claude gave back:**  
The **Version 4 prompt** shown in the previous answer – with all sections, tone guidelines, enum validation, and a clear separation instruction for raw vs structured output.

I then fixed the grammar and wording of that final prompt to ensure it was clean and production‑ready. It gave a long, detailed prompt covering each point I mentioned and also showed how to use this prompt in my code. I pasted it into Copilot, and after that the output became fine and good.

### Bonus Part 2 – LangGraph Loop and Validation

- For bonus part 2, I needed the help of LangGraph because I needed to use a loop, which is difficult with LangChain. So I told Git Copilot to update my code using LangGraph.

My prompt:

> *"Use LangGraph as we need to implement a loop in this code. Make a second LLM2 (Gemini) that gives two things: accepted or rejected (using BaseModel) and a summary of feedback if rejected. Whatever we receive from LLM1, send it to LLM2 for validation. It should just give 'accepted' or 'rejected' plus a summary of feedback on what we need to improve if rejected. If rejected, send it back to LLM1 again with a summary of what to improve for better quality. LLM2 should use the risk_metric_calculator from Task‑1 for checking accuracy. Set a maximum of 3 iterations; if rejected 3 times, exit the loop because we have a limit on Gemini’s free API calls."*

- I integrated LangSmith observability across LLM calls, automatically tracing token usage, latency, and cost per run for both the primary explanation and optional critique. I used the `@traceable` decorator to monitor each function separately (prompt building, API call, parsing), allowing us to see the exact input and output for every LLM call. This makes it easy to understand how the system is behaving at each step.

- This observability is especially useful for future production deployment, as it helps identify which specific calls are taking more time or consuming more tokens. Based on these insights, we can optimize prompts, reduce cost, and improve performance.

- I generated the evaluation prompt for Task‑3 using Claude, and used that prompt in Git Copilot but with a different model (Gemini 3.2 Pro) to get better evaluation. It gave a small change of 2, and I said to fix it. In this way, I finished these tasks.

---

# Task 4 — Fingerprint Analyzer + Assumption Inversion

## Live Demo
👉 [https://wonderful-brigadeiros-9c8c80.netlify.app/](https://wonderful-brigadeiros-9c8c80.netlify.app/)

## The Problem

Most investment tools only show numbers – returns, risk, allocation.  
They do **not** explain *why* you make certain choices or *when* those choices could fail.

Indian HNI families often invest based on hidden habits and biases (home bias, safety-seeking, recency) rather than a clear strategy.  
The real problem is not a lack of data. It is the lack of a clear connection between:

- **How you think** (behaviour & biases)
- **When that thinking leads to poor outcomes** (failure conditions)

### Who This Is For

**Indian HNI families** – multi‑generational households and family offices.  
These users typically:

- Hold large illiquid assets (real estate, gold, private businesses)
- Prefer simple, plain‑English explanations over dense tables
- Care deeply about downside protection and want to know what could go wrong
- Often rely on a single advisor or personal judgment, not a structured process

TimeCell already helps with decision‑making. This feature adds the missing layer:  
behavioural diagnosis + concrete warning signals.

### Why This Isn’t Already Solved

Existing tools fall into three categories, each missing something critical:

| Tool Type | What It Does | What It Misses |
|-----------|--------------|----------------|
| **Portfolio dashboards** (MF Utility, smallcase) | Shows allocation & performance | No behavioural risk or failure conditions |
| **Risk profiling questionnaires** | Labels you “conservative” or “aggressive” | No link to real‑world failure scenarios |
| **Robo‑advisors** | Suggests portfolios mathematically | Hides assumptions; no clear warning signals |

**No mainstream solution** (especially for Indian HNIs) connects **behaviour** with **tripwires** – simple conditions like *“if X happens, your strategy breaks”*.  
Task 4 fills that gap.

### The Unique Value: Behaviour → Failure Conditions

Most tools stop at saying *“you have a safety bias”*.  
This tool goes further.

### Phase 1 – Behavioural Fingerprint
- Converts your portfolio into a human‑readable profile (e.g., “Careful Saver”)
- Identifies key biases (safety‑seeking, home bias, etc.)
- Suggests a **“ghost portfolio”** – a more balanced, rational alternative

### Phase 2 – Assumption Inversion
- Takes the ghost portfolio and asks: *“When would this decision become a bad idea?”*
- Returns clear **tripwires** – e.g.:
  - Equity falls more than 25%
  - Inflation rises above 6% for 3 years
  - Liquidity drops below 3 months of expenses
- Also gives: confidence level + verdict (PROCEED / CAUTION / DO NOT PROCEED)

**Result** – vague anxiety (“should we worry?”) becomes concrete, monitorable rules (“if NIFTY drops 25%, we sell”).

### How to Run the Prototype

#### Option 1: Live Demo (No Installation)
👉 [https://wonderful-brigadeiros-9c8c80.netlify.app/](https://wonderful-brigadeiros-9c8c80.netlify.app/)

**Steps:**

1. **Enter a Groq API key** – get free key from [console.groq.com](https://console.groq.com). Key stays only in browser memory.
2. **Fill portfolio allocation** – use sliders or input fields.
3. **Ensure total = 100%** – the tool will block analysis until sum is correct.
4. **Click “Find My Money Style” (Phase 1)** – get behavioural label, bias scores, ghost portfolio.
5. **Click “Find Warning Signs” (Phase 2)** – get tripwires, confidence, final verdict.

#### Option 2: Offline Demo (No API Key)

Open the live demo or local `index.html`, open browser console (F12), and paste:

```javascript
state.fingerprint = {
  behavioral_type: "Careful Saver",
  behavioral_description: "You prioritise safety and steady returns.",
  behavioral_score: 72,
  fingerprint: { home_bias: 65, safety_seeking: 78, fomo_exposure: 22, diversification: 55, patience_score: 68, recency_bias: 30 },
  ghost_portfolio: { equity_india: 20, equity_intl: 10, debt: 25, fd: 15, gold: 20, real_estate: 5, nifty50: 0, cash: 5 },
  return_drag: "0.8%",
  primary_shift: "Reduce home bias by moving 10% from Indian equities to diversified debt",
  insights: ["You hold more home bias than necessary.", "Consider moving a small portion to debt for stability."]
};

state.inversion = {
  decision_summary: "Move 10% from Indian Equities to Debt",
  tripwires: [
    { label: "Equity Collapse", asset: "Indian Equities", condition: "falls more than", threshold: "-25%", timeframe: "within 12 months", context: "A 25% fall would wipe out most of the proposed gain.", probability: "medium", watch_signal: "NIFTY drops by 12% in one month" },
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

The UI will display sample outputs exactly like a live LLM call.

### How This Aligns with TimeCell’s Philosophy

TimeCell is about **asking better questions** and **thinking clearly under uncertainty**.

This feature directly implements that:

- Better question: not “what is your risk tolerance?” but **“what hidden assumption is in your allocation?”**
- Clearer thinking: not “markets are uncertain” but **“here are the exact conditions where your plan fails”**

The tool forces a **pre‑mortem** – a proven technique to reduce overconfidence and emotional bias.

### Conclusion

**Problem:** HNI families make portfolio choices driven by behavioural biases; they need a simple, plain‑English check that translates allocations into risks and concrete warning signals.

**User:** Indian HNI investors (family offices / multi‑generational households) who hold concentrated assets and need crash‑resilience guidance.  

**Why this matters:** Unlike numeric dashboards, this tool pairs a bias‑corrected “ghost portfolio” with tripwire warnings – actionable plain‑English advice that existing tools rarely generate.
