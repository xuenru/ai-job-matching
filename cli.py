"""Command-line interface for the job matching system."""

import argparse
import sys

from dotenv import load_dotenv

from core.logger import get_logger
from core.utils import get_cache
from workflows.match_jobs import match_jobs_workflow
from workflows.parse_jobs import parse_jobs_workflow
from workflows.parse_resume import parse_resume_workflow
from workflows.run_all import run_all_workflow

# Load environment variables
load_dotenv()

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Job Matching System using Google ADK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python cli.py run-all

  # Parse resume only
  python cli.py parse-resume

  # Parse jobs only
  python cli.py parse-jobs

  # Match jobs (requires resume and jobs already parsed)
  python cli.py match

  # Clear cache
  python cli.py clear-cache
        """,
    )

    parser.add_argument(
        "command",
        choices=["parse-resume", "parse-jobs", "match", "run-all", "clear-cache"],
        help="Command to execute",
    )

    parser.add_argument(
        "--resume", default="resume.md", help="Path to resume markdown file (default: resume.md)"
    )

    parser.add_argument(
        "--jobs-dir", default="JDs", help="Directory containing job markdown files (default: JDs)"
    )

    parser.add_argument(
        "--output",
        default="output/ranked_jobs.json",
        help="Output path for ranked jobs (default: output/ranked_jobs.json)",
    )

    parser.add_argument("--no-cache", action="store_true", help="Disable cache usage")

    args = parser.parse_args()

    logger = get_logger()
    use_cache = not args.no_cache

    try:
        if args.command == "parse-resume":
            logger.info(f"Parsing resume: {args.resume}")
            result = parse_resume_workflow(args.resume, use_cache=use_cache)
            print("\n✓ Resume parsed successfully")
            print(f"  Candidate: {result.name}")
            print(f"  Experience: {result.years_of_experience} years")
            print(f"  Skills: {len(result.skills)}")
            print("  Cached at: cache/resume_parsed.json")

        elif args.command == "parse-jobs":
            logger.info(f"Parsing jobs from: {args.jobs_dir}")
            jobs = parse_jobs_workflow(args.jobs_dir, use_cache=use_cache)
            print(f"\n✓ {len(jobs)} jobs parsed successfully")
            for job in jobs:
                print(f"  - {job.title} at {job.company}")
            print("  Cached at: cache/jobs_parsed.json")

        elif args.command == "match":
            logger.info("Matching resume with jobs")
            result = match_jobs_workflow(
                args.resume, args.jobs_dir, args.output, use_cache=use_cache
            )
            if result:
                print("\n✓ Matching completed successfully")
                print(f"  Jobs evaluated: {len(result.ranked_jobs)}")
                if result.ranked_jobs:
                    print("\n  Top match:")
                    top = result.ranked_jobs[0]
                    print(f"    {top.title} at {top.company}")
                    print(f"    Score: {top.score:.2f}/100")
                    print(f"    Success likelihood: {top.success_likelihood}")
                print(f"\n  Results saved to: {args.output}")

        elif args.command == "run-all":
            logger.info("Running complete pipeline")
            result = run_all_workflow(args.resume, args.jobs_dir, args.output, use_cache=use_cache)
            if result:
                print("\n✓ Pipeline completed successfully")
                print(f"  Jobs evaluated: {len(result.ranked_jobs)}")
                if result.ranked_jobs:
                    print("\n  Top 3 matches:")
                    for i, job in enumerate(result.ranked_jobs[:3], 1):
                        print(f"    {i}. {job.title} at {job.company}")
                        print(f"       Score: {job.score:.2f}/100 ({job.success_likelihood})")
                print(f"\n  Results saved to: {args.output}")

        elif args.command == "clear-cache":
            cache = get_cache()
            logger.info("Clearing all cache")
            cache.clear()
            print("✓ Cache cleared successfully")

        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
