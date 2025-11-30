"""Workflow for matching resume with jobs."""
from agents.cv_agent import CVAgent
from agents.job_agent import JobAgent
from agents.match_agent import MatchAgent
from core.logger import get_logger


def match_jobs_workflow(
    resume_path: str = "resume.md",
    jobs_dir: str = "JDs",
    output_path: str = "output/ranked_jobs.json",
    use_cache: bool = True
):
    """
    Workflow to match resume with all jobs and generate rankings.
    
    Args:
        resume_path: Path to resume markdown file
        jobs_dir: Directory containing job posting markdown files
        output_path: Path to save ranked results
        use_cache: Whether to use cached results if available
    
    Returns:
        RankedJobsOutput object
    """
    logger = get_logger()
    logger.info("=== Starting Job Matching Workflow ===")
    
    # Initialize agents
    cv_agent = CVAgent()
    job_agent = JobAgent()
    match_agent = MatchAgent()
    
    # Parse resume
    logger.info("Step 1: Parsing resume...")
    resume = cv_agent.parse_resume(resume_path, use_cache=use_cache)
    
    # Parse jobs
    logger.info("Step 2: Parsing job postings...")
    jobs = job_agent.parse_all_jobs(jobs_dir, use_cache=use_cache)
    
    if not jobs:
        logger.error("No jobs found to match")
        return None
    
    # Match and rank
    logger.info("Step 3: Matching and ranking jobs...")
    ranked_output = match_agent.match_jobs(resume, jobs, output_path)
    
    # Display summary
    logger.info("=== Matching Results ===")
    logger.info(f"Total jobs evaluated: {len(ranked_output.ranked_jobs)}")
    
    if ranked_output.ranked_jobs:
        logger.info("\nTop 3 matches:")
        for i, job in enumerate(ranked_output.ranked_jobs[:3], 1):
            logger.info(f"{i}. {job.title} at {job.company}")
            logger.info(f"   Score: {job.score:.2f}/100 - {job.success_likelihood} success likelihood")
            logger.info(f"   Matched skills: {len(job.matched_skills)}")
            logger.info(f"   Missing skills: {len(job.missing_skills)}")
    
    logger.info(f"\nFull results saved to: {output_path}")
    
    return ranked_output


if __name__ == "__main__":
    match_jobs_workflow()
