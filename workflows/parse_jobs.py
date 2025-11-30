"""Workflow for parsing job postings."""

from agents.job_agent import JobAgent
from core.logger import get_logger


def parse_jobs_workflow(jobs_dir: str = "JDs", use_cache: bool = True):
    """
    Workflow to parse all job postings from markdown to structured JSON.

    Args:
        jobs_dir: Directory containing job posting markdown files
        use_cache: Whether to use cached results if available

    Returns:
        List of JobSchema objects
    """
    logger = get_logger()
    logger.info("=== Starting Job Parsing Workflow ===")

    # Initialize Job Agent
    job_agent = JobAgent()

    # Parse all jobs
    jobs = job_agent.parse_all_jobs(jobs_dir, use_cache=use_cache)

    logger.info("Job parsing completed successfully")
    logger.info(f"Total jobs parsed: {len(jobs)}")

    for job in jobs:
        logger.info(f"  - {job.title} at {job.company} ({job.location})")

    return jobs


if __name__ == "__main__":
    parse_jobs_workflow()
