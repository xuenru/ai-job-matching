# I Built an AI Agent to Find My Dream Job (So I Don't Have To)

## The Problem: Job Hunting Fatigue
We've all been there. You spend hours scrolling through job boards, reading endless "Rockstar Ninja Developer" descriptions, only to realize half of them aren't a fit. The cognitive load of mapping your specific skills to vague requirements is exhausting.

I decided to stop the scroll and let AI do the heavy lifting. I built a personal **AI Job Matching Agent** using **Google's Agent Development Kit (ADK)** and **Gemini 2.5**. Instead of me reading 100 job descriptions, my agent does it—and tells me exactly which ones are worth my time.

## How It Works
The concept is simple: I give the agent my resume and a folder full of job descriptions. It acts as my personal career consultant, analyzing each role against my actual experience.

### The Tech Stack
- **Brain**: Gemini 2.5 Flash Lite (Fast, cost-effective, and smart enough for semantic matching).
- **Framework**: Google ADK (To manage the agent's "thought process").
- **Language**: Python.

## My Personal Career Agents
I designed three specialized agents to handle the pipeline:

### 1. The Resume Analyst (`CVAgent`)
First, the system needs to understand *me*.
- **What it does**: Reads my Markdown resume.
- **Why**: It extracts my hard skills, years of experience, and project history into a structured format. It knows I'm a "Senior Python Engineer" with "5 years of experience," not just a bag of keywords.

### 2. The Job Scout (`JobAgent`)
Then, it looks at the market.
- **What it does**: Scans job postings (from Markdown files).
- **Why**: It cuts through the fluff. It ignores the "free coffee" perks and isolates the core requirements: tech stack, seniority level, and responsibilities.

### 3. The Matchmaker (`MatchAgent`)
This is where the magic happens.
- **What it does**: It compares *Me* vs. *The Job*.
- **The Output**: It doesn't just say "Match: 85%". It tells me *why*.
    > "This is a great fit because you have the required Python and AWS experience. However, note that they ask for React, which isn't on your resume."

## Building with Google ADK
Using Google's ADK made this feel like building a real software system, not just a script.
- **Structured Thinking**: I used `Pydantic` models to ensure the AI outputs valid JSON, so my code never crashes on a hallucination.
- **Async Core**: I migrated the agents to use ADK's async runners, making the system snappy even when processing multiple jobs.

## The Result
Now, instead of reading 50 job posts, I run:
```bash
python cli.py run-all
```
And I get a ranked list:
1.  **Senior AI Engineer at TechCorp** (Score: 92/100) - *Apply immediately.*
2.  **Backend Dev at StartupX** (Score: 78/100) - *Good fit, but check the salary.*
3.  **Legacy Code Maintainer** (Score: 40/100) - *Skip.*

## Conclusion
Job hunting doesn't have to be a manual grind. By leveraging LLMs and agentic workflows, we can flip the script and make the job market come to us.

---
*The code is open source—clone it and find your next role!*
