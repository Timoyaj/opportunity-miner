"""DEV.to adapter — 100% free, no key, MIT-licensed API.

Docs: https://developers.forem.com/api/v1
Endpoint: https://dev.to/api/articles?tag=<tag>&per_page=30
Also supports: https://dev.to/api/articles?per_page=30&top=7
"""

from datetime import datetime
import logging
import requests

from .base import SourceAdapter, NormalizedSignal
from ..core.scraper import clean_scraped_text

logger = logging.getLogger(__name__)


class DevToAdapter(SourceAdapter):
    """Adapter for mining founder/operator pain from DEV Community."""

    BASE_URL = "https://dev.to/api/articles"

    @property
    def source_name(self) -> str:
        return "devto"

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = requests.get(self.BASE_URL, params={"per_page": 1}, timeout=5)
            if resp.status_code == 200:
                return True, "DEV.to API accessible (OK)"
            return False, f"DEV.to returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"DEV.to unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        # Map generic queries to DEV tags (DEV tags are single-word)
        # If query contains space, try first word as tag
        if not queries:
            queries = ["automation", "excel", "productivity", "workflow"]

        # Normalize queries to DEV tag-like strings
        tag_queries = []
        for q in queries:
            # DEV tags: automation, productivity, discuss, help, etc.
            # Take first meaningful word, lowercased
            tag = q.lower().strip().replace(" ", "-").split(",")[0]
            # Split multi-word into individual tags
            for part in q.lower().split():
                if len(part) >= 3 and part not in ("and", "for", "the"):
                    tag_queries.append(part)
            if tag and tag not in tag_queries:
                tag_queries.append(tag)

        # Deduplicate tag_queries but keep order
        uniq_tags = []
        for t in tag_queries:
            if t not in uniq_tags:
                uniq_tags.append(t)
        # Limit to avoid too many calls; take top 6
        uniq_tags = uniq_tags[:6]

        # Try tag-based fetch
        for tag in uniq_tags:
            if len(results) >= limit:
                break

            try:
                params = {"tag": tag, "per_page": min(30, limit - len(results))}
                resp = requests.get(self.BASE_URL, params=params, timeout=10)
                if resp.status_code != 200:
                    logger.debug(f"DEV.to tag '{tag}' returned {resp.status_code}")
                    continue

                items = resp.json()
                if not isinstance(items, list):
                    continue

                for item in items:
                    if len(results) >= limit:
                        break

                    dev_id = str(item.get("id"))
                    if not dev_id or dev_id in seen_ids:
                        continue
                    seen_ids.add(dev_id)

                    title = item.get("title") or ""
                    description = item.get("description") or ""
                    # Body not included in listing; use description + title
                    body_raw = description or title
                    body = clean_scraped_text(f"{title}\n\n{body_raw}") or title

                    # Published timestamp
                    pub_str = item.get("published_timestamp") or item.get("created_at")
                    try:
                        pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).replace(tzinfo=None) if pub_str else datetime.utcnow()
                    except Exception:
                        pub_date = datetime.utcnow()

                    if since and pub_date < since:
                        continue

                    user = item.get("user") or {}
                    author = user.get("username") or user.get("name")

                    signal = NormalizedSignal(
                        source="devto",
                        source_id=dev_id,
                        source_url=item.get("url") or f"https://dev.to/article/{dev_id}",
                        title=title[:280],
                        author=author,
                        body=body[:4000],
                        published_at=pub_date,
                        metadata={
                            "tag_list": item.get("tag_list", []),
                            "positive_reactions_count": item.get("positive_reactions_count", 0),
                            "comments_count": item.get("comments_count", 0),
                            "reading_time": item.get("reading_time_minutes"),
                            "query_tag": tag,
                            "ingest_tier": "forem_api",
                        },
                    )
                    results.append(signal)

            except Exception as e:
                logger.warning(f"DEV.to collect failed for tag '{tag}': {e}")
                continue

        # Fallback: if not enough results, fetch generic latest
        if len(results) < min(5, limit):
            try:
                resp = requests.get(self.BASE_URL, params={"per_page": min(20, limit - len(results))}, timeout=10)
                if resp.status_code == 200:
                    items = resp.json()
                    for item in items:
                        if len(results) >= limit:
                            break
                        dev_id = str(item.get("id"))
                        if dev_id in seen_ids:
                            continue
                        seen_ids.add(dev_id)
                        title = item.get("title") or ""
                        description = item.get("description") or ""
                        body = clean_scraped_text(f"{title}\n\n{description}") or title
                        pub_str = item.get("published_timestamp")
                        try:
                            pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00")).replace(tzinfo=None) if pub_str else datetime.utcnow()
                        except Exception:
                            pub_date = datetime.utcnow()
                        if since and pub_date < since:
                            continue
                        user = item.get("user") or {}
                        author = user.get("username")
                        signal = NormalizedSignal(
                            source="devto",
                            source_id=dev_id,
                            source_url=item.get("url") or "",
                            title=title[:280],
                            author=author,
                            body=body[:4000],
                            published_at=pub_date,
                            metadata={"ingest_tier": "forem_api_fallback"},
                        )
                        results.append(signal)
            except Exception as e:
                logger.debug(f"DEV.to fallback failed: {e}")

        return results
