"""Unit tests for adapter health check and contract adherence."""

from opportunity_miner.adapters import get_adapter, ADAPTERS_MAP


def test_adapters_registered():
    expected = ["hackernews", "reddit", "upwork", "indiehackers", "producthunt"]
    for name in expected:
        assert name in ADAPTERS_MAP
        adapter = get_adapter(name)
        assert adapter.source_name == name


def test_hackernews_health_check():
    hn = get_adapter("hackernews")
    is_ok, msg = hn.health_check()
    # Should be True if internet is accessible, otherwise gracefully returns diagnostic string
    assert isinstance(is_ok, bool)
    assert isinstance(msg, str)
