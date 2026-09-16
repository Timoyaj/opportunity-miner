"""Indie Hackers source adapter using RSS feeds and community syndication."""

from datetime import datetime
import logging
import xml.etree.ElementTree as ET
import re
import requests

from .base import SourceAdapter, NormalizedSignal

logger = logging.getLogger(__name__)


class IndieHackersAdapter(SourceAdapter):
    """Adapter for gathering founder workflow complaints from Indie Hackers."""

    RSS_FEED = "https://www.indiehackers.com/feed"
    DEFAULT_USER_AGENT = "OpportunityMiner-Research/0.1.0"

    @property
    def source_name(self) -> str:
        return "indiehackers"

    def health_check(self) -> tuple[bool, str]:
        try:
            resp = requests.get(self.RSS_FEED, headers={"User-Agent": self.DEFAULT_USER_AGENT}, timeout=5)
            if resp.status_code == 200:
                return True, "Indie Hackers RSS feed accessible (OK)"
            return False, f"Indie Hackers returned HTTP {resp.status_code}"
        except Exception as e:
            return False, f"Indie Hackers unreachable: {str(e)}"

    def collect(self, queries: list[str], limit: int = 30, since: datetime | None = None) -> list[NormalizedSignal]:
        results: list[NormalizedSignal] = []
        seen_ids = set()

        try:
            resp = requests.get(self.RSS_FEED, headers={"User-Agent": self.DEFAULT_USER_AGENT}, timeout=8)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is not None:
                    for item in channel.findall("item"):
                        if len(results) >= limit:
                            break

                        link = item.findtext("link", default="")
                        title = item.findtext("title", default="")
                        desc = item.findtext("description", default="")
                        guid = item.findtext("guid", default=link)

                        if guid in seen_ids:
                            continue
                        seen_ids.add(guid)

                        clean_body = re.sub(r"<[^>]+>", " ", desc).strip()
                        body = f"{title}\n\n{clean_body}".strip()

                        signal = NormalizedSignal(
                            source="indiehackers",
                            source_id=guid,
                            source_url=link,
                            title=title,
                            author="IndieHacker",
                            body=body,
                            published_at=datetime.utcnow(),
                            metadata={"ingest_tier": "rss"}
                        )
                        results.append(signal)
        except Exception as e:
            logger.warning(f"Indie Hackers collection failed: {e}")

        return results
