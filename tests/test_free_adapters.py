"""Tests for 100% free OSS adapters and vector store fallbacks."""

import os
from opportunity_miner.adapters import get_adapter, ADAPTERS_MAP
from opportunity_miner.core.vector_store import VectorStore
from opportunity_miner.core.extractor import ProblemExtractor
from opportunity_miner.core.serp_enricher import SerpEnricher
from opportunity_miner.core.notifier import Notifier
from opportunity_miner.generators.baserow_sync import FreeCrmSync


def test_free_adapters_registered():
    expected = ["github", "stackoverflow", "devto", "appstore"]
    for name in expected:
        assert name in ADAPTERS_MAP, f"{name} missing from ADAPTERS_MAP"
        adapter = get_adapter(name)
        assert adapter.source_name == name
        # health_check must not crash and return tuple[bool, str]
        ok, msg = adapter.health_check()
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
        # collect must return list, not crash on free public API
        try:
            signals = adapter.collect(queries=["excel automation"], limit=2)
            assert isinstance(signals, list)
        except Exception as e:
            # Should not raise; network failures handled gracefully
            assert False, f"{name}.collect raised {e}"


def test_vector_store_hash_fallback():
    # Force hash backend for deterministic offline test
    os.environ["VECTOR_BACKEND"] = "hash"
    vs = VectorStore(blacklist_path="/tmp/test_blacklist_free.json")
    v1 = vs.embed_text("automate excel reports")
    v2 = vs.embed_text("automate excel reports")
    v3 = vs.embed_text("sourdough baking recipe")
    assert vs.cosine_similarity(v1, v2) >= 0.99
    assert vs.cosine_similarity(v1, v3) < 0.7
    # Blacklist
    vs.save_to_blacklist(v1, reason="test")
    assert vs.is_blacklisted(v2) is True
    assert vs.is_blacklisted(v3) is False


def test_extractor_ollama_fallback_does_not_crash():
    # Ensure Ollama env doesn't break heuristic extraction when Ollama not running
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    # Don't set OLLAMA_HOST; should fast-fallback to heuristic
    pe = ProblemExtractor()
    # Force ollama unavailable for test isolation
    pe._ollama_detected = False
    result = pe.extract("Manual excel nightmare", "I waste 5 hours weekly copy pasting, looking for tool $100", "github")
    assert result is not None
    assert result.is_commercial_problem is True
    assert result.frustration_severity in ("mild", "severe", "blocking")


def test_serp_enricher_instantiates():
    se = SerpEnricher(provider="auto")
    assert se.provider in ("auto", "openserp", "searxng", "duckduckgo")
    # enrich should return dict without network
    out = se.enrich_opportunity("excel automation pain", top_n=1)
    assert "query" in out
    assert "incumbents" in out


def test_notifier_noop():
    n = Notifier(apprise_urls="", ntfy_topic="")
    res = n.send("Test Title", "Test body")
    assert isinstance(res, dict)


def test_baserow_csv_fallback():
    sync = FreeCrmSync(provider="csv")
    class DummyOpp:
        id = "OP-TEST"
        title = "Test Opp"
        category = "AUTOMATION_SERVICE"
        opportunity_score = 88.5
        confidence_score = 0.9
        evidence_level = 4
        status = "NEW"
        score_breakdown = {"pain": 20.0}

    res = sync.push_opportunity(DummyOpp())
    assert isinstance(res, dict)
    assert "csv" in res
