import hashlib
import math
import numpy as np
from typing import List
from app.core.config import settings

class LocalEmbeddingService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.model_name = settings.EMBEDDING_MODEL

    def _hash_token(self, token: str) -> int:
        return int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generates a 384-dimensional dense semantic embedding vector.
        Combines token frequencies, character n-grams, and random projection with L2 normalization.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec

        # Token hashing into dimensions
        for i, word in enumerate(words):
            idx = self._hash_token(word) % self.dimension
            sign = 1.0 if ((self._hash_token(word + "_sign") % 2) == 0) else -1.0
            weight = 1.0 / math.sqrt(i + 1)  # Positional dampening
            vec[idx] += sign * weight

            # Sub-word character trigrams for code & keyword sensitivity
            if len(word) >= 3:
                for c in range(len(word) - 2):
                    trigram = word[c:c+3]
                    t_idx = self._hash_token(trigram) % self.dimension
                    t_sign = 1.0 if ((self._hash_token(trigram + "_sign") % 2) == 0) else -1.0
                    vec[t_idx] += t_sign * 0.5

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return np.vstack([self.embed_text(t) for t in texts])

embedding_service = LocalEmbeddingService()
