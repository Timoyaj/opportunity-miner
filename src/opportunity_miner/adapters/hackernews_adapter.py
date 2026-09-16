"""Hacker News source adapter using Algolia Search API (Zero Auth Required)."""

from datetime import datetime
import logging
import requests

from .base import SourceAdapter, NormalizedSignal

logger = logging.getLogger(__name__)


class HackerNewsAdapter(SourceAdapter):
    """Adapter for searching Ask HN, Show HN, and stories via the free Algolia HN API."""

    BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"

    @property
    def source_name(self) -> str:
        return "hackernews"

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = requests.get(
                self.BASE_URL,
                params={"query": "test", "hitsPerPage": 1},
                timeout=5
            )
            if resp.status_code == 200:
                return True, "Hacker News Algolia API accessible (OK)"
            return False, f"Algolia API returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Hacker News Algolia API unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        tags_list = ["ask_hn", "show_hn", "story"]

        for query in queries:
            for tag in tags_list:
                if len(results) >= limit:
                    break

                params = {
                    "query": query,
                    "tags": tag,
                    "hitsPerPage": min(30, limit - len(results)),
                }
                if since:
                    params["numericFilters"] = f"created_at_i>{int(since.timestamp())}"

                try:
                    resp = requests.get(self.BASE_URL, params=params, timeout=10)
                    if resp.status_code != 200:
                        logger.warning(f"HN Algolia search error ({query}, {tag}): HTTP {resp.status_code}")
                        continue

                    data = resp.json()
                    hits = data.get("hits", [])

                    for hit in hits:
                        obj_id = hit.get("objectID")
                        if not obj_id or obj_id in seen_ids:
                            continue
                        seen_ids.add(obj_id)

                        title = hit.get("title") or ""
                        story_text = hit.get("story_text") or ""
                        url = hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}"
                        
                        created_at_i = hit.get("created_at_i")
                        pub_date = datetime.utcfromtimestamp(created_at_i) if created_at_i else datetime.utcnow()

                        # Body: either story_text or title if self post has no body
                        full_body = story_text if story_text else title

                        signal = NormalizedSignal(
                            source="hackernews",
                            source_id=str(obj_id),
                            source_url=f"https://news.ycombinator.com/item?id={obj_id}",
                            title=title,
                            author=hit.get("author"),
                            body=full_body,
                            published_at=pub_date,
                            metadata={
                                "points": hit.get("points", 0),
                                "num_comments": hit.get("num_comments", 0),
                                "original_url": url,
                                "tag": tag,
                                "matched_query": query,
                            }
                        )
                        results.append(signal)

                except Exception as e:
                    logger.warning(f"Failed collecting HN signals for query '{query}': {e}")
                    continue

        return results
