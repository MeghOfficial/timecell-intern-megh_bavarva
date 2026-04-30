# My Development Journey

## Task 1 – Portfolio Risk Calculator: 

**1. Understanding the problem and tech stack**

First, I gave this prompt to ChatGPT:

> “I have uploaded the PDF. From this, explain the problem statement very clearly in simple English. What do we need to solve so that we can get the best marks according to the evaluation schema? Give me a general idea of how to implement this problem.”

ChatGPT explained the problem clearly, and I got a solid understanding of the project.

**2. Getting a detailed step‑by‑step prompt**

My next prompt was:

> “Based on the provided PDF, give me a detailed prompt that will help me build this project step by step in an easy manner, covering each topic in detail, including inputs, outputs, and bonus questions. Write a strict prompt by stating that you have expertise in wealth management, the AI domain, and portfolio risk analysis. In the prompt, also mention which tech stack I should use for this project and why that specific stack should be used, with proper reasons.”

ChatGPT generated a comprehensive prompt that framed me as a senior Wealth Management Engineer, Portfolio Risk Analyst, and AI Systems Architect. The prompt required a structured output for each task (overview, tech stack, project structure, step‑by‑step implementation, full code, bonus, README strategy, Loom strategy, selection strategy) and emphasised CLI‑first, startup‑ready thinking.


**3. Using Claude for tech stack and project structure**

I took that prompt together with the PDF description and provided it to Claude (with extended thinking). Claude helped me decide the best overall tech stack for the entire project, guided me on project structure, recommended which Python files to create, and explained why CLI‑first solutions are better for this assignment. Based on that advice, I created the required Python files and started implementing Task 1 section by section.

**4. Deciding not to use NumPy/Pandas**

I asked DeepSeek whether I should use NumPy and Pandas in `models.py` for better accuracy. DeepSeek analysed my code and suggested that my current simple Python logic was actually the better choice:

- No extra dependencies – runs anywhere with Python 3.10+.
- Easier to debug – plain loops and arithmetic are transparent.
- Faster for small portfolios (max ~3 assets) – vectorisation adds no benefit.
- Easier to explain and defend in interviews.

I decided to continue with my current logic. If the asset count ever grows significantly (e.g., 10,000+ assets), NumPy/Pandas can be added later without any problem.

**5. Verifying formulas and logic**

Once the initial code was written, I manually verified the formulas and logic using multiple AI tools and different trusted sources to ensure the portfolio calculations were mathematically correct. I wanted to be certain the formulas were reliable before moving forward.

**6. Testing and fixing missing libraries**

After writing the code, I tested everything using the terminal. During testing, I found that some required libraries were missing, so I installed them using GitHub Copilot Free inside VS Code.

**7. Improving visual output**

I noticed that the output formatting in `visualiser.py` was not clean or professional. To improve the presentation, I used the GPT‑5.2 Code Model inside GitHub Copilot and gave a prompt 
> " use visualiser.py and improved the code To redesign the output so it would look well‑structured, readable, and properly separated with good spacing. "

This improved the final terminal output significantly.

**8. Adding edge cases and fixing errors**

I realised there were still many missing edge cases inside `main.py`. I went to DeepSeek and gave a prompt asking it to 
> " add all possible edge cases – especially for every `if-else` condition used inside the risk calculator – and to provide example cases for each condition. " 

DeepSeek returned updated code files with better validation and safer logic.
However, after running the updated code, I found an error related to the “no‑assets” edge case. I copied the same code back to DeepSeek and realised there was something wrong in the calculator file, so I asked it to generate the calculator logic again.

Even in the regenerated version, one important edge case was still missing. I manually identified and fixed that case myself. After that correction, all edge cases worked properly, and the program handled every expected scenario successfully.

**9. Cleaning variable names and adding comments**

Finally, I used GPT again give Prompt
> " Improve code readability – converting variable names into meaningful names such as `total_allocation`, `post_crash_asset_value`, and similar descriptive variable names and `compute_risk_metrics` similar descriptive function name . and also add simple English comments and improve the overall code structure so that the project would look professional, understandable . "


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

### 3. Adding Fallback Logic – The Core Idea (Part 1)

I realised that a single free API key can hit rate limits or experience server errors.  
So I decided to implement a **fallback chain**:

1. **Try Twelve Data first** (closest to real‑time for crypto & indices)
2. If that fails, **try Alpha Vantage**
3. If both fail, **fall back to `yfinance`** (reliable but delayed by ~15 minutes for NSE stocks)

### 4. Fallback Logic – Source Priority Justification

I found this out from DeepSeek and Claude – they told me to use Twelve Data first as it gives near real-time data, then Alpha Vantage, and finally `yfinance` as it is delayed by nearly 10 to 15 minutes. This ensures the system always returns a price, even when one or two sources are down.

### 5. Fallback Logic – Implementation & Integration

I generated the code for this fallback logic using GPT, ran it in a test file, and then gave these files to Claude. I asked Claude to modify the previous code so that it implemented the fallback logic mentioned in my code.

### 6. Strict Evaluation & Feedback

After that, I ran the code in the terminal and generated a strict evaluation prompt using GPT by giving this prompt:

> *"Write a detailed prompt that has an expert software engineer specializing in API integrations, data fetching systems, AI domains, data pipelines, and error handling. Also check whether the code is professional or not, evaluate performance, and finally give me what I can improve in this code for Task 2."*

ChatGPT then gave me the best and strict prompt. After that, I used that prompt for GitCopilot as the evaluator, and the code file is already accessible.


### 7. Fixing API Key Errors & Global Failure Handling

I pasted that error back to Claude and said:

> *"Fix this problem – when an API key is missing, wrong, or half‑written, don't show an error or bug. Instead, we have `yfinance` and crypto APIs that work without an API key, so use those in such scenarios.  
> If every single asset fails (no price from any API for BTC, ETH, NIFTY50, RELIANCE – all of them), then log a critical error and exit the program.  
> Why? Because if you have no data at all to show in your table, there's no point in continuing. The program cannot produce any useful output.  
> What to do: Track how many assets succeeded. After trying all assets, check:  
> - If at least one asset succeeded → show that data (put "N/A" for the failed ones)  
> - If zero assets succeeded → log `"CRITICAL: No data from any source. Exiting."` and call `sys.exit(1)`"*

### 8. Environment Variables & Security

I also added a `.env` file to the code instead of hardcoding keys, because pushing hardcoded keys would expose them. So I integrated `.env` properly. I used GPT to make  the code clean, has a proper structure, and outputs a well‑formatted table and also tell to add simple English comments so that by reading the function names, variable names, and comments, even a non‑technical person can understand what is going on.
