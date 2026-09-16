"""Source adapters registry and factory."""

from .base import SourceAdapter, NormalizedSignal
from .hackernews_adapter import HackerNewsAdapter
from .reddit_adapter import RedditAdapter
from .upwork_adapter import UpworkAdapter
from .indiehackers_adapter import IndieHackersAdapter
from .producthunt_adapter import ProductHuntAdapter

ADAPTERS_MAP = {
    "hackernews": HackerNewsAdapter,
    "reddit": RedditAdapter,
    "upwork": UpworkAdapter,
    "indiehackers": IndieHackersAdapter,
    "producthunt": ProductHuntAdapter,
}


def get_adapter(name: str, **kwargs) -> SourceAdapter:
    """Instantiate a source adapter by name."""
    cls = ADAPTERS_MAP.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown source adapter: {name}. Available: {list(ADAPTERS_MAP.keys())}")
    return cls(**kwargs)


__all__ = [
    "SourceAdapter",
    "NormalizedSignal",
    "HackerNewsAdapter",
    "RedditAdapter",
    "UpworkAdapter",
    "IndieHackersAdapter",
    "ProductHuntAdapter",
    "get_adapter",
    "ADAPTERS_MAP",
]
