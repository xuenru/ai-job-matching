"""Job Agent for parsing job postings using ADK."""
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

# Optional: Import Google ADK when available (for future LLM integration)
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from core.parsing_schemas import JobSchema
from core.utils import get_cache, read_markdown_file, write_json_file, get_all_job_files
from core.logger import get_logger


class JobAgent:
    """Agent responsible for parsing job posting markdown into structured JSON."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.cache = get_cache()
        self.logger = get_logger()
        
        # Initialize ADK client (optional - for real LLM calls)
        # For prototype, we use deterministic parsing
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
            self.logger.increment_metric('cache_hits')
            cached_data = self.cache.get(cache_key, prefix="job")
            if cached_data and 'data' in cached_data:
                return JobSchema(**cached_data['data'])
        
        self.logger.increment_metric('cache_misses')
        
        # Read job file
        job_text = read_markdown_file(job_path)
        
        # Parse job (deterministic for prototype)
        if self.use_llm:
            job_data = self._parse_with_llm(job_text, job_id)
        else:
            job_data = self._parse_deterministic(job_text, job_id)
        
        # Create schema object
        job_schema = JobSchema(**job_data)
        
        # Cache the result
        self.cache.set(cache_key, job_schema.model_dump(), prefix="job")
        self.logger.increment_metric('jobs_parsed')
        
        self.logger.info(f"Job {job_id} parsed and cached successfully")
        
        return job_schema
    
    def parse_all_jobs(self, jobs_dir: str = "JDs", use_cache: bool = True) -> List[JobSchema]:
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
    
    def _parse_deterministic(self, job_text: str, job_id: str) -> Dict[str, Any]:
        """
        Deterministic parsing logic for prototype.
        Extracts structured data from job posting markdown.
        """
        lines = job_text.split('\n')
        
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
            if line_stripped.startswith('#') and not title:
                title = line_stripped.strip('#').strip()
                continue
            
            # Extract company
            if line_lower.startswith('**company'):
                company = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else ""
                continue
            
            # Extract location
            if line_lower.startswith('**location'):
                location = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else ""
                continue
            
            # Extract contract
            if line_lower.startswith('**contract'):
                contract = line_stripped.split(':', 1)[1].strip() if ':' in line_stripped else "Full-time"
                continue
            
            # Identify sections
            if '## responsibilities' in line_lower or '## description' in line_lower:
                current_section = 'responsibilities'
                continue
            elif '## requirements' in line_lower or '## qualifications' in line_lower:
                current_section = 'requirements'
                continue
            elif '## nice to have' in line_lower or '## preferred' in line_lower or '## benefits' in line_lower:
                current_section = 'nice_to_have'
                continue
            
            # Parse content based on current section
            if current_section == 'responsibilities':
                if line_stripped and not line_stripped.startswith('##'):
                    responsibilities += line_stripped + " "
            elif current_section == 'requirements':
                if line_stripped.startswith('-'):
                    req = line_stripped.strip('- ').strip()
                    if req:
                        requirements.append(req)
                elif line_stripped and not line_stripped.startswith('##'):
                    # Handle requirements not in list format
                    if '.' in line_stripped:
                        for req in line_stripped.split('.'):
                            req = req.strip()
                            if req and len(req) > 3:
                                requirements.append(req)
            elif current_section == 'nice_to_have':
                if line_stripped.startswith('-'):
                    nice = line_stripped.strip('- ').strip()
                    if nice:
                        nice_to_have.append(nice)
        
        # Detect seniority from title or requirements
        title_lower = title.lower()
        requirements_text = ' '.join(requirements).lower()
        
        if 'senior' in title_lower or 'lead' in title_lower:
            seniority = "Senior"
        elif 'junior' in title_lower:
            seniority = "Junior"
        elif '5+' in requirements_text or '5 years' in requirements_text:
            seniority = "Senior"
        elif '3+' in requirements_text or '3 years' in requirements_text:
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
            "raw_text": job_text
        }
    
    def _parse_with_llm(self, job_text: str, job_id: str) -> Dict[str, Any]:
        """
        Parse job using LLM (for future implementation).
        """
        self.logger.increment_metric('llm_calls')
        
        # This would use ADK's LLM capabilities
        # For now, fall back to deterministic
        return self._parse_deterministic(job_text, job_id)
