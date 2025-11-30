"""CV Agent for parsing resumes using ADK."""

from typing import Any

from core.logger import get_logger
from core.parsing_schemas import ResumeSchema
from core.utils import get_cache, read_markdown_file, write_json_file


class CVAgent:
    """Agent responsible for parsing resume markdown into structured JSON."""

    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.model_name = model_name
        self.cache = get_cache()
        self.logger = get_logger()

        # Initialize ADK agent
        self.use_llm = True
        try:
            import uuid

            from google.adk import Runner
            from google.adk.agents.llm_agent import Agent
            from google.adk.sessions import InMemorySessionService
            from google.genai.types import Content, Part

            self.agent = Agent(
                model=model_name,
                name="cv_parser",
                description="Parses resumes into structured JSON.",
                instruction="You are an expert resume parser. Your goal is to extract structured information from a resume markdown text and output it as a valid JSON object.",
            )
            self.session_service = InMemorySessionService()
            self.app_name = "agents"
            self.Runner = Runner
            self.Content = Content
            self.Part = Part
            self.uuid = uuid
        except ImportError:
            self.logger.error("google-adk not installed. Falling back to deterministic parsing.")
            self.use_llm = False

    def parse_resume(self, resume_path: str, use_cache: bool = True) -> ResumeSchema:
        """
        Parse resume markdown file into structured JSON.
        Uses cache if available and enabled.
        """
        self.logger.info(f"Parsing resume: {resume_path}")

        # Check cache first
        cache_key = f"resume_{resume_path}"
        if use_cache and self.cache.exists(cache_key, prefix="resume"):
            self.logger.info("Resume found in cache")
            self.logger.increment_metric("cache_hits")
            cached_data = self.cache.get(cache_key, prefix="resume")
            if cached_data and "data" in cached_data:
                return ResumeSchema(**cached_data["data"])

        self.logger.increment_metric("cache_misses")

        # Read resume file
        resume_text = read_markdown_file(resume_path)

        # Parse resume
        if self.use_llm:
            try:
                resume_data = self._parse_with_llm(resume_text)
            except Exception as e:
                self.logger.error(f"LLM parsing failed: {e}. Falling back to deterministic.")
                resume_data = self._parse_deterministic(resume_text)
        else:
            resume_data = self._parse_deterministic(resume_text)

        # Create schema object
        resume_schema = ResumeSchema(**resume_data)

        # Cache the result
        self.cache.set(cache_key, resume_schema.model_dump(), prefix="resume")
        self.logger.increment_metric("resumes_parsed")

        # Also save to output for reference
        write_json_file("cache/resume_parsed.json", resume_schema.model_dump())
        self.logger.info("Resume parsed and cached successfully")

        return resume_schema

    def _parse_deterministic(self, resume_text: str) -> dict[str, Any]:
        """
        Deterministic parsing logic for prototype.
        Extracts structured data from resume markdown.
        """
        self.logger.info("Parsing resume deterministically...")
        lines = resume_text.split("\n")

        # Extract name (first line, usually a heading)
        name = lines[0].strip("#").strip() if lines else "Unknown"

        # Extract skills
        skills = []
        domains = []
        languages_list = []
        education = []
        projects = []
        years_exp = 0

        in_skills_section = False
        in_education_section = False

        for _, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Skills section
            if "skills" in line_lower or "domaines" in line_lower:
                in_skills_section = True
                in_education_section = False
                continue

            # Education section
            if "education" in line_lower or "formation" in line_lower:
                in_education_section = True
                in_skills_section = False
                continue

            # Professional experience section
            if "professional experience" in line_lower or "experience" in line_lower:
                in_skills_section = False
                in_education_section = False

            # Parse skills section
            if in_skills_section and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    values = parts[1].strip()

                    if "domain" in key or "domaines" in key:
                        domains = [v.strip() for v in values.split(",")]
                    elif "language" in key:
                        skills.extend([v.strip() for v in values.split(",")])
                    elif "framework" in key:
                        skills.extend([v.strip() for v in values.split(",")])
                    elif "database" in key:
                        skills.extend([v.strip() for v in values.split(",")])
                    elif "tool" in key or "cloud" in key:
                        skills.extend([v.strip() for v in values.split(",")])

            # Parse education section
            if in_education_section and (line.strip().startswith("-") or "," in line):
                education.append(line.strip("- ").strip())

            # Extract years of experience
            if (
                "(" in line
                and "-" in line
                and ("now" in line_lower or "2024" in line or "2025" in line)
            ):
                # Try to extract start year
                import re

                year_match = re.search(r"(\d{2})/(\d{4})", line)
                if year_match:
                    start_year = int(year_match.group(2))
                    current_year = 2025
                    years_exp = max(years_exp, current_year - start_year)

        # Detect seniority based on years
        if years_exp >= 10:
            seniority = "Senior"
        elif years_exp >= 5:
            seniority = "Senior"
        elif years_exp >= 3:
            seniority = "Mid"
        else:
            seniority = "Junior"

        # Extract languages from text
        text_lower = resume_text.lower()
        if "french" in text_lower or "français" in text_lower:
            languages_list.append("French")
        if "english" in text_lower or "anglais" in text_lower:
            languages_list.append("English")

        # Extract domains from text analysis
        if "ai" in text_lower or "machine learning" in text_lower or "llm" in text_lower:
            if "AI" not in domains:
                domains.append("AI")
        if "data" in text_lower and ("engineer" in text_lower or "science" in text_lower):
            if "Data Engineering" not in domains:
                domains.append("Data Engineering")
        if "mlops" in text_lower or "devops" in text_lower:
            if "MLOps" not in domains:
                domains.append("MLOps")

        # Extract key skills from text
        skill_keywords = [
            "Python",
            "Scala",
            "Java",
            "TypeScript",
            "JavaScript",
            "LangChain",
            "LangGraph",
            "PyTorch",
            "TensorFlow",
            "Keras",
            "FastAPI",
            "Flask",
            "Django",
            "Docker",
            "Kubernetes",
            "AWS",
            "GCP",
            "Azure",
            "Spark",
            "Airflow",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "RAG",
            "LLM",
        ]

        for keyword in skill_keywords:
            if keyword.lower() in text_lower and keyword not in skills:
                skills.append(keyword)

        # Extract projects (simplified)
        if "rag" in text_lower:
            projects.append("RAG system implementation")
        if "mlops" in text_lower or "ml pipeline" in text_lower:
            projects.append("ML pipeline development")

        return {
            "name": name,
            "contact": {"email": "", "location": "France"},
            "years_of_experience": years_exp,
            "seniority": seniority,
            "skills": list(set(skills)),
            "domains": list(set(domains)),
            "languages": languages_list,
            "education": education if education else ["Master's degree"],
            "projects": projects if projects else ["Various ML/AI projects"],
            "preferred_location": "France",
            "other_notes": "Experienced AI/ML engineer with focus on production systems",
        }

    def _parse_with_llm(self, resume_text: str) -> dict[str, Any]:
        """
        Parse resume using LLM.
        """
        self.logger.info("Parsing resume with LLM...")
        self.logger.increment_metric("llm_calls")

        prompt = f"""
        Parse the following resume markdown into a JSON object with the following structure:
        {{
            "name": str,
            "contact": {{ "email": str, "location": str }},
            "years_of_experience": int,
            "seniority": str (Junior, Mid, Senior),
            "skills": list[str],
            "domains": list[str],
            "languages": list[str],
            "education": list[str],
            "projects": list[str],
            "preferred_location": str,
            "other_notes": str
        }}

        Resume Text:
        {resume_text}

        Return ONLY the JSON object, no markdown formatting.
        IMPORTANT: Use empty strings "" for missing values, do NOT use null.
        """

        # Create session ID
        session_id = str(self.uuid.uuid4())

        # Create runner
        runner = self.Runner(
            agent=self.agent, app_name=self.app_name, session_service=self.session_service
        )

        # Run async wrapper
        import asyncio

        async def run_agent():
            # Create session async
            await self.session_service.create_session(
                app_name=self.app_name, session_id=session_id, user_id="user"
            )

            content = self.Content(role="user", parts=[self.Part(text=prompt)])
            events_list = []
            async for event in runner.run_async(
                user_id="user", session_id=session_id, new_message=content
            ):
                events_list.append(event)
            return events_list

        try:
            events = asyncio.run(run_agent())
        except Exception as e:
            self.logger.error(f"Async run failed: {e}")
            raise e

        response_text = ""
        for event in events:
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # Parse JSON from response
        import json
        import re

        # Extract JSON block if present
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # Try parsing the whole response
            return json.loads(response_text)
