"""Unit tests for Stage 1 pre-filtering and content hash deduplication."""

from datetime import datetime
from opportunity_miner.core.prefilter import PreFilter
from opportunity_miner.adapters.base import NormalizedSignal


def test_content_hash_deterministic():
    text1 = "I spend 4 hours every Monday manually consolidating Excel files."
    text2 = "  i SPEND 4 hours every monday   manually consolidating excel files. "
    
    hash1 = PreFilter.compute_hash(text1)
    hash2 = PreFilter.compute_hash(text2)
    assert hash1 == hash2


def test_qualifying_opportunity_candidate():
    prefilter = PreFilter()
    qualifying_text = "It is so tedious and time consuming to copy paste data between these spreadsheets every week. Looking for an automated script."
    qualifies, matches = prefilter.is_candidate(qualifying_text)
    
    assert qualifies is True
    assert len(matches["pain"]) > 0 or len(matches["demand"]) > 0
    assert len(matches["domain"]) > 0


def test_non_qualifying_casual_banter():
    prefilter = PreFilter()
    casual_text = "Good morning everyone, I really enjoyed reading the new biography on Steve Jobs this weekend."
    qualifies, matches = prefilter.is_candidate(casual_text)
    
    assert qualifies is False


def test_filter_signals_deduplication():
    prefilter = PreFilter()
    sig1 = NormalizedSignal(
        source="reddit",
        source_id="101",
        source_url="https://reddit.com/r/excel/101",
        title="Manual reporting issue",
        body="It is frustrating to manually merge spreadsheets daily. Looking for a tool.",
        published_at=datetime.utcnow()
    )
    sig2 = NormalizedSignal(
        source="reddit",
        source_id="102",
        source_url="https://reddit.com/r/excel/102",
        title="Manual reporting issue copy",
        body="It is frustrating to manually merge spreadsheets daily. Looking for a tool.",
        published_at=datetime.utcnow()
    )

    existing = set()
    candidates = prefilter.filter_signals([sig1, sig2], existing_hashes=existing)
    
    assert len(candidates) == 1
    assert len(existing) == 1
