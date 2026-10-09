"""Free OSS SERP enricher — OpenSERP (MIT) + SearXNG (AGPL) + DuckDuckGo fallback.

No paid SerpApi / Bright Data. All self-hostable via `docker`:
  OpenSERP: `docker run -p 7000:7000 karust/openserp serve`
  SearXNG:  `docker run -p 8080:8080 searxng/searxng:latest`

Env:
  SERP_PROVIDER = openserp | searxng | duckduckgo | auto (default)
  OPENSERP_URL  = http://localhost:7000
  SEARXNG_URL   = http://localhost:8080
"""

import logging
import os
import requests

logger = logging.getLogger(__name__)


class SerpEnricher:
    """Query local self-hosted SERP for competitor discovery."""

    def __init__(
        self,
        provider: str | None = None,
        openserp_url: str | None = None,
        searxng_url: str | None = None,
    ):
        self.provider = (provider or os.environ.get("SERP_PROVIDER") or "auto").lower()
        self.openserp_url = (openserp_url or os.environ.get("OPENSERP_URL") or "http://localhost:7000").rstrip("/")
        self.searxng_url = (searxng_url or os.environ.get("SEARXNG_URL") or "http://localhost:8080").rstrip("/")

    def _query_openserp(self, query: str, count: int = 5) -> list[dict]:
        try:
            resp = requests.get(
                f"{self.openserp_url}/google/search",
                params={"text": query, "lang": "EN"},
                timeout=6,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            # OpenSERP returns {"results": [{"title","url","description",...}, ...]}
            results = data.get("results") or data.get("items") or []
            out = []
            for r in results[:count]:
                out.append(
                    {
                        "title": r.get("title", "")[:200],
                        "url": r.get("url") or r.get("link") or "",
                        "snippet": r.get("description") or r.get("snippet") or "",
                        "source": "openserp",
                    }
                )
            return out
        except Exception as e:
            logger.debug(f"OpenSERP query failed ({query}): {e}")
            return []

    def _query_searxng(self, query: str, count: int = 5) -> list[dict]:
        try:
            resp = requests.get(
                f"{self.searxng_url}/search",
                params={"q": query, "format": "json", "pageno": 1},
                headers={"Accept": "application/json"},
                timeout=6,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = data.get("results", [])
            out = []
            for r in results[:count]:
                out.append(
                    {
                        "title": r.get("title", "")[:200],
                        "url": r.get("url", ""),
                        "snippet": r.get("content", "")[:300],
                        "source": "searxng",
                    }
                )
            return out
        except Exception as e:
            logger.debug(f"SearXNG query failed ({query}): {e}")
            return []

    def _query_duckduckgo(self, query: str, count: int = 5) -> list[dict]:
        # Pure Python fallback via `duckduckgo-search` if installed (MIT)
        try:
            from duckduckgo_search import DDGS  # type: ignore

            out = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=count):
                    out.append(
                        {
                            "title": r.get("title", "")[:200],
                            "url": r.get("href", ""),
                            "snippet": r.get("body", "")[:300],
                            "source": "duckduckgo",
                        }
                    )
            return out
        except ImportError:
            logger.debug("duckduckgo-search not installed — pip install duckduckgo-search (MIT) for free fallback")
            return []
        except Exception as e:
            logger.debug(f"DuckDuckGo query failed ({query}): {e}")
            return []

    def search(self, query: str, count: int = 5) -> list[dict]:
        """Search competitors / alternatives for a problem statement (free OSS)."""
        if self.provider == "openserp":
            return self._query_openserp(query, count)
        if self.provider == "searxng":
            return self._query_searxng(query, count)
        if self.provider == "duckduckgo":
            return self._query_duckduckgo(query, count)

        # auto: try OpenSERP → SearXNG → DuckDuckGo
        for fn in (self._query_openserp, self._query_searxng, self._query_duckduckgo):
            res = fn(query, count)
            if res:
                return res
        return []

    def enrich_opportunity(self, problem_statement: str, top_n: int = 5) -> dict:
        """High-level helper for `competitor-researcher` skill: find incumbents for a problem."""
        q = f"{problem_statement} alternative pricing"
        results = self.search(q, count=top_n)
        return {
            "query": q,
            "incumbents": results,
            "incumbent_count": len(results),
            "provider": self.provider,
            "note": "Free OSS SERP via OpenSERP/SearXNG/DuckDuckGo — no paid SerpApi",
        }
