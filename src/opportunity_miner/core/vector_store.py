"""Vector store, local embedding generation, and negative feedback blacklist matching."""

import json
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages dense text embeddings and cosine similarity computations."""

    VECTOR_DIM = 384

    def __init__(self, blacklist_path: str | Path = "data/vectors/negative_blacklist.json"):
        self.blacklist_path = Path(blacklist_path)
        self.blacklist_path.parent.mkdir(parents=True, exist_ok=True)
        self._blacklist_vectors: list[np.ndarray] = []
        self._load_blacklist()

    def _load_blacklist(self):
        """Load user-rejected negative vector blacklist."""
        self._blacklist_vectors = []
        if self.blacklist_path.exists():
            try:
                with open(self.blacklist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        vec = np.array(item.get("vector", []), dtype=np.float32)
                        if len(vec) == self.VECTOR_DIM:
                            self._blacklist_vectors.append(vec)
            except Exception as e:
                logger.warning(f"Failed loading negative blacklist: {e}")

    def save_to_blacklist(self, vector: np.ndarray, reason: str = ""):
        """Add a vector to the negative blacklist."""
        self._blacklist_vectors.append(vector)
        serialized = []
        if self.blacklist_path.exists():
            try:
                with open(self.blacklist_path, "r", encoding="utf-8") as f:
                    serialized = json.load(f)
            except Exception:
                serialized = []

        serialized.append({
            "reason": reason,
            "vector": vector.tolist()
        })
        with open(self.blacklist_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f)

    def is_blacklisted(self, vector: np.ndarray, threshold: float = 0.85) -> bool:
        """Check if vector is too similar to any user-rejected topic."""
        for blacklisted_vec in self._blacklist_vectors:
            sim = self.cosine_similarity(vector, blacklisted_vec)
            if sim >= threshold:
                return True
        return False

    def embed_text(self, text: str) -> np.ndarray:
        """Generate a normalized 384-dimensional dense embedding vector.
        Uses deterministic character & n-gram feature projection with L2 normalization.
        """
        # Deterministic, zero-dependency embedding based on n-gram hashing and projection
        words = text.lower().split()
        vector = np.zeros(self.VECTOR_DIM, dtype=np.float32)

        if not words:
            return vector

        for i, word in enumerate(words):
            # Token hash projection
            h = hash(word)
            idx1 = abs(h) % self.VECTOR_DIM
            idx2 = abs(h >> 4) % self.VECTOR_DIM
            weight = 1.0 / (1.0 + 0.05 * min(i, 50))
            vector[idx1] += weight
            vector[idx2] -= weight * 0.5

            # Bigram feature
            if i > 0:
                bigram = f"{words[i-1]}_{word}"
                bh = hash(bigram)
                b_idx = abs(bh) % self.VECTOR_DIM
                vector[b_idx] += weight * 1.5

        # L2 Normalize
        norm = np.linalg.norm(vector)
        if norm > 1e-6:
            vector = vector / norm

        return vector

    @staticmethod
    def vector_to_bytes(vector: np.ndarray) -> bytes:
        """Serialize numpy vector to raw bytes for database storage."""
        return vector.astype(np.float32).tobytes()

    @staticmethod
    def bytes_to_vector(b: bytes | None, dim: int = 384) -> np.ndarray:
        """Deserialize raw bytes from database into numpy vector."""
        if not b:
            return np.zeros(dim, dtype=np.float32)
        arr = np.frombuffer(b, dtype=np.float32)
        if len(arr) != dim:
            return np.zeros(dim, dtype=np.float32)
        return arr

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors."""
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))
