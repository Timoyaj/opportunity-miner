"""GitHub Issues adapter — 100% free, open-source, no paid API required.

Uses the public GitHub Search API:
  https://api.github.com/search/issues?q=<query>&sort=created&order=desc
Quota: 60 req/h unauthenticated, 5,000 req/h with free PAT (GITHUB_TOKEN env).
Documentation: https://docs.github.com/en/rest/search/search#search-issues-and-pull-requests
"""

from datetime import datetime, timedelta
import logging
import os
import requests

from .base import SourceAdapter, NormalizedSignal
from ..core.scraper import clean_scraped_text

logger = logging.getLogger(__name__)


class GithubAdapter(SourceAdapter):
    """Adapter for mining developer workflow pain from GitHub Issues."""

    SEARCH_URL = "https://api.github.com/search/issues"
    RATE_LIMIT_URL = "https://api.github.com/rate_limit"
    DEFAULT_USER_AGENT = "OpportunityMiner/0.1.0"

    @property
    def source_name(self) -> str:
        return "github"

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.DEFAULT_USER_AGENT,
        }
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = requests.get(self.RATE_LIMIT_URL, headers=self._headers(), timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                remaining = data.get("resources", {}).get("search", {}).get("remaining", "?")
                return True, f"GitHub Search API accessible (remaining search quota: {remaining})"
            if resp.status_code in (403, 429):
                return True, f"GitHub API rate-limited but reachable (HTTP {resp.status_code})"
            return False, f"GitHub API returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"GitHub unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        if not queries:
            queries = ["excel automation tedious", "manual spreadsheet pain", "copy paste reporting nightmare"]

        headers = self._headers()

        for query in queries:
            if len(results) >= limit:
                break

            # Append since filter if provided
            q = query
            if since:
                date_str = since.strftime("%Y-%m-%d")
                q = f"{query} created:>{date_str}"

            params = {
                "q": f"{q} in:title,body",
                "sort": "created",
                "order": "desc",
                "per_page": min(20, limit - len(results)),
            }

            try:
                resp = requests.get(self.SEARCH_URL, headers=headers, params=params, timeout=10)
                if resp.status_code == 403:
                    logger.warning(f"GitHub rate limited for query '{query}': {resp.text[:200]}")
                    # Try to continue with next query after short pause
                    continue
                if resp.status_code != 200:
                    logger.warning(f"GitHub search error ({query}): HTTP {resp.status_code} — {resp.text[:200]}")
                    continue

                data = resp.json()
                items = data.get("items", [])

                for item in items:
                    if len(results) >= limit:
                        break

                    # Skip pull requests (contain pull_request key)
                    if "pull_request" in item:
                        continue

                    gh_id = str(item.get("id"))
                    if not gh_id or gh_id in seen_ids:
                        continue
                    seen_ids.add(gh_id)

                    title = item.get("title") or ""
                    body_raw = item.get("body") or ""
                    body = clean_scraped_text(f"{title}\n\n{body_raw}") or title

                    # Parse created_at
                    created_str = item.get("created_at")
                    try:
                        pub_date = datetime.fromisoformat(created_str.replace("Z", "+00:00")).replace(tzinfo=None) if created_str else datetime.utcnow()
                    except Exception:
                        pub_date = datetime.utcnow()

                    if since and pub_date < since:
                        continue

                    signal = NormalizedSignal(
                        source="github",
                        source_id=gh_id,
                        source_url=item.get("html_url") or f"https://github.com/issues/{gh_id}",
                        title=title[:280],
                        author=(item.get("user") or {}).get("login"),
                        body=body[:4000],
                        published_at=pub_date,
                        metadata={
                            "repository": (item.get("repository_url") or "").split("/")[-1] if item.get("repository_url") else None,
                            "comments": item.get("comments", 0),
                            "state": item.get("state"),
                            "labels": [l.get("name") for l in item.get("labels", [])],
                            "query": query,
                            "ingest_tier": "search_api",
                        },
                    )
                    results.append(signal)

            except Exception as e:
                logger.warning(f"Failed collecting GitHub signals for query '{query}': {e}")
                continue

        return results
