"""Embedding generation for semantic similarity."""
import hashlib
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity


class DeterministicEmbeddings:
    """
    Deterministic embedding generator using hash-based vectors.
    For prototype/testing purposes. Can be replaced with real embeddings later.
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.cache: Dict[str, np.ndarray] = {}
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """Convert text to deterministic vector using hash."""
        # Normalize text
        text = text.lower().strip()
        
        # Check cache
        if text in self.cache:
            return self.cache[text]
        
        # Create hash-based vector
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Extend hash to desired dimension
        vector = []
        for i in range(self.dimension):
            byte_index = i % len(hash_bytes)
            vector.append(hash_bytes[byte_index] / 255.0)
        
        vector = np.array(vector)
        
        # Normalize to unit vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        # Cache result
        self.cache[text] = vector
        
        return vector
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self._text_to_vector(text)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        embeddings = [self._text_to_vector(text) for text in texts]
        return np.array(embeddings)
    
    def cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        vec1 = self.embed_text(text1)
        vec2 = self.embed_text(text2)
        
        # Reshape for sklearn
        vec1 = vec1.reshape(1, -1)
        vec2 = vec2.reshape(1, -1)
        
        similarity = cosine_similarity(vec1, vec2)[0][0]
        return float(similarity)
    
    def average_similarity(self, text: str, texts: List[str]) -> float:
        """Calculate average similarity between text and list of texts."""
        if not texts:
            return 0.0
        
        similarities = [self.cosine_similarity(text, t) for t in texts]
        return sum(similarities) / len(similarities)


# Global embeddings instance
_embeddings = None


def get_embeddings() -> DeterministicEmbeddings:
    """Get or create embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = DeterministicEmbeddings()
    return _embeddings
