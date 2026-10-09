"""Vector store, local embedding generation, and negative feedback blacklist matching.

100% FREE & OPEN-SOURCE design:
  - Tries `sentence-transformers/all-MiniLM-L6-v2` (Apache-2.0, 80MB, 384d) first
  - Falls back to `FastEmbed` (MIT, ONNX, no PyTorch) second
  - Falls back to deterministic n-gram hash projection (zero-deps) last
  - Blacklist: JSON file by default, optional Chroma (Apache-2.0) or Qdrant (Apache-2.0) if installed and env set

All imports are lazy; pipeline never crashes if optional deps are absent.
"""

import json
import logging
import os
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages dense text embeddings and cosine similarity computations."""

    # Default dim for hash fallback and all-MiniLM-L6-v2 (both 384)
    VECTOR_DIM = 384

    def __init__(self, blacklist_path: str | Path = "data/vectors/negative_blacklist.json", model_name: str | None = None, backend: str = "auto"):
        self.blacklist_path = Path(blacklist_path)
        self.blacklist_path.parent.mkdir(parents=True, exist_ok=True)

        # ── Embedding backend auto-detection ─────────────────────────────
        # Env override: VECTOR_MODEL, VECTOR_BACKEND
        # backend: auto | hash | sentence_transformers | fastembed
        self._model_name = model_name or os.environ.get("VECTOR_MODEL") or "sentence-transformers/all-MiniLM-L6-v2"
        env_backend = os.environ.get("VECTOR_BACKEND", backend)  # auto | hash | sentence_transformers | fastembed
        self._backend = env_backend
        self._model = None
        self._model_dim = self.VECTOR_DIM  # will be updated after load
        self._load_embedding_model()

        # ── Blacklist backend ────────────────────────────────────────────
        # Default: JSON file (zero-deps). If USE_CHROMA or CHROMA_PATH set and chromadb installed, use Chroma.
        # Same for QDRANT. Falls back to JSON silently.
        self._blacklist_vectors: list[np.ndarray] = []
        self._chroma_collection = None
        self._qdrant_client = None
        self._init_blacklist_backend()
        self._load_blacklist()

    # ── Embedding model loading ────────────────────────────────────────
    def _load_embedding_model(self):
        if self._backend == "hash":
            logger.info("VectorStore: hash fallback forced via VECTOR_BACKEND=hash")
            return

        # Try sentence-transformers (Apache-2.0, pip: sentence-transformers)
        if self._backend in ("auto", "sentence_transformers"):
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore

                # Only attempt to load if caller wants ST or auto and model seems local/cached or internet allowed
                # We wrap in try; if download fails, we silently fallback
                model = SentenceTransformer(self._model_name)
                # Probe encode to get dim
                dim = model.get_sentence_embedding_dimension()
                if dim:
                    self._model_dim = int(dim)
                    # Keep class-level VECTOR_DIM compatible for legacy code that reads VectorStore.VECTOR_DIM
                    # but also store instance dim
                    self.VECTOR_DIM = self._model_dim  # instance overrides class via assignment
                    self.__class__.VECTOR_DIM = self._model_dim  # update class for new instances
                self._model = model
                logger.info(f"VectorStore: loaded sentence-transformers '{self._model_name}' dim={self._model_dim}")
                return
            except Exception as e:
                logger.debug(f"VectorStore: sentence-transformers not available or load failed ({e}), trying FastEmbed...")

        # Try FastEmbed (MIT, pip: fastembed, ONNX, no torch)
        if self._backend in ("auto", "fastembed"):
            try:
                from fastembed import TextEmbedding  # type: ignore

                # Map model name to FastEmbed equivalent
                # all-MiniLM-L6-v2 -> BAAI/bge-small-en-v1.5 is 384d also, works well
                fe_name = os.environ.get("FASTEMBED_MODEL") or "BAAI/bge-small-en-v1.5"
                # FastEmbed models are downloaded on first use
                model = TextEmbedding(model_name=fe_name)
                # FastEmbed doesn't expose dim statically, but bge-small is 384
                # Keep 384 for compatibility
                self._model = model
                self._is_fastembed = True
                logger.info(f"VectorStore: loaded FastEmbed '{fe_name}' (384d, ONNX)")
                return
            except Exception as e:
                logger.debug(f"VectorStore: FastEmbed not available ({e}), using hash fallback")

        # Hash fallback is always available
        self._model = None
        logger.info("VectorStore: using deterministic hash projection (zero-deps, 384d)")

    # ── Blacklist backend init ─────────────────────────────────────────
    def _init_blacklist_backend(self):
        # Chroma optional path
        chroma_path = os.environ.get("CHROMA_PATH") or os.environ.get("USE_CHROMA")
        if chroma_path:
            try:
                import chromadb  # type: ignore

                # If USE_CHROMA is "true", use default path data/vectors/chroma
                path = "data/vectors/chroma" if chroma_path.lower() in ("1", "true", "yes") else chroma_path
                Path(path).mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=path)
                # Use same embedding function as above if available, else default
                self._chroma_collection = client.get_or_create_collection("negative_blacklist")
                logger.info(f"VectorStore: Chroma blacklist at {path} (Apache-2.0)")
            except Exception as e:
                logger.debug(f"Chroma init skipped: {e}")
                self._chroma_collection = None

        # Qdrant optional path
        qdrant_url = os.environ.get("QDRANT_URL") or os.environ.get("QDRANT_PATH")
        if qdrant_url:
            try:
                from qdrant_client import QdrantClient  # type: ignore

                # Local path mode: QdrantClient(path="data/vectors/qdrant")
                # Server mode: QdrantClient(url="http://localhost:6333")
                if qdrant_url.startswith("http"):
                    self._qdrant_client = QdrantClient(url=qdrant_url)
                else:
                    p = qdrant_url if "/" in qdrant_url else "data/vectors/qdrant"
                    Path(p).mkdir(parents=True, exist_ok=True)
                    self._qdrant_client = QdrantClient(path=p)
                logger.info(f"VectorStore: Qdrant blacklist at {qdrant_url} (Apache-2.0)")
            except Exception as e:
                logger.debug(f"Qdrant init skipped: {e}")

    def _load_blacklist(self):
        """Load user-rejected negative vector blacklist (JSON fallback)."""
        self._blacklist_vectors = []
        # If Chroma/Qdrant active, we don't pre-load JSON (those stores are queried live)
        if self._chroma_collection is not None or self._qdrant_client is not None:
            # Still load JSON for hybrid if file exists, to keep backward-compat
            pass

        if self.blacklist_path.exists():
            try:
                with open(self.blacklist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        vec = np.array(item.get("vector", []), dtype=np.float32)
                        # Accept both 384 and custom dims; store normalized
                        if len(vec) > 0:
                            # If file has old 384 but current dim is different, we keep as-is for comparison
                            # (cosine will work if we zero-pad/truncate)
                            if len(vec) != self._model_dim:
                                # Pad or truncate to current dim for in-memory list
                                if len(vec) < self._model_dim:
                                    padded = np.zeros(self._model_dim, dtype=np.float32)
                                    padded[: len(vec)] = vec
                                    vec = padded
                                else:
                                    vec = vec[: self._model_dim]
                            self._blacklist_vectors.append(vec)
            except Exception as e:
                logger.warning(f"Failed loading negative blacklist: {e}")

    def save_to_blacklist(self, vector: np.ndarray, reason: str = ""):
        """Add a vector to the negative blacklist (all backends)."""
        # Normalize
        n = np.linalg.norm(vector)
        if n > 1e-6:
            vector = vector / n

        self._blacklist_vectors.append(vector)

        # Chroma persistence
        if self._chroma_collection is not None:
            try:
                import uuid as _uuid

                self._chroma_collection.add(
                    ids=[f"blk_{_uuid.uuid4().hex[:8]}"],
                    embeddings=[vector.tolist()],
                    metadatas=[{"reason": reason}],
                )
            except Exception as e:
                logger.debug(f"Chroma blacklist save failed: {e}")

        # Qdrant persistence (simple flat point)
        if self._qdrant_client is not None:
            try:
                import uuid as _uuid
                from qdrant_client.models import PointStruct  # type: ignore

                # Ensure collection exists
                try:
                    self._qdrant_client.create_collection(collection_name="negative_blacklist", vectors_config={"size": len(vector), "distance": "Cosine"})
                except Exception:
                    pass
                self._qdrant_client.upsert(
                    collection_name="negative_blacklist",
                    points=[PointStruct(id=str(_uuid.uuid4()), vector=vector.tolist(), payload={"reason": reason})],
                )
            except Exception as e:
                logger.debug(f"Qdrant blacklist save failed: {e}")

        # Always persist to JSON for portability / fallback
        serialized = []
        if self.blacklist_path.exists():
            try:
                with open(self.blacklist_path, "r", encoding="utf-8") as f:
                    serialized = json.load(f)
            except Exception:
                serialized = []

        serialized.append({"reason": reason, "vector": vector.tolist()})
        try:
            with open(self.blacklist_path, "w", encoding="utf-8") as f:
                json.dump(serialized, f)
        except Exception as e:
            logger.warning(f"Failed writing blacklist file: {e}")

    def is_blacklisted(self, vector: np.ndarray, threshold: float = 0.85) -> bool:
        """Check if vector is too similar to any user-rejected topic."""
        # Normalize query
        n = np.linalg.norm(vector)
        if n > 1e-6:
            vector = vector / n

        # Check in-memory JSON vectors
        for blacklisted_vec in self._blacklist_vectors:
            # Ensure dim match
            if len(blacklisted_vec) != len(vector):
                # Pad/truncate blacklisted to query dim
                if len(blacklisted_vec) < len(vector):
                    tmp = np.zeros(len(vector), dtype=np.float32)
                    tmp[: len(blacklisted_vec)] = blacklisted_vec
                    blacklisted_vec = tmp
                else:
                    blacklisted_vec = blacklisted_vec[: len(vector)]
            sim = self.cosine_similarity(vector, blacklisted_vec)
            if sim >= threshold:
                return True

        # Check Chroma if present (query once)
        if self._chroma_collection is not None:
            try:
                res = self._chroma_collection.query(query_embeddings=[vector.tolist()], n_results=1)
                if res and res.get("distances") and res["distances"][0]:
                    # Chroma returns L2 distance; convert approx: cosine distance = 1 - sim
                    # For cosine we stored normalized, so threshold 0.85 sim ~ distance 0.15
                    # Easier: compute sim directly on retrieved embedding
                    if res.get("embeddings") and res["embeddings"][0]:
                        cand = np.array(res["embeddings"][0][0], dtype=np.float32)
                        if self.cosine_similarity(vector, cand) >= threshold:
                            return True
            except Exception as e:
                logger.debug(f"Chroma blacklist query failed: {e}")

        # Qdrant check
        if self._qdrant_client is not None:
            try:
                hits = self._qdrant_client.search(collection_name="negative_blacklist", query_vector=vector.tolist(), limit=1)
                if hits and hits[0].score >= threshold:
                    return True
            except Exception as e:
                logger.debug(f"Qdrant blacklist query failed: {e}")

        return False

    def embed_text(self, text: str) -> np.ndarray:
        """Generate a normalized dense embedding vector (free local model or hash fallback)."""
        if not text or not text.strip():
            return np.zeros(self._model_dim, dtype=np.float32)

        # Try sentence-transformers
        if self._model is not None and not hasattr(self, "_is_fastembed"):
            try:
                # SentenceTransformer.encode returns np array when normalize_embeddings=True
                vec = self._model.encode(text, normalize_embeddings=True)
                arr = np.array(vec, dtype=np.float32)
                # Ensure dim matches expected
                if len(arr) != self._model_dim:
                    # Truncate/pad to _model_dim for storage consistency
                    if len(arr) > self._model_dim:
                        arr = arr[: self._model_dim]
                    else:
                        padded = np.zeros(self._model_dim, dtype=np.float32)
                        padded[: len(arr)] = arr
                        arr = padded
                        # re-normalize
                        n = np.linalg.norm(arr)
                        if n > 1e-6:
                            arr = arr / n
                return arr.astype(np.float32)
            except Exception as e:
                logger.debug(f"SentenceTransformer encode failed, fallback to hash: {e}")

        # Try FastEmbed (ONNX)
        if hasattr(self, "_is_fastembed") and self._model is not None:
            try:
                # FastEmbed.embed returns generator of lists
                # Use single text -> next(iter(...))
                embeddings = list(self._model.embed([text]))
                if embeddings and len(embeddings) > 0:
                    arr = np.array(embeddings[0], dtype=np.float32)
                    n = np.linalg.norm(arr)
                    if n > 1e-6:
                        arr = arr / n
                    # Pad/truncate to _model_dim
                    if len(arr) != self._model_dim:
                        if len(arr) > self._model_dim:
                            arr = arr[: self._model_dim]
                            n = np.linalg.norm(arr)
                            if n > 1e-6:
                                arr = arr / n
                        else:
                            padded = np.zeros(self._model_dim, dtype=np.float32)
                            padded[: len(arr)] = arr
                            arr = padded
                    return arr.astype(np.float32)
            except Exception as e:
                logger.debug(f"FastEmbed encode failed, fallback to hash: {e}")

        # Deterministic hash fallback (zero-deps, 384d) — always works offline
        words = text.lower().split()
        vector = np.zeros(self._model_dim, dtype=np.float32)
        if not words:
            return vector
        for i, word in enumerate(words):
            h = hash(word)
            idx1 = abs(h) % self._model_dim
            idx2 = abs(h >> 4) % self._model_dim
            weight = 1.0 / (1.0 + 0.05 * min(i, 50))
            vector[idx1] += weight
            vector[idx2] -= weight * 0.5
            if i > 0:
                bigram = f"{words[i-1]}_{word}"
                bh = hash(bigram)
                b_idx = abs(bh) % self._model_dim
                vector[b_idx] += weight * 1.5
        norm = np.linalg.norm(vector)
        if norm > 1e-6:
            vector = vector / norm
        return vector

    @staticmethod
    def vector_to_bytes(vector: np.ndarray) -> bytes:
        """Serialize numpy vector to raw bytes for database storage."""
        return vector.astype(np.float32).tobytes()

    @staticmethod
    def bytes_to_vector(b: bytes | None, dim: int | None = None) -> np.ndarray:
        """Deserialize raw bytes from database into numpy vector.

        If dim is None, infer from byte length (len/4). This allows smooth migration
        from old 384d hash vectors to new 768/1024d local model vectors.
        """
        if not b:
            # Use provided dim or fallback to current VectorStore dim
            d = dim or VectorStore.VECTOR_DIM
            return np.zeros(d, dtype=np.float32)
        arr = np.frombuffer(b, dtype=np.float32)
        if dim is not None and len(arr) != dim:
            # Pad/truncate to requested dim
            if len(arr) < dim:
                padded = np.zeros(dim, dtype=np.float32)
                padded[: len(arr)] = arr
                return padded
            return arr[:dim].astype(np.float32)
        return arr

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Compute cosine similarity between two normalized vectors."""
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        # Handle dim mismatch by truncating to min dim
        if len(v1) != len(v2):
            m = min(len(v1), len(v2))
            v1 = v1[:m]
            v2 = v2[:m]
        return float(np.dot(v1, v2) / (n1 * n2))
