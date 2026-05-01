# My Development Journey

## Task 1 – Portfolio Risk Calculator: 

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

Once the initial code was written, I manually verified the formulas and logic using multiple AI tools and different trusted sources to ensure the portfolio calculations were mathematically correct. I wanted to be certain the formulas were reliable before moving forward.I decided to use numpy/pandas but after conversation with deepseek i continue with my current logic. If the asset count ever grows significantly (e.g., 10,000+ assets), NumPy/Pandas can be added later without any problem.


**5. Adding edge cases and fixing errors**

I realised there were still many missing edge cases inside `main.py`. I went to DeepSeek and gave a prompt asking it to 
> " add all possible edge cases – especially for every `if-else` condition used inside the risk calculator – and to provide example cases for each condition. " 

DeepSeek returned updated code files with better validation and safer logic.
However, after running the updated code, I found an error related to the “no‑assets” edge case. I copied the same code back to DeepSeek and realised there was something wrong in the calculator file, so I asked it to generate the calculator logic again.

Even in the regenerated version, one important edge case was still missing. I manually identified and fixed that case myself. After that correction, all edge cases worked properly, and the program handled every expected scenario successfully.

**6. Cleaning variable names and adding comments**

Finally, I used GPT again give Prompt
> " Improve code readability – converting variable names into meaningful names such as `total_allocation`, `post_crash_asset_value`, and similar descriptive variable names and `compute_risk_metrics` similar descriptive function name . and also add simple English comments and improve the ouptut strcuture overall code structure so that the project would look professional, understandable ."
> This improved the final terminal output significantly.


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
So I decided to implement a **fallback chain**:

1. **Try Twelve Data first** (closest to real‑time for crypto & indices)
2. If that fails, **try Alpha Vantage**
3. If both fail, **fall back to `yfinance`** (reliable but delayed by ~15 minutes for NSE stocks)

I found this out from DeepSeek and Claude – they told me to use Twelve Data first as it gives near real-time data, then Alpha Vantage, and finally `yfinance` as it is delayed by nearly 10 to 15 minutes. This ensures the system always returns a price, even when one or two sources are down.


I generated the code for this fallback logic using GPT, ran it in a test file, and then gave these files to Claude. I asked Claude to modify the previous code so that it implemented the fallback logic mentioned in my code.

### 4. Strict Evaluation & Feedback

After that, I ran the code in the terminal and generated a strict evaluation prompt using GPT by giving this prompt:

> *"Write a detailed prompt that has an expert software engineer specializing in API integrations, data fetching systems, AI domains, data pipelines, and error handling. Also check whether the code is professional or not, evaluate performance, and finally give me what I can improve in this code for Task 2."*

ChatGPT then gave me the best and strict prompt. After that, I used that prompt for GitCopilot as the evaluator, and the code file is already accessible.


### 5. Fixing API Key Errors & Global Failure Handling

I pasted that error back to Claude and give these prompt using deepseek:

> *"Fix this problem – when an API key is missing, wrong, or half‑written, don't show an error or bug. Instead, we have `yfinance` and crypto APIs that work without an API key, so use those in such scenarios.  
> If every single asset fails (no price from any API for BTC, ETH, NIFTY50, RELIANCE – all of them), then log a critical error and exit the program.  
> Why? Because if you have no data at all to show in your table, there's no point in continuing. The program cannot produce any useful output.  
> What to do: Track how many assets succeeded. After trying all assets, check:  
> - If at least one asset succeeded → show that data (put "N/A" for the failed ones)  
> - If zero assets succeeded → log `"CRITICAL: No data from any source. Exiting."` and call `sys.exit(1)`"*

### 6. Environment Variables & Security

I also added a `.env` file to the code instead of hardcoding keys, because pushing hardcoded keys would expose them. So I integrated `.env` properly. I used GPT to make  the code clean, has a proper structure, and outputs a well‑formatted table and also tell to add simple English comments so that by reading the function names, variable names, and comments, even a non‑technical person can understand what is going on.


## Task 3 – AI-Powered Portfolio Explainer

- By providing the Task-3 description and earlier used prompt, I generated the code for Task-3. It gave me code without the bonus part — just a simple Python script using an LLM API.
- I used the Gemini model because it has a free API key, and I do not have any paid subscription for OpenAI or Anthropic. For confidentiality, I generated and added the key in a `.env` file.

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

After that, the issue was fixed. I found that sometimes the AI model did not give the output we required — specifically the one‑line verdict — even though it was clearly mentioned in the prompt. So I decided to use the `BaseModel` of Pydantic (a Langchain feature) to enforce the output format we want.

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

### Step 4: Merging from Hugging Face and Other Sources

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

- For bonus part 2, I needed the help of LangGraph because I needed to use a loop, which is difficult with Langchain. So I told Git Copilot to update my code using LangGraph.

My prompt:

> *"Use LangGraph as we need to implement a loop in this code. Make a second LLM2 (Gemini) that gives two things: accepted or rejected (using BaseModel) and a summary of feedback if rejected. Whatever we receive from LLM1, send it to LLM2 for validation. It should just give 'accepted' or 'rejected' plus a summary of feedback on what we need to improve if rejected. If rejected, send it back to LLM1 again with a summary of what to improve for better quality. LLM2 should use the risk_metric_calculator from Task‑1 for checking accuracy. Set a maximum of 3 iterations; if rejected 3 times, exit the loop because we have a limit on Gemini’s free API calls."*

- I also noticed a problem: the output was generated but not visible for some time, and then suddenly the output appeared in the terminal. This is not good when building a UI based on it, so I implemented the streaming feature available in LangGraph using their official docs with the help of Copilot.

- I generated the evaluation prompt for Task‑3 using Claude, and used that prompt in Git Copilot but with a different model (Gemini 3.2 Pro) to get better evaluation. It gave a small change of 2, and I said to fix it that way. In this way, I finished these tasks.
