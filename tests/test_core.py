"""Unit tests for core modules."""
import unittest
import json
from pathlib import Path
import tempfile
import shutil

from core.parsing_schemas import ResumeSchema, JobSchema, Contact, ScoreBreakdown
from core.embeddings import DeterministicEmbeddings
from core.scoring import JobMatcher
from core.utils import CacheManager
from core.logger import JobMatchLogger


class TestParsingSchemas(unittest.TestCase):
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
            "other_notes": "Test notes"
        }
        
        resume = ResumeSchema(**resume_data)
        self.assertEqual(resume.name, "Test User")
        self.assertEqual(resume.years_of_experience, 5)
        self.assertEqual(len(resume.skills), 2)
    
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
            "raw_text": "Test job description"
        }
        
        job = JobSchema(**job_data)
        self.assertEqual(job.title, "Senior Python Developer")
        self.assertEqual(len(job.requirements), 2)
    
    def test_score_breakdown_validation(self):
        """Test score breakdown validation."""
        breakdown = ScoreBreakdown(
            skill_match=35.0,
            experience_alignment=25.0,
            seniority_fit=8.0,
            location_language=9.0,
            semantic_alignment=7.0
        )
        
        self.assertEqual(breakdown.skill_match, 35.0)
        
        # Test bounds
        with self.assertRaises(Exception):
            ScoreBreakdown(skill_match=50.0)  # Over max


class TestEmbeddings(unittest.TestCase):
    """Test embedding functionality."""
    
    def setUp(self):
        self.embeddings = DeterministicEmbeddings()
    
    def test_embed_text(self):
        """Test text embedding."""
        text = "Python developer with 5 years experience"
        embedding = self.embeddings.embed_text(text)
        
        self.assertEqual(len(embedding), 384)
        self.assertIsInstance(embedding[0], float)
    
    def test_embedding_deterministic(self):
        """Test that embeddings are deterministic."""
        text = "Test text"
        emb1 = self.embeddings.embed_text(text)
        emb2 = self.embeddings.embed_text(text)
        
        self.assertTrue((emb1 == emb2).all())
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        text1 = "Python developer"
        text2 = "Python engineer"
        text3 = "Java developer"
        
        sim_12 = self.embeddings.cosine_similarity(text1, text2)
        sim_13 = self.embeddings.cosine_similarity(text1, text3)
        
        self.assertIsInstance(sim_12, float)
        self.assertGreaterEqual(sim_12, -1.0)
        self.assertLessEqual(sim_12, 1.0)


class TestScoring(unittest.TestCase):
    """Test scoring logic."""
    
    def setUp(self):
        self.matcher = JobMatcher()
        
        self.resume = ResumeSchema(
            name="Test Candidate",
            contact=Contact(email="test@test.com", location="Paris"),
            years_of_experience=5,
            seniority="Senior",
            skills=["Python", "Docker", "FastAPI", "PostgreSQL"],
            domains=["AI", "Data Engineering"],
            languages=["English", "French"],
            education=["Master's degree"],
            projects=["ML project"],
            preferred_location="France"
        )
        
        self.job = JobSchema(
            id="test_job",
            title="Senior Python Developer",
            company="Test Corp",
            location="Paris, France",
            responsibilities="Build Python applications",
            requirements=["Python", "Docker", "5+ years experience"],
            nice_to_have=["AWS"],
            seniority="Senior",
            raw_text="Test job"
        )
    
    def test_skill_match_calculation(self):
        """Test skill matching score."""
        score, matched, missing = self.matcher.calculate_skill_match(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 40)
        self.assertIsInstance(matched, list)
        self.assertIsInstance(missing, list)
    
    def test_experience_alignment(self):
        """Test experience alignment score."""
        score = self.matcher.calculate_experience_alignment(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 30)
    
    def test_seniority_fit(self):
        """Test seniority fit score."""
        score = self.matcher.calculate_seniority_fit(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)
    
    def test_location_language_fit(self):
        """Test location and language fit score."""
        score = self.matcher.calculate_location_language_fit(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)
    
    def test_semantic_similarity(self):
        """Test semantic similarity score."""
        score = self.matcher.calculate_semantic_similarity(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)
    
    def test_overall_match_score(self):
        """Test overall match score calculation."""
        score, breakdown, matched, missing = self.matcher.calculate_match_score(
            self.resume, self.job
        )
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIsInstance(breakdown, ScoreBreakdown)
    
    def test_success_likelihood(self):
        """Test success likelihood determination."""
        high = self.matcher.determine_success_likelihood(80)
        medium = self.matcher.determine_success_likelihood(60)
        low = self.matcher.determine_success_likelihood(40)
        
        self.assertEqual(high, "High")
        self.assertEqual(medium, "Medium")
        self.assertEqual(low, "Low")


class TestCacheManager(unittest.TestCase):
    """Test cache management."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CacheManager(cache_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache."""
        key = "test_key"
        data = {"test": "data", "value": 123}
        
        result = self.cache.set(key, data, prefix="test")
        self.assertTrue(result)
        
        cached = self.cache.get(key, prefix="test")
        self.assertIsNotNone(cached)
        self.assertEqual(cached['data'], data)
    
    def test_cache_exists(self):
        """Test cache existence check."""
        key = "test_key"
        data = {"test": "data"}
        
        self.assertFalse(self.cache.exists(key, prefix="test"))
        
        self.cache.set(key, data, prefix="test")
        self.assertTrue(self.cache.exists(key, prefix="test"))
    
    def test_cache_clear(self):
        """Test cache clearing."""
        self.cache.set("key1", {"data": 1}, prefix="test")
        self.cache.set("key2", {"data": 2}, prefix="test")
        
        self.cache.clear(prefix="test")
        
        self.assertFalse(self.cache.exists("key1", prefix="test"))
        self.assertFalse(self.cache.exists("key2", prefix="test"))


class TestLogger(unittest.TestCase):
    """Test logger functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.logger = JobMatchLogger(name="test_logger", log_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_logging(self):
        """Test basic logging functionality."""
        self.logger.info("Test info message")
        self.logger.debug("Test debug message")
        self.logger.warning("Test warning message")
        
        # Check log file was created
        log_files = list(Path(self.temp_dir).glob("*.log"))
        self.assertGreater(len(log_files), 0)
    
    def test_metrics(self):
        """Test metrics tracking."""
        self.logger.increment_metric('resumes_parsed', 1)
        self.logger.increment_metric('jobs_parsed', 3)
        
        metrics = self.logger.get_metrics()
        self.assertEqual(metrics['resumes_parsed'], 1)
        self.assertEqual(metrics['jobs_parsed'], 3)


if __name__ == '__main__':
    unittest.main()
