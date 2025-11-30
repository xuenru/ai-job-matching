"""Utility functions for caching and file operations."""
import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime


class CacheManager:
    """Manages caching for parsed resumes and jobs."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str, prefix: str = "") -> Path:
        """Get cache file path for a given key."""
        # Create hash of key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        filename = f"{prefix}_{key_hash}.json" if prefix else f"{key_hash}.json"
        return self.cache_dir / filename
    
    def get(self, key: str, prefix: str = "") -> Optional[Dict[str, Any]]:
        """Get cached data by key."""
        cache_path = self._get_cache_path(key, prefix)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"Error reading cache: {e}")
                return None
        
        return None
    
    def set(self, key: str, data: Dict[str, Any], prefix: str = ""):
        """Set cached data by key."""
        cache_path = self._get_cache_path(key, prefix)
        
        try:
            # Add metadata
            cached_data = {
                'key': key,
                'cached_at': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error writing cache: {e}")
            return False
    
    def exists(self, key: str, prefix: str = "") -> bool:
        """Check if cache exists for key."""
        cache_path = self._get_cache_path(key, prefix)
        return cache_path.exists()
    
    def clear(self, prefix: str = ""):
        """Clear all cache or cache with specific prefix."""
        if prefix:
            pattern = f"{prefix}_*.json"
        else:
            pattern = "*.json"
        
        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Error deleting cache file {cache_file}: {e}")
    
    def list_cached(self, prefix: str = "") -> list:
        """List all cached keys."""
        if prefix:
            pattern = f"{prefix}_*.json"
        else:
            pattern = "*.json"
        
        cached_keys = []
        for cache_file in self.cache_dir.glob(pattern):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cached_keys.append(data.get('key', ''))
            except Exception as e:
                print(f"Error reading cache file {cache_file}: {e}")
        
        return cached_keys


def read_markdown_file(file_path: str) -> str:
    """Read markdown file content."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_json_file(file_path: str, data: Dict[str, Any]):
    """Write JSON data to file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON data from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_job_files(jobs_dir: str = "JDs") -> list:
    """Get all job markdown files from directory."""
    jobs_path = Path(jobs_dir)
    if not jobs_path.exists():
        return []
    
    return list(jobs_path.glob("*.md"))


# Global cache instance
_cache = None


def get_cache() -> CacheManager:
    """Get or create cache manager instance."""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache
