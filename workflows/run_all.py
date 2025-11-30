"""Complete workflow that runs all steps."""
from workflows.parse_resume import parse_resume_workflow
from workflows.parse_jobs import parse_jobs_workflow
from workflows.match_jobs import match_jobs_workflow
from core.logger import get_logger


def run_all_workflow(
    resume_path: str = "resume.md",
    jobs_dir: str = "JDs",
    output_path: str = "output/ranked_jobs.json",
    use_cache: bool = True
):
    """
    Run complete job matching pipeline.
    
    Args:
        resume_path: Path to resume markdown file
        jobs_dir: Directory containing job posting markdown files
        output_path: Path to save ranked results
        use_cache: Whether to use cached results if available
    
    Returns:
        RankedJobsOutput object
    """
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("STARTING COMPLETE JOB MATCHING PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Run complete workflow
        result = match_jobs_workflow(
            resume_path=resume_path,
            jobs_dir=jobs_dir,
            output_path=output_path,
            use_cache=use_cache
        )
        
        # Log final metrics
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.log_metrics()
        
        return result
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise


if __name__ == "__main__":
    run_all_workflow()
