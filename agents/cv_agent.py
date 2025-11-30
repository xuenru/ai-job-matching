"""CV Agent for parsing resumes using ADK."""

from typing import Any

from core.logger import get_logger
from core.parsing_schemas import ResumeSchema
from core.utils import get_cache, read_markdown_file, write_json_file


class CVAgent:
    """Agent responsible for parsing resume markdown into structured JSON."""

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.cache = get_cache()
        self.logger = get_logger()

        # Initialize ADK client (optional - for real LLM calls)
        # For prototype, we use deterministic parsing
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

        # Parse resume (deterministic for prototype)
        if self.use_llm:
            resume_data = self._parse_with_llm(resume_text)
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
        Parse resume using LLM (for future implementation).
        """
        self.logger.increment_metric("llm_calls")

        # This would use ADK's LLM capabilities
        # For now, fall back to deterministic
        return self._parse_deterministic(resume_text)
