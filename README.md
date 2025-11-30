# AI Job-Matching System using Google ADK

A complete multi-agent system for matching resumes with job postings, built using Google's Agent Development Kit (ADK). The system parses resumes and job descriptions, computes match scores across multiple dimensions, and produces ranked job recommendations.

## Features

- **Multi-Agent Architecture**: CV-Agent, Job-Agent, and Match-Agent working together
- **Intelligent Scoring**: 5-dimensional scoring system (skills, experience, seniority, location/language, semantic similarity)
- **Caching System**: Fast resume and job parsing with intelligent caching
- **Deterministic Embeddings**: Hash-based vector embeddings for semantic analysis
- **Comprehensive Logging**: Full observability with metrics tracking
- **CLI Interface**: Easy-to-use command-line interface
- **Modular Design**: Clean separation of concerns following ADK best practices

## Architecture

```
┌─────────────────┐
│   CV-Agent      │──> Parse resume.md → resume_parsed.json (cached)
└─────────────────┘

┌─────────────────┐
│   Job-Agent     │──> Parse JDs/*.md → jobs_parsed.json (cached)
└─────────────────┘

┌─────────────────┐
│  Match-Agent    │──> Compute scores → ranked_jobs.json
└─────────────────┘
```

## Scoring System

Total Score: 0-100 points

- **Skill Match** (40 points): Matching required and nice-to-have skills
- **Experience Alignment** (30 points): Domain expertise and years of experience
- **Seniority Fit** (10 points): Career level alignment
- **Location/Language** (10 points): Geographic and language compatibility
- **Semantic Similarity** (10 points): Overall profile-job description alignment

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone or download the project:
```bash
cd ai-job-matching
```

3. Sync dependencies:
```bash
uv sync
# or
make sync
```

4. (Optional) Install with development dependencies:
```bash
uv sync --extra dev
# or
make install-dev
```

5. Verify installation:
```bash
uv run python cli.py --help
```

## Project Structure

```
./
├── agents/                 # Agent implementations
│   ├── cv_agent.py        # Resume parsing agent
│   ├── job_agent.py       # Job posting parsing agent
│   └── match_agent.py     # Job matching agent
├── core/                   # Core utilities
│   ├── parsing_schemas.py # Data schemas (Pydantic)
│   ├── embeddings.py      # Embedding generation
│   ├── scoring.py         # Scoring logic
│   ├── utils.py           # Utilities & cache
│   └── logger.py          # Logging & metrics
├── workflows/              # Workflow orchestration
│   ├── parse_resume.py    # Resume parsing workflow
│   ├── parse_jobs.py      # Job parsing workflow
│   ├── match_jobs.py      # Matching workflow
│   └── run_all.py         # Complete pipeline
├── tests/                  # Unit tests
│   └── test_core.py       # Core module tests
├── cache/                  # Cached parsing results
├── output/                 # Final output files
├── JDs/                    # Job description markdown files
├── resume.md               # Resume markdown file
├── cli.py                  # CLI interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Usage

### Quick Start

Run the complete pipeline:
```bash
python cli.py run-all
```

This will:
1. Parse your resume from `resume.md`
2. Parse all job postings from `JDs/` directory
3. Compute match scores for all jobs
4. Save ranked results to `output/ranked_jobs.json`

### Individual Commands

#### Parse Resume Only
```bash
python cli.py parse-resume
```

Output: `cache/resume_parsed.json`

#### Parse Jobs Only
```bash
python cli.py parse-jobs
```

Output: `cache/jobs_parsed.json`

#### Match Jobs (requires parsed data)
```bash
python cli.py match
```

Output: `output/ranked_jobs.json`

#### Clear Cache
```bash
python cli.py clear-cache
```

### Advanced Options

Specify custom paths:
```bash
python cli.py run-all --resume my_resume.md --jobs-dir JDs/ --output output/results.json
```

Disable caching (force re-parsing):
```bash
python cli.py run-all --no-cache
```

## Input Formats

### Resume Format (resume.md)

Markdown file with the following sections:
- Professional Experience (with dates)
- Skills (categorized: Languages, Frameworks, Tools, etc.)
- Education
- Projects

Example:
```markdown
# John Doe | AI Engineer

## PROFESSIONAL EXPERIENCE

### AI Engineer - Company (01/2020 - Now)
Description of role...

## SKILLS

Languages: Python, TypeScript
Frameworks: LangChain, PyTorch, FastAPI
Databases: PostgreSQL, MongoDB

## EDUCATION

Master's in Computer Science
```

### Job Posting Format (JDs/*.md)

Markdown files with:
- Title
- Company
- Location
- Responsibilities
- Requirements
- Nice to have

Example:
```markdown
# Senior AI Engineer

**Company**: TechCorp
**Location**: Paris, France
**Contract**: Full-time

## Responsibilities
- Build AI systems
- Deploy ML models

## Requirements
- 5+ years Python experience
- Experience with LLMs
- Strong FastAPI skills

## Nice to have
- AWS experience
```

## Output Format

The system generates `output/ranked_jobs.json` with the following structure:

```json
{
  "ranked_jobs": [
    {
      "id": "job_ai_eng",
      "score": 85.5,
      "score_breakdown": {
        "skill_match": 35.0,
        "experience_alignment": 25.0,
        "seniority_fit": 10.0,
        "location_language": 8.0,
        "semantic_alignment": 7.5
      },
      "title": "Senior AI Engineer",
      "company": "Inato",
      "location": "Paris, France",
      "reason": "Excellent match with strong alignment...",
      "matched_skills": ["Python", "LangChain", "Docker", ...],
      "missing_skills": ["Kubernetes"],
      "evidence_snippets": [
        "Build AI-driven solutions...",
        "Experience with LLMs required"
      ],
      "success_likelihood": "High"
    }
  ]
}
```

## Development

### Code Quality Tools

This project uses several tools to maintain code quality:

**Quick Commands (using Makefile):**
```bash
make format      # Format code with black and isort
make lint        # Lint code with ruff
make type-check  # Type check with mypy
make test        # Run tests with pytest
make test-cov    # Run tests with coverage report
make check-all   # Run all checks (format + lint + type-check + test)
make clean       # Remove cache and build artifacts
```

**Manual Commands:**
```bash
# Format code
black agents/ core/ workflows/ tests/ cli.py
isort agents/ core/ workflows/ tests/ cli.py

# Lint code
ruff check agents/ core/ workflows/ tests/ cli.py

# Type check
mypy agents/ core/ workflows/ cli.py

# Run tests
pytest tests/
pytest tests/ --cov=agents --cov=core --cov=workflows
```

### Running Tests

Execute unit tests:
```bash
python3 -m pytest tests/
# or
make test
```

With coverage:
```bash
make test-cov
```

Or using unittest:
```bash
python3 -m unittest discover tests/
```

## Caching System

The system automatically caches:
- Parsed resume: `cache/resume_*.json`
- Parsed jobs: `cache/job_*.json`
- Logs: `cache/job_matcher_*.log`

Cache benefits:
- Faster subsequent runs
- Reduced LLM API calls (when enabled)
- Consistent results

Clear cache when you modify input files:
```bash
python cli.py clear-cache
```

## Extending the System

### Adding Real LLM Integration

The system is designed with LLM stubs. To enable real LLM calls:

1. Set `use_llm = True` in agents
2. Configure Google ADK client with API key
3. Implement LLM prompts in `_parse_with_llm()` methods

Example:
```python
# In agents/cv_agent.py
self.use_llm = True
self.client = genai.Client(api_key="YOUR_API_KEY")
```

### Adding Custom Scoring Rules

Modify `core/scoring.py` to adjust:
- Score weights
- Seniority levels
- Domain matching logic
- Language requirements

### Adding New Agents

Create new agents in `agents/` directory:
```python
class SearchAgent:
    """Agent for searching additional job postings."""
    pass
```

## Logging and Observability

Logs are stored in `cache/job_matcher_YYYYMMDD.log`

View metrics at the end of execution:
```
=== Metrics Summary ===
resumes_parsed: 1
jobs_parsed: 3
matches_computed: 3
cache_hits: 2
cache_misses: 2
llm_calls: 0
=======================
```

## Troubleshooting

### Issue: "File not found: resume.md"
**Solution**: Ensure `resume.md` exists in the project root

### Issue: "No jobs found"
**Solution**: Add `.md` files to the `JDs/` directory

### Issue: Import errors
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Cache conflicts
**Solution**: Clear cache:
```bash
python cli.py clear-cache
```

## Best Practices

1. **Keep resume updated**: Update `resume.md` when skills change
2. **Structured job descriptions**: Use consistent markdown formatting
3. **Regular cache clearing**: Clear cache after major changes
4. **Review top matches**: Manually review top 3-5 matches
5. **Adjust weights**: Customize scoring weights in `core/scoring.py`

## Performance

- Resume parsing: ~0.1s (cached) / ~0.5s (uncached)
- Job parsing: ~0.1s per job (cached) / ~0.3s per job (uncached)
- Matching: ~0.2s per job
- Total pipeline (3 jobs): ~2-3 seconds

## Future Enhancements

- [ ] Real LLM integration for parsing
- [ ] Google Search integration via MCP
- [ ] Historical ranking analysis
- [ ] A/B testing framework
- [ ] Web UI dashboard
- [ ] Email notifications for new matches
- [ ] Interview preparation suggestions

## License

MIT License - feel free to use and modify

## Support

For issues or questions:
1. Check logs in `cache/` directory
2. Review test cases in `tests/`
3. Examine output JSON files
4. Enable debug logging for detailed traces

## Contributing

Contributions welcome! Areas for improvement:
- Additional scoring dimensions
- Better language detection
- Domain-specific matching rules
- Performance optimizations
- More test coverage

---

Built with Google Agent Development Kit (ADK)
