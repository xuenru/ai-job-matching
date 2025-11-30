# Quick Start Guide

## Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
# or
make sync

# Install with dev dependencies (optional)
uv sync --extra dev
# or
make install-dev
```

## Run the System

```bash
# Run complete pipeline (recommended)
uv run python cli.py run-all
# or
make run

# Or run individual steps:
uv run python cli.py parse-resume      # Parse resume only
uv run python cli.py parse-jobs         # Parse jobs only
uv run python cli.py match              # Match and rank jobs
uv run python cli.py clear-cache        # Clear all cache
```

## Output Files

- `cache/resume_parsed.json` - Parsed resume in structured format
- `cache/jobs_parsed.json` - All parsed jobs
- `output/ranked_jobs.json` - Final ranked results with scores
- `cache/job_matcher_*.log` - Detailed logs

## Customization

Edit scoring weights in `core/scoring.py`:
- Skill match: 0-40 points
- Experience: 0-30 points
- Seniority: 0-10 points
- Location/Language: 0-10 points
- Semantic similarity: 0-10 points

## Testing

```bash
# Run unit tests with pytest
uv run pytest tests/
# or
make test

# Run tests with coverage
make test-cov

# Or using unittest
uv run python -m unittest discover tests/
```

## Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all checks
make check-all
```

## Input Files

- `resume.md` - Your resume in markdown format
- `JDs/*.md` - Job descriptions in markdown format

## Example Output

The system produces a JSON file with ranked jobs:
```json
{
  "ranked_jobs": [
    {
      "id": "job_ai_eng",
      "score": 66.4,
      "score_breakdown": {...},
      "title": "AI Engineer",
      "company": "TechCorp",
      "reason": "Excellent match...",
      "matched_skills": ["Python", "Docker", ...],
      "missing_skills": ["Kubernetes"],
      "success_likelihood": "High"
    }
  ]
}
```

## Next Steps

1. Update `resume.md` with your information
2. Add job postings to `JDs/` directory
3. Run `python3 cli.py run-all`
4. Review results in `output/ranked_jobs.json`
5. Check logs in `cache/` for details
