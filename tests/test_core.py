"""Unit tests for core modules."""

import shutil
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.embeddings import DeterministicEmbeddings
from core.logger import JobMatchLogger
from core.parsing_schemas import Contact, JobSchema, ResumeSchema, ScoreBreakdown
from core.scoring import JobMatcher
from core.utils import CacheManager

# ============================================================================
# Test Parsing Schemas
# ============================================================================


class TestParsingSchemas:
    """Test data schemas."""

    def test_resume_schema_validation(self):
        """Test resume schema creation and validation."""
        resume_data = {
            "name": "Test User",
            "contact": {"email": "test@example.com", "location": "Paris"},
            "years_of_experience": 5,
            "seniority": "Senior",
            "skills": ["Python", "Docker"],
            "domains": ["AI", "Data Engineering"],
            "languages": ["English", "French"],
            "education": ["Master's degree"],
            "projects": ["Project 1"],
            "preferred_location": "France",
            "other_notes": "Test notes",
        }

        resume = ResumeSchema(**resume_data)
        assert resume.name == "Test User"
        assert resume.years_of_experience == 5
        assert len(resume.skills) == 2

    def test_job_schema_validation(self):
        """Test job schema creation and validation."""
        job_data = {
            "id": "job_test",
            "title": "Senior Python Developer",
            "company": "Test Corp",
            "location": "Paris, France",
            "contract": "Full-time",
            "responsibilities": "Develop Python applications",
            "requirements": ["5+ years Python", "Docker experience"],
            "nice_to_have": ["AWS experience"],
            "seniority": "Senior",
            "raw_text": "Test job description",
        }

        job = JobSchema(**job_data)
        assert job.title == "Senior Python Developer"
        assert len(job.requirements) == 2

    def test_score_breakdown_validation(self):
        """Test score breakdown validation."""
        breakdown = ScoreBreakdown(
            skill_match=35.0,
            experience_alignment=25.0,
            seniority_fit=8.0,
            location_language=9.0,
            semantic_alignment=7.0,
        )

        assert breakdown.skill_match == 35.0

        # Test bounds
        with pytest.raises(ValidationError):
            ScoreBreakdown(skill_match=50.0)  # Over max


# ============================================================================
# Test Embeddings
# ============================================================================


@pytest.fixture
def embeddings():
    """Create embeddings instance for testing."""
    return DeterministicEmbeddings()


class TestEmbeddings:
    """Test embedding functionality."""

    def test_embed_text(self, embeddings):
        """Test text embedding."""
        text = "Python developer with 5 years experience"
        embedding = embeddings.embed_text(text)

        assert len(embedding) == 384
        assert isinstance(embedding[0], float)

    def test_embedding_deterministic(self, embeddings):
        """Test that embeddings are deterministic."""
        text = "Test text"
        emb1 = embeddings.embed_text(text)
        emb2 = embeddings.embed_text(text)

        assert (emb1 == emb2).all()

    def test_cosine_similarity(self, embeddings):
        """Test cosine similarity calculation."""
        text1 = "Python developer"
        text2 = "Python engineer"

        sim_12 = embeddings.cosine_similarity(text1, text2)

        assert isinstance(sim_12, float)
        assert -1.0 <= sim_12 <= 1.0


# ============================================================================
# Test Scoring
# ============================================================================


@pytest.fixture
def matcher():
    """Create job matcher instance for testing."""
    return JobMatcher()


@pytest.fixture
def sample_resume():
    """Create sample resume for testing."""
    return ResumeSchema(
        name="Test Candidate",
        contact=Contact(email="test@test.com", location="Paris"),
        years_of_experience=5,
        seniority="Senior",
        skills=["Python", "Docker", "FastAPI", "PostgreSQL"],
        domains=["AI", "Data Engineering"],
        languages=["English", "French"],
        education=["Master's degree"],
        projects=["ML project"],
        preferred_location="France",
    )


@pytest.fixture
def sample_job():
    """Create sample job for testing."""
    return JobSchema(
        id="test_job",
        title="Senior Python Developer",
        company="Test Corp",
        location="Paris, France",
        responsibilities="Build Python applications",
        requirements=["Python", "Docker", "5+ years experience"],
        nice_to_have=["AWS"],
        seniority="Senior",
        raw_text="Test job",
    )


class TestScoring:
    """Test scoring logic."""

    def test_skill_match_calculation(self, matcher, sample_resume, sample_job):
        """Test skill matching score."""
        score, matched, missing = matcher.calculate_skill_match(sample_resume, sample_job)

        assert 0 <= score <= 40
        assert isinstance(matched, list)
        assert isinstance(missing, list)

    def test_experience_alignment(self, matcher, sample_resume, sample_job):
        """Test experience alignment score."""
        score = matcher.calculate_experience_alignment(sample_resume, sample_job)

        assert 0 <= score <= 30

    def test_seniority_fit(self, matcher, sample_resume, sample_job):
        """Test seniority fit score."""
        score = matcher.calculate_seniority_fit(sample_resume, sample_job)

        assert 0 <= score <= 10

    def test_location_language_fit(self, matcher, sample_resume, sample_job):
        """Test location and language fit score."""
        score = matcher.calculate_location_language_fit(sample_resume, sample_job)

        assert 0 <= score <= 10

    def test_semantic_similarity(self, matcher, sample_resume, sample_job):
        """Test semantic similarity score."""
        score = matcher.calculate_semantic_similarity(sample_resume, sample_job)

        assert 0 <= score <= 10

    def test_overall_match_score(self, matcher, sample_resume, sample_job):
        """Test overall match score calculation."""
        score, breakdown, matched, missing = matcher.calculate_match_score(
            sample_resume, sample_job
        )

        assert 0 <= score <= 100
        assert isinstance(breakdown, ScoreBreakdown)

    def test_success_likelihood(self, matcher):
        """Test success likelihood determination."""
        high = matcher.determine_success_likelihood(80)
        medium = matcher.determine_success_likelihood(60)
        low = matcher.determine_success_likelihood(40)

        assert high == "High"
        assert medium == "Medium"
        assert low == "Low"


# ============================================================================
# Test Cache Manager
# ============================================================================


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create cache manager instance for testing."""
    return CacheManager(cache_dir=temp_cache_dir)


class TestCacheManager:
    """Test cache management."""

    def test_cache_set_and_get(self, cache_manager):
        """Test setting and getting cache."""
        key = "test_key"
        data = {"test": "data", "value": 123}

        result = cache_manager.set(key, data, prefix="test")
        assert result is True

        cached = cache_manager.get(key, prefix="test")
        assert cached is not None
        assert cached["data"] == data

    def test_cache_exists(self, cache_manager):
        """Test cache existence check."""
        key = "test_key"
        data = {"test": "data"}

        assert cache_manager.exists(key, prefix="test") is False

        cache_manager.set(key, data, prefix="test")
        assert cache_manager.exists(key, prefix="test") is True

    def test_cache_clear(self, cache_manager):
        """Test cache clearing."""
        cache_manager.set("key1", {"data": 1}, prefix="test")
        cache_manager.set("key2", {"data": 2}, prefix="test")

        cache_manager.clear(prefix="test")

        assert cache_manager.exists("key1", prefix="test") is False
        assert cache_manager.exists("key2", prefix="test") is False


# ============================================================================
# Test Logger
# ============================================================================


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def logger(temp_log_dir):
    """Create logger instance for testing."""
    return JobMatchLogger(name="test_logger", log_dir=temp_log_dir)


class TestLogger:
    """Test logger functionality."""

    def test_logging(self, logger, temp_log_dir):
        """Test basic logging functionality."""
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")

        # Check log file was created
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) > 0

    def test_metrics(self, logger):
        """Test metrics tracking."""
        logger.increment_metric("resumes_parsed", 1)
        logger.increment_metric("jobs_parsed", 3)

        metrics = logger.get_metrics()
        assert metrics["resumes_parsed"] == 1
        assert metrics["jobs_parsed"] == 3
