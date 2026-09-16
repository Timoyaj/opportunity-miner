"""Reddit source adapter supporting public JSON endpoints, RSS feeds, and optional PRAW."""

from datetime import datetime
import logging
import xml.etree.ElementTree as ET
import requests

from .base import SourceAdapter, NormalizedSignal
from ..core.scraper import clean_scraped_text

logger = logging.getLogger(__name__)


class RedditAdapter(SourceAdapter):
    """Adapter for monitoring subreddits with multi-tier fallback."""

    DEFAULT_USER_AGENT = "OpportunityMiner-Research/0.1.0 (Community problem discovery engine)"

    def __init__(self, user_agent: str | None = None):
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

    @property
    def source_name(self) -> str:
        return "reddit"

    def health_check(self) -> tuple[bool, str]:
        headers = {"User-Agent": self.user_agent}
        try:
            resp = requests.get(
                "https://www.reddit.com/r/excel/new.json?limit=1",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                return True, "Reddit public JSON interface accessible (OK)"
            elif resp.status_code in (403, 429):
                # Try RSS fallback
                rss_resp = requests.get("https://www.reddit.com/r/excel/new/.rss", headers=headers, timeout=5)
                if rss_resp.status_code == 200:
                    return True, "Reddit public RSS interface accessible (JSON rate-limited)"
                return False, f"Reddit returned HTTP {resp.status_code} on JSON and {rss_resp.status_code} on RSS"
            return False, f"Reddit returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Reddit connection failed: {str(e)}"


    def collect(self, queries: list[str], limit: int = 50, since: datetime | None = None) -> list[NormalizedSignal]:
        """Collects signals across subreddits listed in queries (subreddits passed as queries list)."""
        results: list[NormalizedSignal] = []
        seen_ids = set()

        headers = {"User-Agent": self.user_agent}

        for subreddit in queries:
            if len(results) >= limit:
                break

            sub_name = subreddit.replace("r/", "").strip()
            sub_limit = min(25, limit - len(results))

            # Tier 1: Public JSON endpoint
            collected_from_json = False
            try:
                json_url = f"https://www.reddit.com/r/{sub_name}/new.json?limit={sub_limit}"
                resp = requests.get(json_url, headers=headers, timeout=8)

                if resp.status_code == 200:
                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    for item in children:
                        post = item.get("data", {})
                        post_id = post.get("id")
                        if not post_id or post_id in seen_ids:
                            continue
                        seen_ids.add(post_id)

                        created_utc = post.get("created_utc")
                        pub_date = datetime.utcfromtimestamp(created_utc) if created_utc else datetime.utcnow()
                        if since and pub_date < since:
                            continue

                        title = post.get("title") or ""
                        selftext = post.get("selftext") or ""
                        permalink = post.get("permalink") or ""
                        source_url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else permalink

                        body = f"{title}\n\n{selftext}".strip()

                        signal = NormalizedSignal(
                            source="reddit",
                            source_id=f"t3_{post_id}",
                            source_url=source_url,
                            title=title,
                            author=post.get("author"),
                            body=body,
                            published_at=pub_date,
                            metadata={
                                "subreddit": sub_name,
                                "score": post.get("score", 0),
                                "num_comments": post.get("num_comments", 0),
                                "upvote_ratio": post.get("upvote_ratio", 1.0),
                            }
                        )
                        results.append(signal)
                    collected_from_json = True
            except Exception as e:
                logger.debug(f"Reddit JSON error for r/{sub_name}: {e}")

            # Tier 2: RSS fallback if JSON was blocked / rate limited
            if not collected_from_json:
                try:
                    rss_url = f"https://www.reddit.com/r/{sub_name}/new/.rss"
                    resp = requests.get(rss_url, headers=headers, timeout=8)
                    if resp.status_code == 200:
                        root = ET.fromstring(resp.content)
                        # Atom namespace handling
                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        entries = root.findall("atom:entry", ns)
                        for entry in entries:
                            entry_id = entry.findtext("atom:id", default="", namespaces=ns)
                            post_id = entry_id.split("/")[-1] if entry_id else ""
                            if not post_id or post_id in seen_ids:
                                continue
                            seen_ids.add(post_id)

                            pub_str = entry.findtext("atom:published", default="", namespaces=ns) or entry.findtext("atom:updated", default="", namespaces=ns)
                            try:
                                pub_date = datetime.fromisoformat(pub_str).replace(tzinfo=None) if pub_str else datetime.utcnow()
                            except Exception:
                                pub_date = datetime.utcnow()

                            if since and pub_date < since:
                                continue

                            title = clean_scraped_text(entry.findtext("atom:title", default="", namespaces=ns))
                            raw_content = entry.findtext("atom:content", default="", namespaces=ns)
                            clean_content = clean_scraped_text(raw_content)
                            link_elem = entry.find("atom:link", ns)
                            link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                            author = entry.findtext("atom:author/atom:name", default="", namespaces=ns)

                            body = f"{title}\n\n{clean_content}".strip() if clean_content else title

                            signal = NormalizedSignal(
                                source="reddit",
                                source_id=post_id,
                                source_url=link,
                                title=title,
                                author=author,
                                body=body,
                                published_at=pub_date,
                                metadata={"subreddit": sub_name, "ingest_tier": "rss"}
                            )
                            results.append(signal)
                except Exception as rss_err:
                    logger.warning(f"Reddit RSS fallback failed for r/{sub_name}: {rss_err}")

        return results
