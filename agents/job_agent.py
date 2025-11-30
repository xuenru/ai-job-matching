"""Job Agent for parsing job postings using ADK."""

from pathlib import Path
from typing import Any

from core.logger import get_logger
from core.parsing_schemas import JobSchema
from core.utils import get_all_job_files, get_cache, read_markdown_file, write_json_file


class JobAgent:
    """Agent responsible for parsing job posting markdown into structured JSON."""

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
                name="job_parser",
                description="Parses job postings into structured JSON.",
                instruction="You are an expert job posting parser. Your goal is to extract structured information from a job posting markdown text and output it as a valid JSON object.",
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

    def parse_job(self, job_path: str, use_cache: bool = True) -> JobSchema:
        """
        Parse job posting markdown file into structured JSON.
        Uses cache if available and enabled.
        """
        self.logger.info(f"Parsing job: {job_path}")

        # Generate job ID from filename
        job_id = Path(job_path).stem

        # Check cache first
        cache_key = f"job_{job_path}"
        if use_cache and self.cache.exists(cache_key, prefix="job"):
            self.logger.info(f"Job {job_id} found in cache")
            self.logger.increment_metric("cache_hits")
            cached_data = self.cache.get(cache_key, prefix="job")
            if cached_data and "data" in cached_data:
                return JobSchema(**cached_data["data"])

        self.logger.increment_metric("cache_misses")

        # Read job file
        job_text = read_markdown_file(job_path)

        # Parse job
        if self.use_llm:
            try:
                job_data = self._parse_with_llm(job_text, job_id)
            except Exception as e:
                self.logger.error(f"LLM parsing failed: {e}. Falling back to deterministic.")
                job_data = self._parse_deterministic(job_text, job_id)
        else:
            job_data = self._parse_deterministic(job_text, job_id)

        # Create schema object
        job_schema = JobSchema(**job_data)

        # Cache the result
        self.cache.set(cache_key, job_schema.model_dump(), prefix="job")
        self.logger.increment_metric("jobs_parsed")

        self.logger.info(f"Job {job_id} parsed and cached successfully")

        return job_schema

    def parse_all_jobs(self, jobs_dir: str = "JDs", use_cache: bool = True) -> list[JobSchema]:
        """
        Parse all job posting files in directory.
        """
        self.logger.info(f"Parsing all jobs in: {jobs_dir}")

        job_files = get_all_job_files(jobs_dir)
        jobs = []

        for job_file in job_files:
            try:
                job_schema = self.parse_job(str(job_file), use_cache=use_cache)
                jobs.append(job_schema)
            except Exception as e:
                self.logger.error(f"Error parsing job {job_file}: {e}")

        self.logger.info(f"Parsed {len(jobs)} jobs")

        # Save all jobs to output
        jobs_data = [job.model_dump() for job in jobs]
        write_json_file("cache/jobs_parsed.json", {"jobs": jobs_data})

        return jobs

    def _parse_deterministic(self, job_text: str, job_id: str) -> dict[str, Any]:
        """
        Deterministic parsing logic for prototype.
        Extracts structured data from job posting markdown.
        """
        self.logger.info("Parsing job deterministically...")
        lines = job_text.split("\n")

        title = ""
        company = ""
        location = ""
        contract = "Full-time"
        responsibilities = ""
        requirements = []
        nice_to_have = []
        seniority = ""

        current_section = None

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Extract title (first heading)
            if line_stripped.startswith("#") and not title:
                title = line_stripped.strip("#").strip()
                continue

            # Extract company
            if line_lower.startswith("**company"):
                company = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
                continue

            # Extract location
            if line_lower.startswith("**location"):
                location = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
                continue

            # Extract contract
            if line_lower.startswith("**contract"):
                contract = (
                    line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else "Full-time"
                )
                continue

            # Identify sections
            if "## responsibilities" in line_lower or "## description" in line_lower:
                current_section = "responsibilities"
                continue
            elif "## requirements" in line_lower or "## qualifications" in line_lower:
                current_section = "requirements"
                continue
            elif (
                "## nice to have" in line_lower
                or "## preferred" in line_lower
                or "## benefits" in line_lower
            ):
                current_section = "nice_to_have"
                continue

            # Parse content based on current section
            if current_section == "responsibilities":
                if line_stripped and not line_stripped.startswith("##"):
                    responsibilities += line_stripped + " "
            elif current_section == "requirements":
                if line_stripped.startswith("-"):
                    req = line_stripped.strip("- ").strip()
                    if req:
                        requirements.append(req)
                elif line_stripped and not line_stripped.startswith("##"):
                    # Handle requirements not in list format
                    if "." in line_stripped:
                        for req in line_stripped.split("."):
                            req = req.strip()
                            if req and len(req) > 3:
                                requirements.append(req)
            elif current_section == "nice_to_have":
                if line_stripped.startswith("-"):
                    nice = line_stripped.strip("- ").strip()
                    if nice:
                        nice_to_have.append(nice)

        # Detect seniority from title or requirements
        title_lower = title.lower()
        requirements_text = " ".join(requirements).lower()

        if "senior" in title_lower or "lead" in title_lower:
            seniority = "Senior"
        elif "junior" in title_lower:
            seniority = "Junior"
        elif "5+" in requirements_text or "5 years" in requirements_text:
            seniority = "Senior"
        elif "3+" in requirements_text or "3 years" in requirements_text:
            seniority = "Mid"
        else:
            seniority = "Mid"

        return {
            "id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "contract": contract,
            "responsibilities": responsibilities.strip(),
            "requirements": requirements,
            "nice_to_have": nice_to_have,
            "seniority": seniority,
            "raw_text": job_text,
        }

    def _parse_with_llm(self, job_text: str, job_id: str) -> dict[str, Any]:
        """
        Parse job using LLM.
        """
        self.logger.info("Parsing job with LLM...")
        self.logger.increment_metric("llm_calls")

        prompt = f"""
        Parse the following job posting markdown into a JSON object with the following structure:
        {{
            "id": "{job_id}",
            "title": str,
            "company": str,
            "location": str,
            "contract": str,
            "responsibilities": str,
            "requirements": list[str],
            "nice_to_have": list[str],
            "seniority": str (Junior, Mid, Senior),
            "raw_text": str (original text)
        }}

        Job Posting:
        {job_text}

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

        # Parse JSON
        import json
        import re

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
        else:
            data = json.loads(response_text)

        # Ensure ID and raw_text are correct
        data["id"] = job_id
        data["raw_text"] = job_text

        return data
