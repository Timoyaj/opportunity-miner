"""Stack Overflow adapter — 100% free via Stack Exchange API v2.3 (10k req/day, no key).

Docs: https://api.stackexchange.com/docs/advanced-search
No authentication required. Supports `filter=withbody` to get markdown body.
"""

from datetime import datetime
import logging
import requests

from .base import SourceAdapter, NormalizedSignal
from ..core.scraper import clean_scraped_text

logger = logging.getLogger(__name__)


class StackOverflowAdapter(SourceAdapter):
    """Adapter for mining Excel/automation pain from Stack Overflow."""

    API_URL = "https://api.stackexchange.com/2.3/search/advanced"
    INFO_URL = "https://api.stackexchange.com/2.3/info"

    @property
    def source_name(self) -> str:
        return "stackoverflow"

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = requests.get(self.INFO_URL, params={"site": "stackoverflow"}, timeout=5)
            if resp.status_code == 200:
                return True, "Stack Exchange API accessible (Stack Overflow OK)"
            return False, f"Stack Exchange returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Stack Overflow unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        if not queries:
            queries = ["excel automation", "spreadsheet manual", "powerbi reporting tedious"]

        # Stack Exchange expects single query string; we iterate over provided queries
        for query in queries:
            if len(results) >= limit:
                break

            params = {
                "order": "desc",
                "sort": "creation",
                "q": query,
                "site": "stackoverflow",
                "pagesize": min(25, limit - len(results)),
                "filter": "withbody",  # returns body_markdown
            }
            # Optional since filter: Stack API uses `fromdate` (unix timestamp)
            if since:
                try:
                    params["fromdate"] = int(since.timestamp())
                except Exception:
                    pass

            try:
                resp = requests.get(self.API_URL, params=params, timeout=10)
                if resp.status_code == 400:
                    # Some queries may be too broad; try fallback without q
                    logger.debug(f"Stack Overflow bad request for '{query}': {resp.text[:200]}")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"Stack Overflow API error ({query}): HTTP {resp.status_code}")
                    continue

                data = resp.json()
                # Respect backoff if present
                if "backoff" in data:
                    logger.debug(f"Stack Overflow backoff requested: {data['backoff']}s")

                items = data.get("items", [])

                for item in items:
                    if len(results) >= limit:
                        break

                    qid = str(item.get("question_id"))
                    if not qid or qid in seen_ids:
                        continue
                    seen_ids.add(qid)

                    title = item.get("title") or ""
                    # body_markdown may contain HTML entities; clean it
                    body_raw = item.get("body_markdown") or item.get("body") or ""
                    # Stack bodies are HTML; clean
                    body_clean = clean_scraped_text(body_raw)
                    full_body = f"{title}\n\n{body_clean}".strip() if body_clean else title

                    creation = item.get("creation_date")
                    pub_date = datetime.utcfromtimestamp(creation) if creation else datetime.utcnow()
                    if since and pub_date < since:
                        continue

                    author = None
                    owner = item.get("owner") or {}
                    if isinstance(owner, dict):
                        author = owner.get("display_name")

                    signal = NormalizedSignal(
                        source="stackoverflow",
                        source_id=qid,
                        source_url=item.get("link") or f"https://stackoverflow.com/questions/{qid}",
                        title=title[:280],
                        author=author,
                        body=full_body[:4000],
                        published_at=pub_date,
                        metadata={
                            "tags": item.get("tags", []),
                            "score": item.get("score", 0),
                            "view_count": item.get("view_count", 0),
                            "answer_count": item.get("answer_count", 0),
                            "is_answered": item.get("is_answered", False),
                            "query": query,
                            "ingest_tier": "stackexchange_api",
                        },
                    )
                    results.append(signal)

            except Exception as e:
                logger.warning(f"Failed collecting Stack Overflow signals for '{query}': {e}")
                continue

        return results
