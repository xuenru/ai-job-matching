"""Logging configuration for the job matching system."""
import logging
import sys
from pathlib import Path
from datetime import datetime


class JobMatchLogger:
    """Logger for job matching operations with metrics tracking."""
    
    def __init__(self, name: str = "job_matcher", log_dir: str = "cache"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
        
        # Metrics storage
        self.metrics = {
            'resumes_parsed': 0,
            'jobs_parsed': 0,
            'matches_computed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'llm_calls': 0,
        }
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a metric counter."""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
            self.debug(f"Metric {metric_name}: {self.metrics[metric_name]}")
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        return self.metrics.copy()
    
    def log_metrics(self):
        """Log current metrics summary."""
        self.info("=== Metrics Summary ===")
        for key, value in self.metrics.items():
            self.info(f"{key}: {value}")
        self.info("=" * 23)


# Global logger instance
_logger = None


def get_logger(name: str = "job_matcher") -> JobMatchLogger:
    """Get or create logger instance."""
    global _logger
    if _logger is None:
        _logger = JobMatchLogger(name)
    return _logger
