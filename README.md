# Task 1 Implementation Summary

I started by understanding the full problem statement carefully and created a strong prompt for ChatGPT so it could explain the problem in simple English. My goal was to clearly understand what needed to be solved, what evaluators were expecting, and how to maximize marks according to the evaluation schema.

After that, I asked for a detailed step-by-step implementation prompt that covered all topics, including bonus questions, input/output handling, and the best tech stack for the project. I specifically asked it to respond as an expert in wealth management, AI, and portfolio risk analysis so the guidance would be practical and professional rather than generic.

While working on Task 1, I checked whether I should use NumPy and Pandas in `models.py` for better accuracy. DeepSeek analyzed my code and suggested that my current simple Python logic was already the better choice. Since the task only involved a maximum of around 3 assets, using NumPy or Pandas would add unnecessary complexity without improving performance. Simple Python made the code easier to debug, explain, and defend during interviews. I decided to continue with my current logic because if the asset count increases significantly in the future (like 10,000+ assets), NumPy or Pandas can always be added later without any problem.

Then I used Claude to help decide the best overall tech stack for the entire project. I uploaded the problem statement description and asked for a professional breakdown of Task Overview, Tech Stack Decision, Project Structure, Folder Structure, README strategy, and step-by-step implementation for each task. I specifically requested production-quality thinking and startup-level architecture so the project would look like work from someone ready to join Timecell, not just an assignment submission.

Claude provided guidance on the project structure, recommended Python files for implementation, and explained why CLI-first solutions were better for this assignment. Based on that, I created the required Python files and started implementing each section of Task 1.

Once the initial code was written, I verified the formulas and logic using multiple AI tools and different trusted sources to ensure that the portfolio calculations were mathematically correct. I wanted to make sure the formulas were reliable before moving forward.

After writing the code, I tested everything using the terminal. During testing, I found that some required libraries were missing, so I installed them using GitHub Copilot Free inside VS Code.

Next, I noticed that the output formatting in `visualize.py` was not looking clean or professional. To improve the presentation, I used the GPT-5.2 Code Model inside GitHub Copilot and gave a prompt to redesign the output so it would look well-structured, readable, and properly separated with good spacing. This improved the final terminal output significantly.

After that, I realized there were still many missing edge cases inside `main.py`. I went to DeepSeek and gave a prompt asking it to add all possible edge cases, especially for every `if-else` condition used inside the risk calculator, and also provide example cases for each condition. It returned updated code files with better validation and safer logic.

However, after running the updated code, I found an error related to the “no-assets” edge case. I copied the same code back to DeepSeek and realized there was something wrong in the calculator file, so I asked it to generate the calculator logic again.

Even in the regenerated version, one important edge case was still missing. I manually identified and fixed that case myself. After that correction, all edge cases worked properly, and the program handled all expected scenarios successfully.

Finally, I used GPT again to improve code readability by converting variable names into meaningful names such as `total_allocation`, `post_crash_asset_value`, and similar descriptive names. I also asked it to add simple English comments and improve the code structure so that the project would look professional, understandable.

In this way, I completed Task 1 with proper logic verification, edge case handling, clean code structure, professional formatting, and strong implementation quality.
