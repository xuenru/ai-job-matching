"""Workflow for parsing resume."""

from agents.cv_agent import CVAgent
from core.logger import get_logger


def parse_resume_workflow(resume_path: str = "resume.md", use_cache: bool = True):
    """
    Workflow to parse resume from markdown to structured JSON.

    Args:
        resume_path: Path to resume markdown file
        use_cache: Whether to use cached results if available

    Returns:
        ResumeSchema object
    """
    logger = get_logger()
    logger.info("=== Starting Resume Parsing Workflow ===")

    # Initialize CV Agent
    cv_agent = CVAgent()

    # Parse resume
    resume = cv_agent.parse_resume(resume_path, use_cache=use_cache)

    logger.info("Resume parsing completed successfully")
    logger.info(f"Candidate: {resume.name}")
    logger.info(f"Experience: {resume.years_of_experience} years")
    logger.info(f"Skills: {len(resume.skills)} skills found")
    logger.info(f"Domains: {', '.join(resume.domains)}")

    return resume


if __name__ == "__main__":
    parse_resume_workflow()
