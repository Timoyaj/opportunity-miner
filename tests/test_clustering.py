"""Unit tests for incremental centroid clustering and vector operations."""

import numpy as np
from opportunity_miner.core.vector_store import VectorStore


def test_vector_cosine_similarity():
    vstore = VectorStore()
    v1 = vstore.embed_text("automate excel spreadsheet reports")
    v2 = vstore.embed_text("automate excel spreadsheet reports")
    v3 = vstore.embed_text("baking sourdough bread at home")

    sim_identical = vstore.cosine_similarity(v1, v2)
    sim_different = vstore.cosine_similarity(v1, v3)

    assert sim_identical >= 0.99
    assert sim_different < 0.6


def test_vector_serialization_roundtrip():
    vstore = VectorStore()
    original_vec = np.random.randn(384).astype(np.float32)
    norm = np.linalg.norm(original_vec)
    original_vec /= norm

    b = vstore.vector_to_bytes(original_vec)
    restored_vec = vstore.bytes_to_vector(b)

    np.testing.assert_allclose(original_vec, restored_vec, atol=1e-6)
